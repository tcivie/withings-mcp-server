"""Withings MCP Server main implementation."""

import asyncio
import csv
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from dotenv import load_dotenv

from .auth import WithingsAuth

import time

MEAS_TYPES = {
    1: ("Weight", "kg"),
    4: ("Height", "m"),
    5: ("Fat-free mass", "kg"),
    6: ("Body fat", "%"),
    8: ("Fat mass", "kg"),
    9: ("Diastolic BP", "mmHg"),
    10: ("Systolic BP", "mmHg"),
    11: ("Heart rate", "bpm"),
    12: ("Temperature", "\u00b0C"),
    54: ("SpO2", "%"),
    71: ("Body temperature", "\u00b0C"),
    76: ("Muscle mass", "kg"),
    88: ("Bone mass", "kg"),
    91: ("Pulse wave velocity", "m/s"),
}

WORKOUT_TYPES = {
    1: "Walk",
    2: "Run",
    3: "Hiking",
    4: "Skating",
    5: "BMX",
    6: "Bicycling",
    7: "Swimming",
    8: "Surfing",
    9: "Kitesurfing",
    10: "Windsurfing",
    11: "Bodyboard",
    12: "Tennis",
    13: "Table tennis",
    14: "Squash",
    15: "Badminton",
    16: "Lift weights",
    17: "Calisthenics",
    18: "Elliptical",
    19: "Pilates",
    20: "Basketball",
    21: "Soccer",
    22: "Football",
    23: "Rugby",
    24: "Volleyball",
    25: "Waterpolo",
    26: "Horse riding",
    27: "Golf",
    28: "Yoga",
    29: "Dancing",
    30: "Boxing",
    31: "Fencing",
    32: "Wrestling",
    33: "Martial arts",
    34: "Skiing",
    35: "Snowboarding",
    36: "Other",
    188: "Rowing",
    191: "Ice hockey",
    192: "Handball",
    193: "Climbing",
    194: "Ice skating",
    272: "Multi-sport",
}

SLEEP_STATES = {
    0: "awake",
    1: "light",
    2: "deep",
    3: "rem",
}


def _convert_measure_value(value, unit):
    return float(value * (10 ** unit))


def _default_date_range(days_back):
    end = int(time.time())
    start = end - (days_back * 86400)
    return (start, end)


def _default_ymd_range(days_back):
    today = datetime.now()
    end = today.strftime("%Y-%m-%d")
    start = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    return (start, end)


ACTIVITY_COLUMNS = [
    "date", "steps", "calories", "total_calories", "distance_km",
    "elevation_m", "light_activity_min", "moderate_activity_min",
    "intense_activity_min", "hr_average", "hr_min", "hr_max",
]

SLEEP_COLUMNS = [
    "date", "total_sleep_hours", "deep_hours", "light_hours",
    "rem_hours", "awake_hours", "sleep_score", "hr_average",
]

WORKOUT_COLUMNS = [
    "date", "type", "duration_min", "calories", "distance_km",
    "elevation_m", "steps", "hr_average", "hr_min", "hr_max", "spo2_average",
]


def format_measurements(raw_body):
    measuregrps = raw_body.get("measuregrps", [])
    if not measuregrps:
        return []
    total = len(measuregrps)
    groups = measuregrps[:50]
    result = []
    for grp in groups:
        record = {"date": datetime.fromtimestamp(grp["date"]).strftime("%Y-%m-%d")}
        for m in grp.get("measures", []):
            mtype = m["type"]
            if mtype not in MEAS_TYPES:
                continue
            name, unit = MEAS_TYPES[mtype]
            converted = round(_convert_measure_value(m["value"], m["unit"]), 1)
            if unit == "%":
                record[name] = f"{converted}%"
            else:
                record[name] = f"{converted} {unit}"
        result.append(record)
    if total > 50:
        result.append(f"(showing 50 of {total} total, use narrower date range)")
    return result


