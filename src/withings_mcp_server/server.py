"""Withings MCP Server main implementation."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from .auth import WithingsAuth


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
                    description="Get user information from Withings account",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_measurements",
                    description="Get body measurements (weight, fat mass, muscle mass, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "meastype": {
                                "type": "string",
                                "description": "Measurement type: weight=1, height=4, fat_free_mass=5, fat_ratio=6, fat_mass_weight=8, diastolic_bp=9, systolic_bp=10, heart_rate=11, temperature=12, spo2=54, body_temp=71, muscle_mass=76, bone_mass=88, pulse_wave_velocity=91",
                                "enum": ["1", "4", "5", "6", "8", "9", "10", "11", "12", "54", "71", "76", "88", "91"],
                            },
                            "category": {
                                "type": "string",
                                "description": "Measurement category: 1=real, 2=user_objective",
                                "enum": ["1", "2"],
                                "default": "1",
                            },
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD) or Unix timestamp",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD) or Unix timestamp",
                            },
                            "lastupdate": {
                                "type": "string",
                                "description": "Get measurements modified since this timestamp",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_activity",
                    description="Get daily activity data (steps, calories, distance, elevation)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format",
                            },
                            "lastupdate": {
                                "type": "string",
                                "description": "Get activities modified since this timestamp",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_sleep_summary",
                    description="Get sleep summary data (duration, deep sleep, REM, wake up count, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format",
                            },
                            "lastupdate": {
                                "type": "string",
                                "description": "Get sleep data modified since this timestamp",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_sleep_details",
                    description="Get detailed sleep data with all sleep phases",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD) or Unix timestamp",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD) or Unix timestamp",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_workouts",
                    description="Get workout/training sessions data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdateymd": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format",
                            },
                            "enddateymd": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_heart_rate",
                    description="Get heart rate measurements over a time period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "startdate": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD) or Unix timestamp",
                            },
                            "enddate": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD) or Unix timestamp",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_authorization_url",
                    description="Get OAuth2 authorization URL to authenticate with Withings",
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
                    result = await self._get_measurements(arguments)
                elif name == "get_activity":
                    result = await self._get_activity(arguments)
                elif name == "get_sleep_summary":
                    result = await self._get_sleep_summary(arguments)
                elif name == "get_sleep_details":
                    result = await self._get_sleep_details(arguments)
                elif name == "get_workouts":
                    result = await self._get_workouts(arguments)
                elif name == "get_heart_rate":
                    result = await self._get_heart_rate(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make authenticated request to Withings API."""
        headers = self.auth.get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

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
        """Get body measurements."""
        params = {"action": "getmeas"}

        if "meastype" in args:
            params["meastype"] = args["meastype"]
        if "category" in args:
            params["category"] = args["category"]
        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])
        if "lastupdate" in args:
            params["lastupdate"] = self._parse_date(args["lastupdate"])

        return await self._make_request("/measure", params)

    async def _get_activity(self, args: dict) -> dict:
        """Get activity data."""
        params = {"action": "getactivity"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]
        if "lastupdate" in args:
            params["lastupdate"] = self._parse_date(args["lastupdate"])

        return await self._make_request("/v2/measure", params)

    async def _get_sleep_summary(self, args: dict) -> dict:
        """Get sleep summary."""
        params = {"action": "getsummary"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]
        if "lastupdate" in args:
            params["lastupdate"] = self._parse_date(args["lastupdate"])

        return await self._make_request("/v2/sleep", params)

    async def _get_sleep_details(self, args: dict) -> dict:
        """Get detailed sleep data."""
        params = {"action": "get"}

        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])

        return await self._make_request("/v2/sleep", params)

    async def _get_workouts(self, args: dict) -> dict:
        """Get workout data."""
        params = {"action": "getworkouts"}

        if "startdateymd" in args:
            params["startdateymd"] = args["startdateymd"]
        if "enddateymd" in args:
            params["enddateymd"] = args["enddateymd"]

        return await self._make_request("/v2/measure", params)

    async def _get_heart_rate(self, args: dict) -> dict:
        """Get heart rate data."""
        params = {"action": "getintradayactivity"}

        if "startdate" in args:
            params["startdate"] = self._parse_date(args["startdate"])
        if "enddate" in args:
            params["enddate"] = self._parse_date(args["enddate"])

        return await self._make_request("/v2/measure", params)

    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main():
    """Main entry point."""
    server = WithingsServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