def format_activity(raw_body):
    activities = raw_body.get("activities", [])
    if not activities:
        return []
    total = len(activities)
    items = activities[:30]
    field_map = {
        "steps": "steps",
        "calories": "calories",
        "totalcalories": "total_calories",
        "distance": "distance_km",
        "elevation": "elevation_m",
        "soft": "light_activity_min",
        "moderate": "moderate_activity_min",
        "intense": "intense_activity_min",
        "hr_average": "hr_average",
        "hr_min": "hr_min",
        "hr_max": "hr_max",
    }
    result = []
    for act in items:
        record = {"date": act["date"]}
        for raw_key, out_key in field_map.items():
            val = act.get(raw_key)
            if val is None or val == 0:
                continue
            if raw_key == "distance":
                record[out_key] = round(val / 1000, 1)
            else:
                record[out_key] = val
        result.append(record)
    if total > 30:
        truncated = total - 30
        result.append({"note": f"{truncated} entries truncated (showing 30 of {total})"})
    return result


def format_sleep_summary(raw_body):
    series = raw_body.get("series", [])
    if not series:
        return []
    total = len(series)
    items = series[:30]
    duration_fields = {
        "deepsleepduration": "deep_hours",
        "lightsleepduration": "light_hours",
        "remsleepduration": "rem_hours",
        "wakeupduration": "awake_hours",
        "total_sleep_time": "total_sleep_hours",
    }
    latency_fields = {
        "durationtosleep": "time_to_sleep_min",
        "durationtowakeup": "time_to_wakeup_min",
    }
    rename_fields = {
        "wakeupcount": "wakeup_count",
        "breathing_disturbances_intensity": "breathing_disturbances",
        "snoringepisodecount": "snoring_episodes",
    }
    passthrough_fields = [
        "sleep_score", "sleep_efficiency", "hr_average", "hr_min",
        "hr_max", "rr_average", "apnea_hypopnea_index",
    ]
    result = []
    for entry in items:
        record = {"date": entry["date"]}
        data = entry.get("data", {})
        for raw_key, out_key in duration_fields.items():
            if raw_key in data:
                record[out_key] = round(data[raw_key] / 3600, 1)
        for raw_key, out_key in latency_fields.items():
            if raw_key in data:
                record[out_key] = int(data[raw_key] / 60)
        for raw_key, out_key in rename_fields.items():
            if raw_key in data:
                record[out_key] = data[raw_key]
        for field in passthrough_fields:
            if field in data:
                record[field] = data[field]
        result.append(record)
    if total > 30:
        truncated = total - 30
        result.append({"note": f"{truncated} entries truncated (showing 30 of {total})"})
    return result


def format_sleep_details(raw_body):
    series = raw_body.get("series", [])
    if not series:
        return {"phases": [], "hr_samples": [], "summary": {}}
    phases = []
    all_hr = {}
    for entry in series:
        start = entry["startdate"]
        end = entry["enddate"]
        state = entry.get("state", -1)
        phases.append({
            "time": datetime.fromtimestamp(start).strftime("%H:%M"),
            "state": SLEEP_STATES.get(state, "unknown"),
            "duration_min": int((end - start) / 60),
        })
        hr = entry.get("hr", {})
        for ts_str, bpm in hr.items():
            all_hr[int(ts_str)] = int(bpm)
    sorted_ts = sorted(all_hr.keys())
    hr_samples = [{"time": datetime.fromtimestamp(ts).strftime("%H:%M"), "bpm": all_hr[ts]} for ts in sorted_ts]
    if len(hr_samples) > 100:
        n = len(hr_samples)
        step = n / 100
        hr_samples = [hr_samples[int(i * step)] for i in range(100)]
    summary = {"total_phases": len(phases)}
    if all_hr:
        bpm_values = list(all_hr.values())
        summary["avg_hr"] = int(round(sum(bpm_values) / len(bpm_values)))
        summary["min_hr"] = min(bpm_values)
        summary["max_hr"] = max(bpm_values)
    return {"phases": phases, "hr_samples": hr_samples, "summary": summary}


def format_workouts(raw_body):
    series = raw_body.get("series", [])
    if not series:
        return []
    total = len(series)
    items = series[:30]
    data_field_map = {
        "calories": "calories",
        "distance": "distance_km",
        "elevation": "elevation_m",
        "steps": "steps",
        "hr_average": "hr_average",
        "hr_min": "hr_min",
        "hr_max": "hr_max",
        "spo2_average": "spo2_average",
    }
    result = []
    for entry in items:
        category = entry.get("category", -1)
        record = {
            "date": entry["date"],
            "type": WORKOUT_TYPES.get(category, f"Unknown (code {category})"),
            "duration_min": round((entry["enddate"] - entry["startdate"]) / 60),
        }
        data = entry.get("data", {})
        for raw_key, out_key in data_field_map.items():
            val = data.get(raw_key)
            if val is None or val == 0:
                continue
            if raw_key == "distance":
                record[out_key] = round(val / 1000, 1)
            else:
                record[out_key] = val
        result.append(record)
    if total > 30:
        truncated = total - 30
        result.append({"note": f"{truncated} entries truncated (showing 30 of {total})"})
    return result


def format_heart_rate(raw_body):
    series = raw_body.get("series", {})
    if not series or not isinstance(series, dict):
        return {"min_hr": 0, "max_hr": 0, "avg_hr": 0, "total_samples": 0, "hourly": []}
    all_hr = []
    date_hour_buckets = {}
    hourly_buckets = {}
    daily_buckets = {}
    for ts_str, entry in series.items():
        if "heart_rate" not in entry:
            continue
        hr = entry["heart_rate"]
        all_hr.append(hr)
        ts = int(ts_str)
        dt = datetime.fromtimestamp(ts)
        hour_key = dt.strftime("%H:00")
        date_key = dt.strftime("%Y-%m-%d")
        dh_key = (date_key, hour_key)
        if dh_key not in date_hour_buckets:
            date_hour_buckets[dh_key] = True
        if hour_key not in hourly_buckets:
            hourly_buckets[hour_key] = []
        hourly_buckets[hour_key].append(hr)
        if date_key not in daily_buckets:
            daily_buckets[date_key] = []
        daily_buckets[date_key].append(hr)
    if not all_hr:
        return {"min_hr": 0, "max_hr": 0, "avg_hr": 0, "total_samples": 0, "hourly": []}
    overall = {
        "min_hr": min(all_hr),
        "max_hr": max(all_hr),
        "avg_hr": int(round(sum(all_hr) / len(all_hr))),
        "total_samples": len(all_hr),
    }
    if len(date_hour_buckets) > 24:
        daily = []
        for date_key in sorted(daily_buckets.keys()):
            vals = daily_buckets[date_key]
            daily.append({
                "date": date_key,
                "avg": int(round(sum(vals) / len(vals))),
                "min": min(vals),
                "max": max(vals),
            })
        overall["daily"] = daily
    else:
        hourly = []
        for hour_key in sorted(hourly_buckets.keys()):
            vals = hourly_buckets[hour_key]
            hourly.append({
                "hour": hour_key,
                "avg": int(round(sum(vals) / len(vals))),
                "min": min(vals),
                "max": max(vals),
                "samples": len(vals),
            })
        overall["hourly"] = hourly
    return overall


# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class WithingsServer:
    """MCP Server for Withings API."""

    def __init__(self):
        self.server = Server("withings-mcp-server")
        self.auth = WithingsAuth()
        self.base_url = "https://wbsapi.withings.net"
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available Withings API tools."""
            return [
                Tool(
                    name="get_user_info",
                    description="Get user device information from Withings account.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_measurements",
                    description="Get body measurements (weight, body fat %, muscle mass, bone mass, BP, heart rate, SpO2, temperature). Returns last 30 days by default. Data is summarized per measurement with human-readable units.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to 30 days ago.",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_activity",
                    description="Get daily activity summary (steps, calories, distance in km, active minutes, elevation, heart rate). Returns last 7 days by default.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to 7 days ago.",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_sleep_summary",
                    description="Get nightly sleep summary (total/deep/light/REM/awake hours, sleep score, heart rate, breathing disturbances). Returns last 7 days by default.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to 7 days ago.",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_sleep_details",
                    description="Get detailed sleep phases (light/deep/REM/awake transitions) and heart rate samples for a single night. Returns last night by default.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to yesterday.",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_workouts",
                    description="Get workout sessions (type, duration, calories, distance, heart rate, SpO2). Returns last 30 days by default.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to 30 days ago.",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_heart_rate",
                    description="Get heart rate data with hourly aggregation (avg/min/max per hour). Returns today by default. Multi-day queries return daily summaries instead.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD). Defaults to today.",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD). Defaults to today.",
                            },
                        },
                    },
                ),
                Tool(
                    name="export_csv",
                    description="Export health data to a CSV file in /tmp. Returns the file path. Use after fetching data with the other tools.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_type": {
                                "type": "string",
                                "description": "Type of data to export.",
                                "enum": ["measurements", "activity", "sleep", "workouts", "heart_rate"],
                            },
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD).",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD).",
                            },
                        },
                        "required": ["data_type"],
                    },
                ),
                Tool(
                    name="get_authorization_url",
                    description="Get OAuth2 authorization URL to authenticate with Withings. Use this if other tools return authentication errors.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {
                                "type": "string",
                                "description": "OAuth scopes (comma-separated): user.info, user.metrics, user.activity",
                                "default": "user.info,user.metrics,user.activity",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_authorization_url":
                    scope = arguments.get("scope", "user.info,user.metrics,user.activity")
                    url = self.auth.get_authorization_url(scope)
                    return [
                        TextContent(
                            type="text",
                            text=f"Please visit this URL to authorize:\n\n{url}\n\nAfter authorization, you'll receive a code. Use it to get access tokens.",
                        )
                    ]

                # For all other tools, ensure we have a valid token
                await self.auth.ensure_valid_token()

                if name == "get_user_info":
                    result = await self._get_user_info()
                elif name == "get_measurements":
                    raw = await self._get_measurements(arguments)
                    result = format_measurements(raw)
                elif name == "get_activity":
                    raw = await self._get_activity(arguments)
                    result = format_activity(raw)
                elif name == "get_sleep_summary":
                    raw = await self._get_sleep_summary(arguments)
                    result = format_sleep_summary(raw)
                elif name == "get_sleep_details":
                    raw = await self._get_sleep_details(arguments)
                    result = format_sleep_details(raw)
                elif name == "get_workouts":
                    raw = await self._get_workouts(arguments)
                    result = format_workouts(raw)
                elif name == "get_heart_rate":
                    raw = await self._get_heart_rate(arguments)
                    result = format_heart_rate(raw)
                elif name == "export_csv":
                    result = await self._export_csv(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _make_request(self, endpoint: str, params: dict, retry_on_401: bool = True) -> dict:
        """Make authenticated request to Withings API."""
        headers = self.auth.get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params,
            )

            # Don't raise for status yet - check for 401 first
            data = response.json()

            # Handle 401 - token expired, try refresh and retry once
            if data.get("status") == 401 and retry_on_401:
                await self.auth.refresh_access_token()
                # Retry the request with new token
                return await self._make_request(endpoint, params, retry_on_401=False)

            # Check for other API errors
            if data.get("status") != 0:
                raise Exception(f"API error: {data}")

            return data.get("body", {})

    def _parse_date(self, date_str: Optional[str]) -> Optional[int]:
        """Parse date string to Unix timestamp."""
        if not date_str:
            return None

        # If already a timestamp
        if date_str.isdigit():
            return int(date_str)

        # Parse YYYY-MM-DD format
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return int(dt.timestamp())
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or Unix timestamp")

    async def _get_user_info(self) -> dict:
        """Get user information."""
        return await self._make_request("/v2/user", {"action": "getdevice"})

    async def _get_measurements(self, args: dict) -> dict:
        """Get body measurements. Defaults to last 30 days."""
        params = {"action": "getmeas"}

        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])

        # Default to last 30 days
        if "startdate" not in params and "enddate" not in params:
            start, end = _default_date_range(30)
            params["startdate"] = start
            params["enddate"] = end

        return await self._make_request("/measure", params)

    async def _get_activity(self, args: dict) -> dict:
        """Get activity data. Defaults to last 7 days."""
        params = {"action": "getactivity"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]

        # Default to last 7 days
        if "startdateymd" not in params and "enddateymd" not in params:
            start, end = _default_ymd_range(7)
            params["startdateymd"] = start
            params["enddateymd"] = end

        return await self._make_request("/v2/measure", params)

    async def _get_sleep_summary(self, args: dict) -> dict:
        """Get sleep summary. Defaults to last 7 days."""
        params = {"action": "getsummary"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]

        # Default to last 7 days
        if "startdateymd" not in params and "enddateymd" not in params:
            start, end = _default_ymd_range(7)
            params["startdateymd"] = start
            params["enddateymd"] = end

        return await self._make_request("/v2/sleep", params)

    async def _get_sleep_details(self, args: dict) -> dict:
        """Get detailed sleep data. Defaults to last night."""
        params = {"action": "get"}

        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])

        # Default to last night (yesterday to today)
        if "startdate" not in params and "enddate" not in params:
            start, end = _default_date_range(1)
            params["startdate"] = start
            params["enddate"] = end

        return await self._make_request("/v2/sleep", params)

    async def _get_workouts(self, args: dict) -> dict:
        """Get workout data. Defaults to last 30 days."""
        params = {"action": "getworkouts"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]

        # Default to last 30 days
        if "startdateymd" not in params and "enddateymd" not in params:
            start, end = _default_ymd_range(30)
            params["startdateymd"] = start
            params["enddateymd"] = end

        return await self._make_request("/v2/measure", params)

    async def _get_heart_rate(self, args: dict) -> dict:
        """Get heart rate data. Defaults to today."""
        params = {"action": "getintradayactivity"}

        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])

        # Default to today
        if "startdate" not in params and "enddate" not in params:
            start, end = _default_date_range(0)
            params["startdate"] = start
            params["enddate"] = end

        return await self._make_request("/v2/measure", params)

    async def _export_csv(self, args: dict) -> dict:
        """Fetch data and export to CSV."""
        data_type = args["data_type"]

        # Fetch the data using appropriate method
        fetch_args = {}
        if "startdate" in args:
            fetch_args["startdate"] = args["startdate"]
        if "enddate" in args:
            fetch_args["enddate"] = args["enddate"]

        # Map data_type to fetch+format
        if data_type == "measurements":
            if "startdate" not in fetch_args:
                s, e = _default_ymd_range(30)
                fetch_args["startdate"] = s
                fetch_args["enddate"] = e
            raw = await self._get_measurements(fetch_args)
            records = format_measurements(raw)
        elif data_type == "activity":
            if "startdate" in fetch_args:
                fetch_args["startdateymd"] = fetch_args.pop("startdate")
            if "enddate" in fetch_args:
                fetch_args["enddateymd"] = fetch_args.pop("enddate")
            raw = await self._get_activity(fetch_args)
            records = format_activity(raw)
        elif data_type == "sleep":
            if "startdate" in fetch_args:
                fetch_args["startdateymd"] = fetch_args.pop("startdate")
            if "enddate" in fetch_args:
                fetch_args["enddateymd"] = fetch_args.pop("enddate")
            raw = await self._get_sleep_summary(fetch_args)
            records = format_sleep_summary(raw)
        elif data_type == "workouts":
            if "startdate" in fetch_args:
                fetch_args["startdateymd"] = fetch_args.pop("startdate")
            if "enddate" in fetch_args:
                fetch_args["enddateymd"] = fetch_args.pop("enddate")
            raw = await self._get_workouts(fetch_args)
            records = format_workouts(raw)
        elif data_type == "heart_rate":
            raw = await self._get_heart_rate(fetch_args)
            records = format_heart_rate(raw)
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

        return export_to_csv(data_type, records)

    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def export_to_csv(data_type, records):
    file_path = f"/tmp/withings_export_{data_type}_{int(time.time())}.csv"

    if data_type == "heart_rate" and isinstance(records, dict):
        if "hourly" in records:
            header = ["hour", "avg", "min", "max", "samples"]
            rows = records["hourly"]
        else:
            header = ["date", "avg", "min", "max"]
            rows = records["daily"]
    else:
        dict_records = [r for r in records if isinstance(r, dict)]
        if data_type == "activity":
            header = ACTIVITY_COLUMNS
        elif data_type == "sleep":
            header = SLEEP_COLUMNS
        elif data_type == "workouts":
            header = WORKOUT_COLUMNS
        else:
            if dict_records:
                first = dict_records[0]
                other_keys = sorted(k for k in first if k != "date")
                header = ["date"] + other_keys
            else:
                header = ["date"]
        rows = dict_records

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(col, "") for col in header])

    return {"file_path": file_path, "rows": len(rows), "data_type": data_type}


def main():
    """Main entry point."""
    server = WithingsServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
