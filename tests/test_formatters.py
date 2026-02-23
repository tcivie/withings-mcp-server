"""Tests for Withings MCP server helper functions and lookup dictionaries.

These tests define the expected behavior of module-level constants and pure
helper functions that convert raw Withings API data into human-readable formats.
"""

import csv
import glob
import os
import time
from datetime import datetime, timedelta

import pytest

from withings_mcp_server.server import format_sleep_details, format_heart_rate, format_workouts, export_to_csv


class TestMeasTypes:
    """Tests for the MEAS_TYPES lookup dictionary."""

    def test_meas_types_is_a_dict(self):
        # Given / When
        from withings_mcp_server.server import MEAS_TYPES

        # Then
        assert isinstance(MEAS_TYPES, dict)

    def test_meas_types_contains_all_14_entries(self):
        from withings_mcp_server.server import MEAS_TYPES

        expected_keys = {1, 4, 5, 6, 8, 9, 10, 11, 12, 54, 71, 76, 88, 91}
        assert set(MEAS_TYPES.keys()) == expected_keys

    def test_meas_types_weight_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[1] == ("Weight", "kg")

    def test_meas_types_height_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[4] == ("Height", "m")

    def test_meas_types_fat_free_mass_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[5] == ("Fat-free mass", "kg")

    def test_meas_types_body_fat_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[6] == ("Body fat", "%")

    def test_meas_types_fat_mass_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[8] == ("Fat mass", "kg")

    def test_meas_types_diastolic_bp_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[9] == ("Diastolic BP", "mmHg")

    def test_meas_types_systolic_bp_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[10] == ("Systolic BP", "mmHg")

    def test_meas_types_heart_rate_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[11] == ("Heart rate", "bpm")

    def test_meas_types_temperature_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[12] == ("Temperature", "\u00b0C")

    def test_meas_types_spo2_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[54] == ("SpO2", "%")

    def test_meas_types_body_temperature_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[71] == ("Body temperature", "\u00b0C")

    def test_meas_types_muscle_mass_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[76] == ("Muscle mass", "kg")

    def test_meas_types_bone_mass_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[88] == ("Bone mass", "kg")

    def test_meas_types_pulse_wave_velocity_entry(self):
        from withings_mcp_server.server import MEAS_TYPES

        assert MEAS_TYPES[91] == ("Pulse wave velocity", "m/s")

    def test_meas_types_values_are_name_unit_tuples(self):
        from withings_mcp_server.server import MEAS_TYPES

        for key, value in MEAS_TYPES.items():
            assert isinstance(value, tuple), f"MEAS_TYPES[{key}] should be a tuple"
            assert len(value) == 2, f"MEAS_TYPES[{key}] should have exactly 2 elements (name, unit)"
            name, unit = value
            assert isinstance(name, str), f"MEAS_TYPES[{key}] name should be a string"
            assert isinstance(unit, str), f"MEAS_TYPES[{key}] unit should be a string"


class TestWorkoutTypes:
    """Tests for the WORKOUT_TYPES lookup dictionary."""

    def test_workout_types_is_a_dict(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert isinstance(WORKOUT_TYPES, dict)

    def test_workout_types_contains_expected_count(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        # 36 standard entries (1-36) + 5 higher codes (188, 191, 192, 193, 194, 272)
        assert len(WORKOUT_TYPES) == 42

    def test_workout_types_walk(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[1] == "Walk"

    def test_workout_types_run(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[2] == "Run"

    def test_workout_types_hiking(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[3] == "Hiking"

    def test_workout_types_swimming(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[7] == "Swimming"

    def test_workout_types_yoga(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[28] == "Yoga"

    def test_workout_types_other(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[36] == "Other"

    def test_workout_types_rowing_high_code(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[188] == "Rowing"

    def test_workout_types_ice_hockey_high_code(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[191] == "Ice hockey"

    def test_workout_types_climbing_high_code(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[193] == "Climbing"

    def test_workout_types_multi_sport_high_code(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        assert WORKOUT_TYPES[272] == "Multi-sport"

    def test_workout_types_all_values_are_strings(self):
        from withings_mcp_server.server import WORKOUT_TYPES

        for key, value in WORKOUT_TYPES.items():
            assert isinstance(key, int), f"Key {key} should be an int"
            assert isinstance(value, str), f"WORKOUT_TYPES[{key}] should be a string"

    def test_workout_types_selected_sports_mapping(self):
        """Verify a broad selection of sport mappings in bulk."""
        from withings_mcp_server.server import WORKOUT_TYPES

        expected_subset = {
            4: "Skating",
            5: "BMX",
            6: "Bicycling",
            8: "Surfing",
            12: "Tennis",
            16: "Lift weights",
            17: "Calisthenics",
            18: "Elliptical",
            20: "Basketball",
            21: "Soccer",
            30: "Boxing",
            34: "Skiing",
            35: "Snowboarding",
            192: "Handball",
            194: "Ice skating",
        }
        for code, name in expected_subset.items():
            assert WORKOUT_TYPES[code] == name, f"WORKOUT_TYPES[{code}] should be '{name}'"


class TestSleepStates:
    """Tests for the SLEEP_STATES lookup dictionary."""

    def test_sleep_states_is_a_dict(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert isinstance(SLEEP_STATES, dict)

    def test_sleep_states_has_four_entries(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert len(SLEEP_STATES) == 4

    def test_sleep_states_awake(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert SLEEP_STATES[0] == "awake"

    def test_sleep_states_light(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert SLEEP_STATES[1] == "light"

    def test_sleep_states_deep(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert SLEEP_STATES[2] == "deep"

    def test_sleep_states_rem(self):
        from withings_mcp_server.server import SLEEP_STATES

        assert SLEEP_STATES[3] == "rem"

    def test_sleep_states_keys_are_integers(self):
        from withings_mcp_server.server import SLEEP_STATES

        for key in SLEEP_STATES:
            assert isinstance(key, int), f"Key {key} should be an int"


class TestConvertMeasureValue:
    """Tests for _convert_measure_value(value, unit) -> float."""

    def test_typical_weight_conversion(self):
        # Given: Withings encodes 75.5 kg as value=75500, unit=-3
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(75500, -3)

        # Then
        assert result == pytest.approx(75.5)

    def test_zero_unit_returns_value_as_float(self):
        # Given: unit=0 means value * 10^0 = value * 1
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(120, 0)

        # Then
        assert result == pytest.approx(120.0)

    def test_positive_unit_scales_up(self):
        # Given: value=5, unit=2 means 5 * 10^2 = 500
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(5, 2)

        # Then
        assert result == pytest.approx(500.0)

    def test_negative_unit_scales_down(self):
        # Given: value=1800, unit=-2 means 1800 * 10^-2 = 18.0
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(1800, -2)

        # Then
        assert result == pytest.approx(18.0)

    def test_height_conversion(self):
        # Given: Withings encodes 1.78 m as value=178, unit=-2
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(178, -2)

        # Then
        assert result == pytest.approx(1.78)

    def test_spo2_conversion(self):
        # Given: SpO2 of 98% as value=98, unit=0
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(98, 0)

        # Then
        assert result == pytest.approx(98.0)

    def test_returns_float_type(self):
        from withings_mcp_server.server import _convert_measure_value

        result = _convert_measure_value(100, 0)
        assert isinstance(result, float)

    def test_value_zero_returns_zero(self):
        from withings_mcp_server.server import _convert_measure_value

        result = _convert_measure_value(0, -3)
        assert result == pytest.approx(0.0)

    def test_large_negative_unit(self):
        # Given: value=123456789, unit=-6 means 123.456789
        from withings_mcp_server.server import _convert_measure_value

        # When
        result = _convert_measure_value(123456789, -6)

        # Then
        assert result == pytest.approx(123.456789)


class TestDefaultDateRange:
    """Tests for _default_date_range(days_back) -> tuple[int, int]."""

    def test_returns_tuple_of_two_ints(self):
        from withings_mcp_server.server import _default_date_range

        result = _default_date_range(7)

        assert isinstance(result, tuple)
        assert len(result) == 2
        start, end = result
        assert isinstance(start, int)
        assert isinstance(end, int)

    def test_end_timestamp_is_close_to_now(self):
        from withings_mcp_server.server import _default_date_range

        _, end = _default_date_range(7)
        now = int(time.time())

        # End timestamp should be within 5 seconds of current time
        assert abs(end - now) < 5

    def test_start_timestamp_is_days_back_from_end(self):
        from withings_mcp_server.server import _default_date_range

        days_back = 30
        start, end = _default_date_range(days_back)

        # The difference should be approximately days_back days in seconds
        expected_diff = days_back * 86400
        actual_diff = end - start

        # Allow 5 seconds tolerance
        assert abs(actual_diff - expected_diff) < 5

    def test_start_is_before_end(self):
        from withings_mcp_server.server import _default_date_range

        start, end = _default_date_range(1)
        assert start < end

    def test_one_day_back(self):
        from withings_mcp_server.server import _default_date_range

        start, end = _default_date_range(1)

        diff_seconds = end - start
        one_day = 86400

        assert abs(diff_seconds - one_day) < 5

    def test_zero_days_back_returns_same_start_and_end(self):
        from withings_mcp_server.server import _default_date_range

        start, end = _default_date_range(0)

        # With 0 days back, start and end should be essentially the same
        assert abs(end - start) < 5

    def test_timestamps_are_unix_epoch_based(self):
        from withings_mcp_server.server import _default_date_range

        start, end = _default_date_range(7)

        # Unix timestamps for reasonable dates should be > 1_000_000_000 (2001)
        # and < 2_000_000_000 (2033)
        assert start > 1_000_000_000
        assert end > 1_000_000_000
        assert end < 2_000_000_000


class TestDefaultYmdRange:
    """Tests for _default_ymd_range(days_back) -> tuple[str, str]."""

    def test_returns_tuple_of_two_strings(self):
        from withings_mcp_server.server import _default_ymd_range

        result = _default_ymd_range(7)

        assert isinstance(result, tuple)
        assert len(result) == 2
        start, end = result
        assert isinstance(start, str)
        assert isinstance(end, str)

    def test_end_date_is_today(self):
        from withings_mcp_server.server import _default_ymd_range

        _, end = _default_ymd_range(7)
        today = datetime.now().strftime("%Y-%m-%d")

        assert end == today

    def test_start_date_is_days_back_from_today(self):
        from withings_mcp_server.server import _default_ymd_range

        days_back = 30
        start, _ = _default_ymd_range(days_back)
        expected_start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        assert start == expected_start

    def test_dates_are_in_yyyy_mm_dd_format(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(7)

        # Verify the format by parsing; will raise ValueError if wrong
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")

    def test_seven_days_back(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(7)

        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        delta = (end_dt - start_dt).days

        assert delta == 7

    def test_one_day_back(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(1)

        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        delta = (end_dt - start_dt).days

        assert delta == 1

    def test_zero_days_back_returns_same_date(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(0)

        assert start == end

    def test_date_strings_have_correct_length(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(14)

        # YYYY-MM-DD is always 10 characters
        assert len(start) == 10
        assert len(end) == 10

    def test_start_is_before_or_equal_to_end(self):
        from withings_mcp_server.server import _default_ymd_range

        start, end = _default_ymd_range(90)

        # String comparison works for YYYY-MM-DD format
        assert start <= end


class TestFormatActivity:
    """Tests for format_activity(raw_body) -> list[dict]."""

    def _make_full_activity(self, **overrides):
        """Helper to build a complete raw activity entry with sensible defaults."""
        base = {
            "date": "2025-02-20",
            "timezone": "Europe/Berlin",
            "deviceid": "abc123",
            "hash_deviceid": "hash123",
            "brand": 18,
            "is_tracker": True,
            "steps": 8432,
            "distance": 6200.5,
            "elevation": 12.3,
            "soft": 120,
            "moderate": 30,
            "intense": 15,
            "active": 45,
            "calories": 2150.7,
            "totalcalories": 2800.2,
            "hr_average": 72,
            "hr_min": 52,
            "hr_max": 145,
            "hr_zone_0": 600,
            "hr_zone_1": 300,
            "hr_zone_2": 100,
            "hr_zone_3": 50,
            "model_id": 16,
        }
        base.update(overrides)
        return base

    def test_single_activity_day_with_all_fields(self):
        """A single complete activity record is transformed with all expected fields."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [self._make_full_activity()],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert isinstance(result, list)
        assert len(result) == 1
        record = result[0]
        assert record["date"] == "2025-02-20"
        assert record["steps"] == 8432
        assert record["calories"] == 2150.7
        assert record["total_calories"] == 2800.2
        assert record["distance_km"] == pytest.approx(6.2, abs=0.05)
        assert record["elevation_m"] == 12.3
        assert record["light_activity_min"] == 120
        assert record["moderate_activity_min"] == 30
        assert record["intense_activity_min"] == 15
        assert record["hr_average"] == 72
        assert record["hr_min"] == 52
        assert record["hr_max"] == 145

    def test_multiple_activity_days(self):
        """Multiple activity entries each produce a separate output record."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [
                self._make_full_activity(date="2025-02-20", steps=8432),
                self._make_full_activity(date="2025-02-21", steps=10200),
                self._make_full_activity(date="2025-02-22", steps=5000),
            ],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert len(result) == 3
        assert result[0]["date"] == "2025-02-20"
        assert result[0]["steps"] == 8432
        assert result[1]["date"] == "2025-02-21"
        assert result[1]["steps"] == 10200
        assert result[2]["date"] == "2025-02-22"
        assert result[2]["steps"] == 5000

    def test_distance_converted_from_meters_to_km(self):
        """Distance is divided by 1000 and rounded to 1 decimal place."""
        from withings_mcp_server.server import format_activity

        # Given: 6200.5 meters should become 6.2 km (rounded to 1 decimal)
        raw_body = {
            "activities": [self._make_full_activity(distance=6200.5)],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert result[0]["distance_km"] == 6.2

    def test_distance_rounding_edge_cases(self):
        """Distance rounding follows standard 1-decimal rounding rules."""
        from withings_mcp_server.server import format_activity

        # Given: 1550 meters = 1.55 km, rounds to 1.6 km
        raw_body = {
            "activities": [self._make_full_activity(distance=1550)],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert result[0]["distance_km"] == pytest.approx(1.6, abs=0.01)

    def test_internal_fields_are_stripped(self):
        """Device, tracker, brand, model, timezone, active, and hr_zone fields are removed."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [self._make_full_activity()],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        record = result[0]
        stripped_keys = [
            "timezone", "deviceid", "hash_deviceid", "brand",
            "is_tracker", "model_id", "active",
            "hr_zone_0", "hr_zone_1", "hr_zone_2", "hr_zone_3",
        ]
        for key in stripped_keys:
            assert key not in record, f"Internal field '{key}' should be stripped"

    def test_field_renaming(self):
        """Fields are renamed: totalcalories->total_calories, soft->light_activity_min, etc."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [self._make_full_activity()],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        record = result[0]
        # Renamed fields should exist
        assert "total_calories" in record
        assert "distance_km" in record
        assert "elevation_m" in record
        assert "light_activity_min" in record
        assert "moderate_activity_min" in record
        assert "intense_activity_min" in record

        # Original names should NOT exist
        assert "totalcalories" not in record
        assert "distance" not in record
        assert "elevation" not in record
        assert "soft" not in record
        assert "moderate" not in record
        assert "intense" not in record

    def test_empty_activities_list_returns_empty_list(self):
        """An empty activities array produces an empty output list."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {"activities": [], "more": False, "offset": 0}

        # When
        result = format_activity(raw_body)

        # Then
        assert result == []

    def test_missing_activities_key_returns_empty_list(self):
        """If 'activities' key is missing entirely, return an empty list."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {"more": False, "offset": 0}

        # When
        result = format_activity(raw_body)

        # Then
        assert result == []

    def test_zero_value_fields_are_excluded(self):
        """Fields with a value of 0 should be omitted from the output record."""
        from withings_mcp_server.server import format_activity

        # Given: steps=0, hr_min=0 should be excluded
        raw_body = {
            "activities": [
                self._make_full_activity(
                    steps=0,
                    hr_min=0,
                    elevation=0,
                    soft=0,
                )
            ],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        record = result[0]
        assert "steps" not in record, "Zero-value 'steps' should be excluded"
        assert "hr_min" not in record, "Zero-value 'hr_min' should be excluded"
        assert "elevation_m" not in record, "Zero-value 'elevation_m' should be excluded"
        assert "light_activity_min" not in record, "Zero-value 'light_activity_min' should be excluded"
        # Non-zero fields should still be present
        assert "date" in record
        assert "calories" in record

    def test_none_value_fields_are_excluded(self):
        """Fields with a value of None should be omitted from the output record."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [
                self._make_full_activity(
                    hr_average=None,
                    hr_max=None,
                )
            ],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        record = result[0]
        assert "hr_average" not in record, "None-value 'hr_average' should be excluded"
        assert "hr_max" not in record, "None-value 'hr_max' should be excluded"

    def test_truncation_at_30_entries(self):
        """More than 30 activities are truncated and the last entry is a message."""
        from withings_mcp_server.server import format_activity

        # Given: 35 activity days
        activities = [
            self._make_full_activity(date=f"2025-01-{str(i).zfill(2)}", steps=1000 + i)
            for i in range(1, 36)
        ]
        raw_body = {"activities": activities, "more": False, "offset": 0}

        # When
        result = format_activity(raw_body)

        # Then: should have 30 data entries + 1 truncation message entry
        assert len(result) == 31
        # Last entry should contain a truncation notice
        last = result[-1]
        assert "note" in last or "message" in last
        # The truncation message should mention how many were truncated
        msg_value = last.get("note") or last.get("message")
        assert "5" in msg_value, "Should mention 5 entries were truncated"
        assert "truncated" in msg_value.lower() or "omitted" in msg_value.lower()

    def test_exactly_30_entries_no_truncation(self):
        """Exactly 30 activities should not trigger truncation."""
        from withings_mcp_server.server import format_activity

        # Given: exactly 30 activity days
        activities = [
            self._make_full_activity(date=f"2025-01-{str(i).zfill(2)}", steps=1000 + i)
            for i in range(1, 31)
        ]
        raw_body = {"activities": activities, "more": False, "offset": 0}

        # When
        result = format_activity(raw_body)

        # Then: exactly 30 data entries, no truncation message
        assert len(result) == 30
        # No entry should be a truncation notice
        for record in result:
            assert "date" in record

    def test_returns_list_type(self):
        """The function always returns a list."""
        from withings_mcp_server.server import format_activity

        # Given
        raw_body = {
            "activities": [self._make_full_activity()],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert isinstance(result, list)

    def test_date_field_always_included_even_if_empty_string(self):
        """The date field should be preserved as-is (it identifies the record)."""
        from withings_mcp_server.server import format_activity

        # Given: date is a non-empty string, always present
        raw_body = {
            "activities": [self._make_full_activity(date="2025-03-15")],
            "more": False,
            "offset": 0,
        }

        # When
        result = format_activity(raw_body)

        # Then
        assert result[0]["date"] == "2025-03-15"


class TestFormatMeasurements:
    """Tests for format_measurements(raw_body) -> list[dict].

    Transforms raw Withings /measure?action=getmeas response body into
    concise human-readable records with date, named measurements, and units.
    """

    # --- Helpers to build realistic Withings API response bodies ---

    @staticmethod
    def _make_measure(value, meas_type, unit, algo=0, fm=0):
        """Build a single Withings measure dict."""
        return {"value": value, "type": meas_type, "unit": unit, "algo": algo, "fm": fm}

    @staticmethod
    def _make_measuregrp(date_ts, measures, grpid=100, attrib=0, category=1):
        """Build a single Withings measurement group dict with all internal fields."""
        return {
            "grpid": grpid,
            "attrib": attrib,
            "date": date_ts,
            "created": date_ts + 1,
            "modified": date_ts + 2,
            "category": category,
            "deviceid": "abc123",
            "hash_deviceid": "hash123",
            "measures": measures,
            "comment": None,
        }

    @staticmethod
    def _make_body(measuregrps):
        """Build the top-level 'body' dict wrapping measurement groups."""
        return {
            "updatetime": 1740009600,
            "timezone": "Europe/Berlin",
            "measuregrps": measuregrps,
        }

    # Reference timestamps (UTC):
    # 1740009600 = 2025-02-20 00:00:00 UTC
    # 1740096000 = 2025-02-21 00:00:00 UTC

    def test_single_group_with_one_measure(self):
        """A single measurement group with one weight measure produces one record."""
        from withings_mcp_server.server import format_measurements

        # Given: one group with weight=75.5 kg (value=75500, unit=-3, type=1)
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["date"] == "2025-02-20"
        assert result[0]["Weight"] == "75.5 kg"

    def test_single_group_with_multiple_measures(self):
        """A single group with weight and body fat produces one record with both."""
        from withings_mcp_server.server import format_measurements

        # Given: weight=75.5 kg + body fat=18.2%
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),   # Weight: 75.5 kg
                self._make_measure(182, 6, -1),      # Body fat: 18.2%
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert len(result) == 1
        assert result[0]["date"] == "2025-02-20"
        assert result[0]["Weight"] == "75.5 kg"
        assert result[0]["Body fat"] == "18.2%"

    def test_multiple_measurement_groups(self):
        """Multiple groups produce multiple records, one per group."""
        from withings_mcp_server.server import format_measurements

        # Given: two groups on different days
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),  # 2025-02-20 Weight: 75.5 kg
            ]),
            self._make_measuregrp(1740096000, [
                self._make_measure(74800, 1, -3),  # 2025-02-21 Weight: 74.8 kg
            ]),
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert len(result) == 2
        assert result[0]["date"] == "2025-02-20"
        assert result[0]["Weight"] == "75.5 kg"
        assert result[1]["date"] == "2025-02-21"
        assert result[1]["Weight"] == "74.8 kg"

    def test_empty_measuregrps_returns_empty_list(self):
        """When measuregrps is an empty list, return an empty list."""
        from withings_mcp_server.server import format_measurements

        # Given
        raw_body = self._make_body([])

        # When
        result = format_measurements(raw_body)

        # Then
        assert result == []

    def test_missing_measuregrps_key_returns_empty_list(self):
        """When measuregrps key is absent from raw_body, return an empty list."""
        from withings_mcp_server.server import format_measurements

        # Given: body without measuregrps key
        raw_body = {"updatetime": 1740009600, "timezone": "Europe/Berlin"}

        # When
        result = format_measurements(raw_body)

        # Then
        assert result == []

    def test_unknown_measurement_type_is_skipped(self):
        """Measurement types not in MEAS_TYPES are silently skipped."""
        from withings_mcp_server.server import format_measurements

        # Given: type 9999 is not in MEAS_TYPES, type 1 (Weight) is
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),     # known: Weight
                self._make_measure(42000, 9999, -3),  # unknown: should be skipped
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert len(result) == 1
        assert "Weight" in result[0]
        # The unknown type should not appear as any key (besides "date")
        assert set(result[0].keys()) == {"date", "Weight"}

    def test_values_are_rounded_to_one_decimal(self):
        """Converted values are rounded to 1 decimal place."""
        from withings_mcp_server.server import format_measurements

        # Given: value=75567, unit=-3 => 75.567 => rounded to 75.6
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75567, 1, -3),
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert result[0]["Weight"] == "75.6 kg"

    def test_percentage_formatting_no_space_before_percent(self):
        """Percentage types format as '18.2%' with no space before the % sign."""
        from withings_mcp_server.server import format_measurements

        # Given: Body fat type=6, unit is "%"
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(182, 6, -1),  # Body fat: 18.2%
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert result[0]["Body fat"] == "18.2%"
        # Verify no space before %
        assert " %" not in result[0]["Body fat"]

    def test_spo2_percentage_formatting(self):
        """SpO2 (type=54) also uses percentage formatting without space."""
        from withings_mcp_server.server import format_measurements

        # Given: SpO2 type=54, unit is "%", value=98, unit=0
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(98, 54, 0),  # SpO2: 98.0%
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert result[0]["SpO2"] == "98.0%"

    def test_internal_fields_are_stripped(self):
        """Output records must not contain internal Withings fields."""
        from withings_mcp_server.server import format_measurements

        # Given
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then: verify none of the internal fields leak into the output
        forbidden_keys = {
            "grpid", "attrib", "created", "modified", "algo", "fm",
            "comment", "deviceid", "hash_deviceid", "category",
        }
        for record in result:
            leaked = set(record.keys()) & forbidden_keys
            assert leaked == set(), f"Internal fields leaked into output: {leaked}"

    def test_truncation_at_50_entries(self):
        """When more than 50 measuregrps exist, return 50 entries plus a truncation message."""
        from withings_mcp_server.server import format_measurements

        # Given: 55 measurement groups
        groups = []
        for i in range(55):
            groups.append(
                self._make_measuregrp(
                    1740009600 + i * 3600,  # each 1 hour apart
                    [self._make_measure(75000 + i * 100, 1, -3)],
                    grpid=1000 + i,
                )
            )
        raw_body = self._make_body(groups)

        # When
        result = format_measurements(raw_body)

        # Then: 50 dict entries + 1 string truncation message = 51 elements
        assert len(result) == 51
        # First 50 are dicts
        for entry in result[:50]:
            assert isinstance(entry, dict)
        # Last element is the truncation message string
        assert isinstance(result[50], str)
        assert "50" in result[50]
        assert "55" in result[50]

    def test_truncation_message_content(self):
        """The truncation message follows the expected format."""
        from withings_mcp_server.server import format_measurements

        # Given: 60 measurement groups
        groups = [
            self._make_measuregrp(
                1740009600 + i * 3600,
                [self._make_measure(75000, 1, -3)],
                grpid=2000 + i,
            )
            for i in range(60)
        ]
        raw_body = self._make_body(groups)

        # When
        result = format_measurements(raw_body)

        # Then
        last = result[-1]
        assert last == "(showing 50 of 60 total, use narrower date range)"

    def test_date_format_is_yyyy_mm_dd(self):
        """The date field uses YYYY-MM-DD format."""
        from withings_mcp_server.server import format_measurements

        # Given
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then: parse the date to verify format; will raise ValueError if wrong
        date_str = result[0]["date"]
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        assert parsed.year == 2025
        assert parsed.month == 2
        assert parsed.day == 20

    def test_same_date_groups_remain_separate(self):
        """Multiple measuregrps with the same timestamp remain as separate entries."""
        from withings_mcp_server.server import format_measurements

        # Given: two groups at the exact same timestamp
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),  # Weight
            ], grpid=1),
            self._make_measuregrp(1740009600, [
                self._make_measure(182, 6, -1),  # Body fat
            ], grpid=2),
        ])

        # When
        result = format_measurements(raw_body)

        # Then: two separate entries, not merged
        assert len(result) == 2
        assert result[0]["date"] == "2025-02-20"
        assert result[1]["date"] == "2025-02-20"

    def test_non_percentage_unit_has_space_before_unit(self):
        """Non-percentage values are formatted with a space between value and unit."""
        from withings_mcp_server.server import format_measurements

        # Given: Heart rate type=11, unit is "bpm"
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(72, 11, 0),  # Heart rate: 72.0 bpm
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert result[0]["Heart rate"] == "72.0 bpm"

    def test_returns_list_type(self):
        """The return value is always a list."""
        from withings_mcp_server.server import format_measurements

        # Given
        raw_body = self._make_body([
            self._make_measuregrp(1740009600, [
                self._make_measure(75500, 1, -3),
            ])
        ])

        # When
        result = format_measurements(raw_body)

        # Then
        assert isinstance(result, list)

    def test_exactly_50_entries_no_truncation(self):
        """When exactly 50 measuregrps exist, no truncation message is added."""
        from withings_mcp_server.server import format_measurements

        # Given: exactly 50 groups
        groups = [
            self._make_measuregrp(
                1740009600 + i * 3600,
                [self._make_measure(75000, 1, -3)],
                grpid=3000 + i,
            )
            for i in range(50)
        ]
        raw_body = self._make_body(groups)

        # When
        result = format_measurements(raw_body)

        # Then: exactly 50 dict entries, no string message
        assert len(result) == 50
        for entry in result:
            assert isinstance(entry, dict)


class TestFormatSleepSummary:
    """Tests for format_sleep_summary(raw_body) -> list[dict]."""

    def _make_series_entry(self, **data_overrides):
        """Helper to build a single series entry with sensible defaults."""
        data = {
            "breathing_disturbances_intensity": 10,
            "deepsleepduration": 4320,
            "durationtosleep": 600,
            "durationtowakeup": 300,
            "hr_average": 58,
            "hr_max": 72,
            "hr_min": 48,
            "lightsleepduration": 12600,
            "nb_rem_episodes": 4,
            "night_events": 2,
            "out_of_bed_count": 1,
            "remsleepduration": 6480,
            "rr_average": 15,
            "rr_max": 18,
            "rr_min": 12,
            "sleep_efficiency": 0.92,
            "sleep_latency": 600,
            "sleep_score": 82,
            "snoring": 120,
            "snoringepisodecount": 3,
            "total_sleep_time": 23400,
            "total_timeinbed": 27000,
            "wakeup_latency": 300,
            "wakeupcount": 2,
            "wakeupduration": 1800,
            "apnea_hypopnea_index": 5,
        }
        data.update(data_overrides)
        return {
            "id": 12345,
            "timezone": "Europe/Berlin",
            "model": 32,
            "model_id": 32,
            "hash_deviceid": "hash123",
            "startdate": 1740000000,
            "enddate": 1740027000,
            "date": "2025-02-20",
            "naps": [],
            "data": data,
            "created": 1740027001,
            "modified": 1740027002,
        }

    def _make_raw_body(self, series=None, more=False, offset=0):
        """Helper to build a raw_body dict."""
        body = {"more": more, "offset": offset}
        if series is not None:
            body["series"] = series
        return body

    # --- Test: single sleep session with all data fields ---

    def test_single_session_with_all_fields(self):
        """A complete series entry produces one dict with all expected keys."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = self._make_raw_body(series=[self._make_series_entry()])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        assert isinstance(result, list)
        assert len(result) == 1

        entry = result[0]
        expected = {
            "date": "2025-02-20",
            "total_sleep_hours": 6.5,
            "deep_hours": 1.2,
            "light_hours": 3.5,
            "rem_hours": 1.8,
            "awake_hours": 0.5,
            "time_to_sleep_min": 10,
            "time_to_wakeup_min": 5,
            "wakeup_count": 2,
            "sleep_score": 82,
            "sleep_efficiency": 0.92,
            "hr_average": 58,
            "hr_min": 48,
            "hr_max": 72,
            "rr_average": 15,
            "breathing_disturbances": 10,
            "snoring_episodes": 3,
            "apnea_hypopnea_index": 5,
        }
        assert entry == expected

    # --- Test: duration conversion (seconds to hours, 1 decimal) ---

    def test_duration_seconds_to_hours_conversion(self):
        """Duration fields in seconds are converted to hours rounded to 1 decimal."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: 7200s = 2.0h, 5400s = 1.5h, 3600s = 1.0h, 900s = 0.25h -> 0.2,
        #         18000s = 5.0h
        raw_body = self._make_raw_body(series=[self._make_series_entry(
            deepsleepduration=7200,
            lightsleepduration=5400,
            remsleepduration=3600,
            wakeupduration=900,
            total_sleep_time=18000,
        )])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        assert entry["deep_hours"] == 2.0
        assert entry["light_hours"] == 1.5
        assert entry["rem_hours"] == 1.0
        assert entry["awake_hours"] == 0.2  # 900/3600 = 0.25, round(0.25, 1) = 0.2
        assert entry["total_sleep_hours"] == 5.0

    def test_duration_rounding_to_one_decimal(self):
        """Hours values are rounded to exactly 1 decimal place."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: 4320s / 3600 = 1.2 exactly
        raw_body = self._make_raw_body(series=[self._make_series_entry(
            deepsleepduration=4320,
        )])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        assert result[0]["deep_hours"] == 1.2

    # --- Test: latency conversion (seconds to minutes, int) ---

    def test_latency_seconds_to_minutes_conversion(self):
        """Latency fields in seconds are converted to integer minutes."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: 600s = 10min, 300s = 5min
        raw_body = self._make_raw_body(series=[self._make_series_entry(
            durationtosleep=600,
            durationtowakeup=300,
        )])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        assert entry["time_to_sleep_min"] == 10
        assert isinstance(entry["time_to_sleep_min"], int)
        assert entry["time_to_wakeup_min"] == 5
        assert isinstance(entry["time_to_wakeup_min"], int)

    # --- Test: field renaming works correctly ---

    def test_field_renaming(self):
        """Raw field names are renamed to the expected output names."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = self._make_raw_body(series=[self._make_series_entry(
            wakeupcount=7,
            breathing_disturbances_intensity=15,
            snoringepisodecount=8,
        )])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        # Renamed fields present with new names
        assert entry["wakeup_count"] == 7
        assert entry["breathing_disturbances"] == 15
        assert entry["snoring_episodes"] == 8

        # Old names must NOT be present
        assert "wakeupcount" not in entry
        assert "breathing_disturbances_intensity" not in entry
        assert "snoringepisodecount" not in entry

    # --- Test: internal/stripped fields are not present ---

    def test_internal_fields_stripped(self):
        """Metadata and internal fields are excluded from output."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = self._make_raw_body(series=[self._make_series_entry()])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        stripped_fields = [
            "id", "timezone", "model", "model_id", "hash_deviceid",
            "startdate", "enddate", "created", "modified", "naps",
            "snoring", "nb_rem_episodes", "night_events",
            "out_of_bed_count", "total_timeinbed", "wakeup_latency",
            "sleep_latency", "rr_max", "rr_min",
        ]
        for field in stripped_fields:
            assert field not in entry, f"Field '{field}' should be stripped but is present"

    # --- Test: empty series -> empty list ---

    def test_empty_series_returns_empty_list(self):
        """An empty series array produces an empty list."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = self._make_raw_body(series=[])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        assert result == []

    def test_missing_series_key_returns_empty_list(self):
        """When 'series' key is absent from raw_body, return empty list."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = {"more": False, "offset": 0}

        # When
        result = format_sleep_summary(raw_body)

        # Then
        assert result == []

    # --- Test: missing data fields are not included in output ---

    def test_missing_data_fields_omitted_from_output(self):
        """If a data field is not present in the raw entry, it should not appear in output."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: a minimal series entry with only a few data fields
        minimal_entry = {
            "id": 99,
            "timezone": "UTC",
            "model": 32,
            "model_id": 32,
            "hash_deviceid": "abc",
            "startdate": 1740000000,
            "enddate": 1740027000,
            "date": "2025-02-20",
            "naps": [],
            "data": {
                "sleep_score": 75,
                "hr_average": 60,
                "deepsleepduration": 3600,
            },
            "created": 1740027001,
            "modified": 1740027002,
        }
        raw_body = self._make_raw_body(series=[minimal_entry])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        assert entry["date"] == "2025-02-20"
        assert entry["sleep_score"] == 75
        assert entry["hr_average"] == 60
        assert entry["deep_hours"] == 1.0

        # Fields not in data should NOT be present (no None, no 0 defaults)
        assert "light_hours" not in entry
        assert "rem_hours" not in entry
        assert "awake_hours" not in entry
        assert "total_sleep_hours" not in entry
        assert "time_to_sleep_min" not in entry
        assert "time_to_wakeup_min" not in entry
        assert "wakeup_count" not in entry
        assert "sleep_efficiency" not in entry
        assert "hr_min" not in entry
        assert "hr_max" not in entry
        assert "rr_average" not in entry
        assert "breathing_disturbances" not in entry
        assert "snoring_episodes" not in entry
        assert "apnea_hypopnea_index" not in entry

    # --- Test: multiple sleep sessions ---

    def test_multiple_sleep_sessions(self):
        """Multiple series entries produce multiple output dicts in the same order."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        entry1 = self._make_series_entry()
        entry1["date"] = "2025-02-19"

        entry2 = self._make_series_entry()
        entry2["date"] = "2025-02-20"

        entry3 = self._make_series_entry()
        entry3["date"] = "2025-02-21"

        raw_body = self._make_raw_body(series=[entry1, entry2, entry3])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        assert len(result) == 3
        assert result[0]["date"] == "2025-02-19"
        assert result[1]["date"] == "2025-02-20"
        assert result[2]["date"] == "2025-02-21"

    # --- Test: truncation at 30 entries ---

    def test_truncation_at_30_entries(self):
        """When more than 30 entries exist, only 30 data dicts are returned plus a truncation message."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: 35 series entries
        entries = []
        for i in range(35):
            entry = self._make_series_entry()
            entry["date"] = f"2025-01-{i + 1:02d}"
            entries.append(entry)

        raw_body = self._make_raw_body(series=entries)

        # When
        result = format_sleep_summary(raw_body)

        # Then: 30 data entries + 1 truncation message = 31 total
        assert len(result) == 31

        # The first 30 should be real data entries with "date" keys
        data_entries = [r for r in result if isinstance(r, dict) and "date" in r]
        assert len(data_entries) == 30

        # The last element should be a truncation indicator
        last = result[-1]
        assert isinstance(last, (dict, str))

    def test_exactly_30_entries_not_truncated(self):
        """When exactly 30 entries exist, no truncation occurs."""
        from withings_mcp_server.server import format_sleep_summary

        # Given: exactly 30 series entries
        entries = []
        for i in range(30):
            entry = self._make_series_entry()
            entry["date"] = f"2025-01-{i + 1:02d}"
            entries.append(entry)

        raw_body = self._make_raw_body(series=entries)

        # When
        result = format_sleep_summary(raw_body)

        # Then: all 30 entries, no truncation message
        assert len(result) == 30
        for r in result:
            assert isinstance(r, dict)
            assert "date" in r

    # --- Test: pass-through fields kept as-is ---

    def test_passthrough_fields_kept_as_is(self):
        """Fields that should be kept as-is are not modified."""
        from withings_mcp_server.server import format_sleep_summary

        # Given
        raw_body = self._make_raw_body(series=[self._make_series_entry(
            sleep_score=95,
            sleep_efficiency=0.88,
            hr_average=62,
            hr_min=45,
            hr_max=85,
            rr_average=16,
            apnea_hypopnea_index=3,
        )])

        # When
        result = format_sleep_summary(raw_body)

        # Then
        entry = result[0]
        assert entry["sleep_score"] == 95
        assert entry["sleep_efficiency"] == 0.88
        assert entry["hr_average"] == 62
        assert entry["hr_min"] == 45
        assert entry["hr_max"] == 85
        assert entry["rr_average"] == 16
        assert entry["apnea_hypopnea_index"] == 3


class TestFormatHeartRate:
    """Tests for format_heart_rate(raw_body) -> dict.

    Transforms raw Withings intraday heart rate data (from /v2/measure?action=getintradayactivity)
    into an aggregated summary with overall stats and hourly (or daily) buckets.
    """

    # --- Helpers ---

    @staticmethod
    def _ts(year, month, day, hour, minute=0):
        """Build a Unix timestamp string from local-time components."""
        dt = datetime(year, month, day, hour, minute)
        return str(int(dt.timestamp()))

    @staticmethod
    def _hour_label(hour):
        """Format an hour integer as 'HH:00'."""
        return f"{hour:02d}:00"

    def _make_series(self, entries):
        """Build a series dict from a list of (timestamp_str, heart_rate) tuples.

        Each entry becomes a key in the series dict with the standard Withings
        intraday structure: heart_rate, model, model_id, deviceid.
        """
        series = {}
        for ts_str, hr in entries:
            series[ts_str] = {
                "heart_rate": hr,
                "model": "Scanwatch",
                "model_id": 93,
                "deviceid": "abc123",
            }
        return series

    # --- Test: single sample ---

    def test_single_sample(self):
        """A single HR sample produces correct overall stats and one hourly bucket."""
        from withings_mcp_server.server import format_heart_rate

        # Given: one sample at 08:00 with HR=72
        ts = self._ts(2025, 2, 20, 8, 0)
        raw_body = {"series": self._make_series([(ts, 72)])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result["min_hr"] == 72
        assert result["max_hr"] == 72
        assert result["avg_hr"] == 72
        assert result["total_samples"] == 1
        assert len(result["hourly"]) == 1
        bucket = result["hourly"][0]
        assert bucket["hour"] == self._hour_label(8)
        assert bucket["avg"] == 72
        assert bucket["min"] == 72
        assert bucket["max"] == 72
        assert bucket["samples"] == 1

    # --- Test: multiple samples in same hour ---

    def test_multiple_samples_in_same_hour(self):
        """Multiple samples within the same hour are aggregated into one bucket."""
        from withings_mcp_server.server import format_heart_rate

        # Given: three samples at 08:00, 08:05, 08:10 with HR=70, 80, 90
        ts1 = self._ts(2025, 2, 20, 8, 0)
        ts2 = self._ts(2025, 2, 20, 8, 5)
        ts3 = self._ts(2025, 2, 20, 8, 10)
        raw_body = {"series": self._make_series([(ts1, 70), (ts2, 80), (ts3, 90)])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert len(result["hourly"]) == 1
        bucket = result["hourly"][0]
        assert bucket["hour"] == self._hour_label(8)
        assert bucket["avg"] == 80  # (70+80+90)/3 = 80
        assert bucket["min"] == 70
        assert bucket["max"] == 90
        assert bucket["samples"] == 3

    # --- Test: multiple hours ---

    def test_multiple_hours(self):
        """Samples spanning multiple hours produce one bucket per hour."""
        from withings_mcp_server.server import format_heart_rate

        # Given: samples in hours 08, 09, and 10
        ts1 = self._ts(2025, 2, 20, 8, 0)
        ts2 = self._ts(2025, 2, 20, 9, 0)
        ts3 = self._ts(2025, 2, 20, 10, 0)
        raw_body = {"series": self._make_series([
            (ts1, 65), (ts2, 75), (ts3, 85),
        ])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert len(result["hourly"]) == 3
        assert result["hourly"][0]["hour"] == self._hour_label(8)
        assert result["hourly"][1]["hour"] == self._hour_label(9)
        assert result["hourly"][2]["hour"] == self._hour_label(10)

    # --- Test: empty series returns empty result ---

    def test_empty_series_returns_empty_result(self):
        """An empty series dict returns the zero/empty default structure."""
        from withings_mcp_server.server import format_heart_rate

        # Given
        raw_body = {"series": {}}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result == {
            "min_hr": 0,
            "max_hr": 0,
            "avg_hr": 0,
            "total_samples": 0,
            "hourly": [],
        }

    # --- Test: missing series key returns empty result ---

    def test_missing_series_key_returns_empty_result(self):
        """When 'series' key is absent, return the zero/empty default structure."""
        from withings_mcp_server.server import format_heart_rate

        # Given
        raw_body = {}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result == {
            "min_hr": 0,
            "max_hr": 0,
            "avg_hr": 0,
            "total_samples": 0,
            "hourly": [],
        }

    # --- Test: overall min/max/avg calculation ---

    def test_overall_min_max_avg_calculation(self):
        """Overall min_hr, max_hr, and avg_hr are computed across all samples."""
        from withings_mcp_server.server import format_heart_rate

        # Given: 5 samples with HR values 60, 70, 80, 90, 100
        # avg = (60+70+80+90+100)/5 = 80
        ts1 = self._ts(2025, 2, 20, 8, 0)
        ts2 = self._ts(2025, 2, 20, 8, 5)
        ts3 = self._ts(2025, 2, 20, 9, 0)
        ts4 = self._ts(2025, 2, 20, 9, 5)
        ts5 = self._ts(2025, 2, 20, 10, 0)
        raw_body = {"series": self._make_series([
            (ts1, 60), (ts2, 70), (ts3, 80), (ts4, 90), (ts5, 100),
        ])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result["min_hr"] == 60
        assert result["max_hr"] == 100
        assert result["avg_hr"] == 80
        assert result["total_samples"] == 5

    # --- Test: avg_hr is rounded to int ---

    def test_avg_hr_rounded_to_int(self):
        """The overall avg_hr is rounded to an integer."""
        from withings_mcp_server.server import format_heart_rate

        # Given: 3 samples with HR values 70, 71, 72
        # avg = (70+71+72)/3 = 71.0 (exact), but let's use values that don't divide evenly
        # 70, 73, 74 -> avg = 217/3 = 72.333... -> rounds to 72
        ts1 = self._ts(2025, 2, 20, 8, 0)
        ts2 = self._ts(2025, 2, 20, 8, 5)
        ts3 = self._ts(2025, 2, 20, 8, 10)
        raw_body = {"series": self._make_series([
            (ts1, 70), (ts2, 73), (ts3, 74),
        ])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result["avg_hr"] == 72
        assert isinstance(result["avg_hr"], int)

    # --- Test: hourly aggregation (avg/min/max/samples per bucket) ---

    def test_hourly_aggregation_per_bucket(self):
        """Each hourly bucket computes its own avg, min, max, and samples count."""
        from withings_mcp_server.server import format_heart_rate

        # Given: 3 samples in hour 08 and 2 samples in hour 09
        ts_08_00 = self._ts(2025, 2, 20, 8, 0)
        ts_08_05 = self._ts(2025, 2, 20, 8, 5)
        ts_08_10 = self._ts(2025, 2, 20, 8, 10)
        ts_09_00 = self._ts(2025, 2, 20, 9, 0)
        ts_09_05 = self._ts(2025, 2, 20, 9, 5)
        raw_body = {"series": self._make_series([
            (ts_08_00, 72), (ts_08_05, 75), (ts_08_10, 68),
            (ts_09_00, 82), (ts_09_05, 85),
        ])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert len(result["hourly"]) == 2

        h08 = result["hourly"][0]
        assert h08["hour"] == self._hour_label(8)
        assert h08["avg"] == 72  # round((72+75+68)/3) = round(71.666...) = 72
        assert h08["min"] == 68
        assert h08["max"] == 75
        assert h08["samples"] == 3

        h09 = result["hourly"][1]
        assert h09["hour"] == self._hour_label(9)
        assert h09["avg"] == 84  # round((82+85)/2) = round(83.5) = 84
        assert h09["min"] == 82
        assert h09["max"] == 85
        assert h09["samples"] == 2

    # --- Test: hour format is "HH:00" ---

    def test_hour_format_is_hh_colon_00(self):
        """Hourly bucket hour field uses 'HH:00' zero-padded format."""
        from withings_mcp_server.server import format_heart_rate

        # Given: a sample at 01:30 (hour 1, should be '01:00')
        ts = self._ts(2025, 2, 20, 1, 30)
        raw_body = {"series": self._make_series([(ts, 65)])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert result["hourly"][0]["hour"] == "01:00"
        # Verify zero-padding: should be 2 digits
        assert len(result["hourly"][0]["hour"]) == 5  # "HH:00"
        assert result["hourly"][0]["hour"][2] == ":"

    # --- Test: hourly sorted by hour ---

    def test_hourly_sorted_by_hour(self):
        """Hourly buckets are sorted by hour in ascending order."""
        from withings_mcp_server.server import format_heart_rate

        # Given: samples at hours 14, 08, 22, 03 (out of order in the dict)
        ts_14 = self._ts(2025, 2, 20, 14, 0)
        ts_08 = self._ts(2025, 2, 20, 8, 0)
        ts_22 = self._ts(2025, 2, 20, 22, 0)
        ts_03 = self._ts(2025, 2, 20, 3, 0)
        raw_body = {"series": self._make_series([
            (ts_14, 80), (ts_08, 70), (ts_22, 90), (ts_03, 60),
        ])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        hours = [bucket["hour"] for bucket in result["hourly"]]
        assert hours == ["03:00", "08:00", "14:00", "22:00"]

    # --- Test: entries without heart_rate key are skipped ---

    def test_entries_without_heart_rate_key_are_skipped(self):
        """Series entries that lack a 'heart_rate' key are silently skipped."""
        from withings_mcp_server.server import format_heart_rate

        # Given: two valid entries and two without heart_rate
        ts1 = self._ts(2025, 2, 20, 8, 0)
        ts2 = self._ts(2025, 2, 20, 8, 5)
        ts_bad1 = self._ts(2025, 2, 20, 8, 10)
        ts_bad2 = self._ts(2025, 2, 20, 9, 0)
        series = {
            ts1: {"heart_rate": 72, "model": "Scanwatch", "model_id": 93, "deviceid": "abc123"},
            ts2: {"heart_rate": 78, "model": "Scanwatch", "model_id": 93, "deviceid": "abc123"},
            ts_bad1: {"model": "Scanwatch", "model_id": 93, "deviceid": "abc123"},  # no heart_rate
            ts_bad2: {"steps": 100, "model": "Scanwatch"},  # no heart_rate
        }
        raw_body = {"series": series}

        # When
        result = format_heart_rate(raw_body)

        # Then: only the 2 valid samples are counted
        assert result["total_samples"] == 2
        assert result["min_hr"] == 72
        assert result["max_hr"] == 78
        assert result["avg_hr"] == 75  # (72+78)/2 = 75

    # --- Test: multi-day data returns daily instead of hourly ---

    def test_multi_day_data_returns_daily_instead_of_hourly(self):
        """When data spans enough hours (>24 unique hourly buckets), switch to daily summary."""
        from withings_mcp_server.server import format_heart_rate

        # Given: samples across 3 days with >24 unique hourly buckets
        # Day 1 (Feb 20): hours 0-11 = 12 buckets
        # Day 2 (Feb 21): hours 0-11 = 12 buckets
        # Day 3 (Feb 22): hours 0-1 = 2 buckets
        # Total = 26 unique hourly buckets (>24)
        entries = []
        for hour in range(12):
            entries.append((self._ts(2025, 2, 20, hour, 0), 60 + hour))
        for hour in range(12):
            entries.append((self._ts(2025, 2, 21, hour, 0), 70 + hour))
        for hour in range(2):
            entries.append((self._ts(2025, 2, 22, hour, 0), 80 + hour))

        raw_body = {"series": self._make_series(entries)}

        # When
        result = format_heart_rate(raw_body)

        # Then: should have 'daily' key instead of 'hourly'
        assert "daily" in result
        assert "hourly" not in result
        assert isinstance(result["daily"], list)
        assert len(result["daily"]) == 3

        # Verify each daily entry has the expected structure
        for day_entry in result["daily"]:
            assert "date" in day_entry
            assert "avg" in day_entry
            assert "min" in day_entry
            assert "max" in day_entry

        # Verify dates are sorted and formatted as YYYY-MM-DD
        dates = [d["date"] for d in result["daily"]]
        assert dates == ["2025-02-20", "2025-02-21", "2025-02-22"]

        # Verify day 1 stats: HR values 60-71
        day1 = result["daily"][0]
        assert day1["min"] == 60
        assert day1["max"] == 71
        assert day1["avg"] == round(sum(range(60, 72)) / 12)  # 65.5 -> 66

    # --- Test: returns dict type ---

    def test_returns_dict_type(self):
        """The return value is always a dict."""
        from withings_mcp_server.server import format_heart_rate

        # Given
        ts = self._ts(2025, 2, 20, 8, 0)
        raw_body = {"series": self._make_series([(ts, 72)])}

        # When
        result = format_heart_rate(raw_body)

        # Then
        assert isinstance(result, dict)


class TestFormatWorkouts:
    """Tests for format_workouts(raw_body) -> list[dict].

    Transforms raw Withings /v2/measure?action=getworkouts response body into
    concise human-readable workout records with type mapping, duration
    calculation, and unit conversions.
    """

    def _make_workout_entry(self, **overrides):
        """Helper to build a single raw workout series entry with sensible defaults."""
        data = {
            "calories": 380.5,
            "intensity": 80,
            "manual_distance": None,
            "manual_calories": None,
            "hr_average": 145,
            "hr_min": 120,
            "hr_max": 172,
            "hr_zone_0": 60,
            "hr_zone_1": 300,
            "hr_zone_2": 600,
            "hr_zone_3": 960,
            "pause_duration": 30,
            "algo_pause_duration": 28,
            "spo2_average": 96,
            "steps": 4200,
            "distance": 4800.3,
            "elevation": 25.0,
        }
        data.update(overrides.pop("data_overrides", {}))
        base = {
            "id": 12345,
            "category": 2,
            "timezone": "Europe/Berlin",
            "model": 16,
            "model_id": 16,
            "deviceid": "abc123",
            "hash_deviceid": "hash123",
            "startdate": 1740000000,
            "enddate": 1740001920,  # 32 min later
            "date": "2025-02-20",
            "modified": 1740002000,
            "attrib": 0,
            "data": data,
        }
        base.update(overrides)
        return base

    def _make_raw_body(self, series=None, more=False, offset=0):
        """Helper to build a raw_body dict."""
        body = {"more": more, "offset": offset}
        if series is not None:
            body["series"] = series
        return body

    # --- Test: single workout with all data ---

    def test_single_workout_with_all_data(self):
        """A complete workout entry produces one dict with all expected output fields."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry()])

        # When
        result = format_workouts(raw_body)

        # Then
        assert isinstance(result, list)
        assert len(result) == 1

        entry = result[0]
        expected = {
            "date": "2025-02-20",
            "type": "Run",
            "duration_min": 32,
            "calories": 380.5,
            "distance_km": 4.8,
            "elevation_m": 25.0,
            "steps": 4200,
            "hr_average": 145,
            "hr_min": 120,
            "hr_max": 172,
            "spo2_average": 96,
        }
        assert entry == expected

    # --- Test: workout type mapping from category code ---

    def test_workout_type_mapping_walk(self):
        """Category 1 maps to 'Walk' via WORKOUT_TYPES."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=1)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Walk"

    def test_workout_type_mapping_swimming(self):
        """Category 7 maps to 'Swimming' via WORKOUT_TYPES."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=7)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Swimming"

    def test_workout_type_mapping_yoga(self):
        """Category 28 maps to 'Yoga' via WORKOUT_TYPES."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=28)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Yoga"

    def test_workout_type_mapping_high_code_rowing(self):
        """Category 188 maps to 'Rowing' (high-range code)."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=188)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Rowing"

    # --- Test: unknown category code ---

    def test_unknown_category_code_produces_unknown_label(self):
        """An unmapped category code produces 'Unknown (code N)' as the type."""
        from withings_mcp_server.server import format_workouts

        # Given: category 9999 is not in WORKOUT_TYPES
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=9999)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Unknown (code 9999)"

    def test_unknown_category_code_zero(self):
        """Category 0 is not in WORKOUT_TYPES and should produce 'Unknown (code 0)'."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(category=0)])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["type"] == "Unknown (code 0)"

    # --- Test: duration calculation from timestamps ---

    def test_duration_calculation_from_timestamps(self):
        """Duration in minutes is (enddate - startdate) / 60, rounded to int."""
        from withings_mcp_server.server import format_workouts

        # Given: 1740000000 to 1740001920 = 1920 seconds = 32 minutes
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            startdate=1740000000,
            enddate=1740001920,
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["duration_min"] == 32
        assert isinstance(result[0]["duration_min"], int)

    def test_duration_calculation_rounds_to_nearest_int(self):
        """Duration should be rounded to the nearest integer minute."""
        from withings_mcp_server.server import format_workouts

        # Given: 1740000000 to 1740002700 = 2700 seconds = 45.0 exactly
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            startdate=1740000000,
            enddate=1740002700,
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["duration_min"] == 45

    def test_duration_calculation_non_exact_minutes(self):
        """Non-exact minute durations are rounded to the nearest integer."""
        from withings_mcp_server.server import format_workouts

        # Given: 1740000000 to 1740002500 = 2500 seconds = 41.67 min -> rounds to 42
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            startdate=1740000000,
            enddate=1740002500,
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["duration_min"] == 42

    # --- Test: distance meters to km conversion ---

    def test_distance_meters_to_km_conversion(self):
        """Distance is converted from meters to km with 1 decimal place."""
        from withings_mcp_server.server import format_workouts

        # Given: 4800.3 meters = 4.8003 km -> rounds to 4.8
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"distance": 4800.3}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["distance_km"] == 4.8

    def test_distance_conversion_rounding(self):
        """Distance rounding follows standard 1-decimal rules."""
        from withings_mcp_server.server import format_workouts

        # Given: 1550 meters = 1.55 km -> rounds to 1.6
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"distance": 1550}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["distance_km"] == pytest.approx(1.6, abs=0.01)

    def test_distance_conversion_large_value(self):
        """Large distance values convert correctly."""
        from withings_mcp_server.server import format_workouts

        # Given: 42195 meters (marathon) = 42.195 km -> 42.2 km
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"distance": 42195}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result[0]["distance_km"] == pytest.approx(42.2, abs=0.01)

    # --- Test: internal fields stripped ---

    def test_internal_fields_are_stripped(self):
        """Metadata and internal fields must not appear in the output."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry()])

        # When
        result = format_workouts(raw_body)

        # Then
        entry = result[0]
        stripped_keys = [
            "id", "timezone", "model", "model_id", "deviceid",
            "hash_deviceid", "modified", "attrib", "category",
            "startdate", "enddate", "data",
        ]
        for key in stripped_keys:
            assert key not in entry, f"Internal field '{key}' should be stripped"

    def test_internal_data_fields_are_stripped(self):
        """Internal data sub-fields (intensity, manual_*, hr_zone_*, pause_*) must not appear."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry()])

        # When
        result = format_workouts(raw_body)

        # Then
        entry = result[0]
        stripped_data_keys = [
            "intensity", "manual_distance", "manual_calories",
            "hr_zone_0", "hr_zone_1", "hr_zone_2", "hr_zone_3",
            "pause_duration", "algo_pause_duration",
        ]
        for key in stripped_data_keys:
            assert key not in entry, f"Internal data field '{key}' should be stripped"

    # --- Test: null/zero data fields excluded ---

    def test_null_data_fields_excluded(self):
        """Fields with None values should be omitted from the output."""
        from withings_mcp_server.server import format_workouts

        # Given: hr_average=None, spo2_average=None
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"hr_average": None, "spo2_average": None}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        entry = result[0]
        assert "hr_average" not in entry, "None-value 'hr_average' should be excluded"
        assert "spo2_average" not in entry, "None-value 'spo2_average' should be excluded"
        # Non-null fields should still be present
        assert "date" in entry
        assert "calories" in entry

    def test_zero_data_fields_excluded(self):
        """Fields with zero values should be omitted from the output."""
        from withings_mcp_server.server import format_workouts

        # Given: steps=0, elevation=0
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"steps": 0, "elevation": 0}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        entry = result[0]
        assert "steps" not in entry, "Zero-value 'steps' should be excluded"
        assert "elevation_m" not in entry, "Zero-value 'elevation_m' should be excluded"

    def test_zero_distance_excluded(self):
        """Zero distance should be excluded and not produce a distance_km field."""
        from withings_mcp_server.server import format_workouts

        # Given: distance=0
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"distance": 0}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert "distance_km" not in result[0], "Zero distance should be excluded"

    # --- Test: empty/missing series -> empty list ---

    def test_empty_series_returns_empty_list(self):
        """An empty series array produces an empty list."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[])

        # When
        result = format_workouts(raw_body)

        # Then
        assert result == []

    def test_missing_series_key_returns_empty_list(self):
        """When 'series' key is absent from raw_body, return empty list."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = {"more": False, "offset": 0}

        # When
        result = format_workouts(raw_body)

        # Then
        assert result == []

    # --- Test: multiple workouts ---

    def test_multiple_workouts_produce_multiple_records(self):
        """Multiple series entries each produce a separate output record in order."""
        from withings_mcp_server.server import format_workouts

        # Given: three different workouts
        entry1 = self._make_workout_entry(category=2, date="2025-02-18")
        entry2 = self._make_workout_entry(category=1, date="2025-02-19")
        entry3 = self._make_workout_entry(category=7, date="2025-02-20")
        raw_body = self._make_raw_body(series=[entry1, entry2, entry3])

        # When
        result = format_workouts(raw_body)

        # Then
        assert len(result) == 3
        assert result[0]["date"] == "2025-02-18"
        assert result[0]["type"] == "Run"
        assert result[1]["date"] == "2025-02-19"
        assert result[1]["type"] == "Walk"
        assert result[2]["date"] == "2025-02-20"
        assert result[2]["type"] == "Swimming"

    # --- Test: truncation at 30 entries ---

    def test_truncation_at_30_entries(self):
        """When more than 30 workouts exist, only 30 are returned plus a truncation message."""
        from withings_mcp_server.server import format_workouts

        # Given: 35 workout entries
        entries = [
            self._make_workout_entry(date=f"2025-01-{i + 1:02d}")
            for i in range(35)
        ]
        raw_body = self._make_raw_body(series=entries)

        # When
        result = format_workouts(raw_body)

        # Then: 30 data entries + 1 truncation message = 31 total
        assert len(result) == 31

        # First 30 should be real data entries with "date" keys
        data_entries = [r for r in result if isinstance(r, dict) and "date" in r]
        assert len(data_entries) == 30

        # Last element should indicate truncation
        last = result[-1]
        assert isinstance(last, (dict, str))

    def test_truncation_message_mentions_count(self):
        """The truncation message should indicate how many entries were truncated."""
        from withings_mcp_server.server import format_workouts

        # Given: 40 workout entries -> 10 truncated
        entries = [
            self._make_workout_entry(date=f"2025-01-{i + 1:02d}" if i < 28 else f"2025-02-{i - 27:02d}")
            for i in range(40)
        ]
        raw_body = self._make_raw_body(series=entries)

        # When
        result = format_workouts(raw_body)

        # Then: the truncation notice should mention the counts
        last = result[-1]
        if isinstance(last, str):
            assert "30" in last
            assert "40" in last
        elif isinstance(last, dict):
            msg_value = last.get("note") or last.get("message", "")
            assert "30" in msg_value
            assert "40" in msg_value

    def test_exactly_30_entries_no_truncation(self):
        """Exactly 30 workouts should not trigger truncation."""
        from withings_mcp_server.server import format_workouts

        # Given: exactly 30 entries
        entries = [
            self._make_workout_entry(date=f"2025-01-{i + 1:02d}")
            for i in range(30)
        ]
        raw_body = self._make_raw_body(series=entries)

        # When
        result = format_workouts(raw_body)

        # Then: exactly 30 entries, no truncation message
        assert len(result) == 30
        for entry in result:
            assert isinstance(entry, dict)
            assert "date" in entry

    # --- Test: returns list type ---

    def test_returns_list_type(self):
        """The function always returns a list."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry()])

        # When
        result = format_workouts(raw_body)

        # Then
        assert isinstance(result, list)

    # --- Test: elevation renamed to elevation_m ---

    def test_elevation_renamed_to_elevation_m(self):
        """The elevation field from data is renamed to elevation_m in the output."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"elevation": 50.0}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert "elevation_m" in result[0]
        assert result[0]["elevation_m"] == 50.0
        assert "elevation" not in result[0]

    # --- Test: distance renamed to distance_km ---

    def test_distance_renamed_to_distance_km(self):
        """The distance field from data is renamed to distance_km (converted)."""
        from withings_mcp_server.server import format_workouts

        # Given
        raw_body = self._make_raw_body(series=[self._make_workout_entry(
            data_overrides={"distance": 10000}
        )])

        # When
        result = format_workouts(raw_body)

        # Then
        assert "distance_km" in result[0]
        assert result[0]["distance_km"] == 10.0
        assert "distance" not in result[0]


class TestFormatSleepDetails:
    """Tests for format_sleep_details(raw_body) -> dict.

    Transforms raw Withings /v2/sleep?action=get response body into a dict
    containing sleep phases, aggregated HR samples, and a summary.
    """

    @staticmethod
    def _ts_to_hhmm(ts):
        """Convert a Unix timestamp to local HH:MM string (matches expected impl behavior)."""
        return datetime.fromtimestamp(ts).strftime("%H:%M")

    # --- Test: single phase with HR data ---

    def test_single_phase_with_hr_data(self):
        """A single series entry produces one phase and its HR samples."""
        # Given
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62, "1740000300": 64, "1740000600": 60},
                    "rr": {"1740000000": 15},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        # When
        result = format_sleep_details(raw_body)

        # Then
        assert isinstance(result, dict)
        assert len(result["phases"]) == 1

        phase = result["phases"][0]
        assert phase["time"] == self._ts_to_hhmm(1740000000)
        assert phase["state"] == "light"
        assert phase["duration_min"] == 15

        assert len(result["hr_samples"]) == 3
        assert all("time" in s and "bpm" in s for s in result["hr_samples"])

    # --- Test: multiple phases ---

    def test_multiple_phases(self):
        """Multiple series entries produce multiple phases in order."""
        # Given
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740000900": 56},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        # When
        result = format_sleep_details(raw_body)

        # Then
        assert len(result["phases"]) == 2
        assert result["phases"][0]["state"] == "light"
        assert result["phases"][0]["duration_min"] == 15
        assert result["phases"][1]["state"] == "deep"
        assert result["phases"][1]["duration_min"] == 30

    # --- Test: state code mapping (all known states) ---

    def test_state_code_awake(self):
        """State code 0 maps to 'awake'."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 0,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["state"] == "awake"

    def test_state_code_light(self):
        """State code 1 maps to 'light'."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 1,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["state"] == "light"

    def test_state_code_deep(self):
        """State code 2 maps to 'deep'."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 2,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["state"] == "deep"

    def test_state_code_rem(self):
        """State code 3 maps to 'rem'."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 3,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["state"] == "rem"

    # --- Test: unknown state code ---

    def test_unknown_state_code_maps_to_unknown(self):
        """An unrecognized state code (e.g. 99) maps to 'unknown'."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 99,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["state"] == "unknown"

    # --- Test: HR data merged from multiple phases ---

    def test_hr_data_merged_from_multiple_phases(self):
        """HR samples from all series entries are merged into a single flat list."""
        # Given: two phases, each with HR samples
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62, "1740000300": 64, "1740000600": 60},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740000900": 56, "1740001200": 54, "1740001500": 52, "1740001800": 55},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        # When
        result = format_sleep_details(raw_body)

        # Then: 3 + 4 = 7 total HR samples
        assert len(result["hr_samples"]) == 7

    # --- Test: HR timestamps converted to HH:MM ---

    def test_hr_timestamps_converted_to_hhmm(self):
        """HR dict keys (string Unix timestamps) are converted to HH:MM local time."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62, "1740000300": 64},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        hr_times = [s["time"] for s in result["hr_samples"]]
        expected_time_0 = self._ts_to_hhmm(1740000000)
        expected_time_1 = self._ts_to_hhmm(1740000300)

        assert expected_time_0 in hr_times
        assert expected_time_1 in hr_times

    # --- Test: HR samples are sorted by time ---

    def test_hr_samples_sorted_by_time(self):
        """HR samples are sorted chronologically."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740001800": 55, "1740000900": 56},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        bpm_values = [s["bpm"] for s in result["hr_samples"]]
        # Sorted chronologically: 1740000000(62), 1740000900(56), 1740001800(55)
        assert bpm_values == [62, 56, 55]

    # --- Test: HR sample bpm is int ---

    def test_hr_sample_bpm_is_int(self):
        """Each HR sample bpm value is an integer."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert isinstance(result["hr_samples"][0]["bpm"], int)

    # --- Test: duration calculated correctly ---

    def test_duration_calculated_correctly(self):
        """Duration in minutes is (enddate - startdate) / 60 as integer."""
        # Given: 1800 seconds = 30 minutes
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740001800,
                    "state": 2,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["phases"][0]["duration_min"] == 30
        assert isinstance(result["phases"][0]["duration_min"], int)

    # --- Test: empty series returns empty result ---

    def test_empty_series_returns_empty_result(self):
        """An empty series array produces empty phases, hr_samples, and summary."""
        raw_body = {
            "series": [],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        assert result == {"phases": [], "hr_samples": [], "summary": {}}

    # --- Test: missing series key returns empty result ---

    def test_missing_series_key_returns_empty_result(self):
        """When 'series' key is absent, return empty phases, hr_samples, and summary."""
        raw_body = {
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        assert result == {"phases": [], "hr_samples": [], "summary": {}}

    # --- Test: summary aggregation ---

    def test_summary_total_phases(self):
        """Summary includes correct total_phases count."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740000900": 56},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740002700,
                    "enddate": 1740004500,
                    "state": 3,
                    "hr": {"1740002700": 50},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["summary"]["total_phases"] == 3

    def test_summary_avg_hr(self):
        """Summary avg_hr is the integer average of all HR samples."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 60, "1740000300": 80},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        # avg of [60, 80] = 70
        assert result["summary"]["avg_hr"] == 70
        assert isinstance(result["summary"]["avg_hr"], int)

    def test_summary_min_hr(self):
        """Summary min_hr is the minimum bpm across all HR samples."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62, "1740000300": 64, "1740000600": 60},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740000900": 56, "1740001200": 54, "1740001500": 52, "1740001800": 55},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["summary"]["min_hr"] == 52

    def test_summary_max_hr(self):
        """Summary max_hr is the maximum bpm across all HR samples."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62, "1740000300": 64, "1740000600": 60},
                    "rr": {},
                    "snoring": {},
                },
                {
                    "startdate": 1740000900,
                    "enddate": 1740002700,
                    "state": 2,
                    "hr": {"1740000900": 56, "1740001200": 54},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["summary"]["max_hr"] == 64

    def test_summary_with_no_hr_data(self):
        """When there are phases but no HR data, summary has total_phases but no HR stats."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                },
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)
        assert result["summary"]["total_phases"] == 1
        assert "avg_hr" not in result["summary"]
        assert "min_hr" not in result["summary"]
        assert "max_hr" not in result["summary"]

    # --- Test: HR sample limiting (>100 samples reduced) ---

    def test_hr_samples_limited_to_approximately_100(self):
        """When more than 100 HR samples exist, downsample to ~100 by keeping every Nth."""
        # Given: 200 HR samples (one per 5-min over a series)
        hr_data = {}
        base_ts = 1740000000
        for i in range(200):
            hr_data[str(base_ts + i * 300)] = 55 + (i % 10)

        raw_body = {
            "series": [
                {
                    "startdate": base_ts,
                    "enddate": base_ts + 200 * 300,
                    "state": 2,
                    "hr": hr_data,
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        # When
        result = format_sleep_details(raw_body)

        # Then: should be capped at ~100 samples
        assert len(result["hr_samples"]) <= 100

    def test_hr_samples_not_limited_when_under_100(self):
        """When 100 or fewer HR samples exist, all are kept."""
        # Given: 50 HR samples
        hr_data = {}
        base_ts = 1740000000
        for i in range(50):
            hr_data[str(base_ts + i * 300)] = 55 + (i % 10)

        raw_body = {
            "series": [
                {
                    "startdate": base_ts,
                    "enddate": base_ts + 50 * 300,
                    "state": 2,
                    "hr": hr_data,
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        # When
        result = format_sleep_details(raw_body)

        # Then: all 50 samples are present
        assert len(result["hr_samples"]) == 50

    # --- Test: model and model_id are stripped from output ---

    def test_model_fields_stripped_from_output(self):
        """The output dict should not contain model or model_id keys."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        assert "model" not in result
        assert "model_id" not in result

    # --- Test: output structure has exactly the three expected keys ---

    def test_output_has_expected_keys(self):
        """The output dict has exactly 'phases', 'hr_samples', and 'summary' keys."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        assert set(result.keys()) == {"phases", "hr_samples", "summary"}

    # --- Test: phase time uses local HH:MM from startdate ---

    def test_phase_time_is_local_hhmm_from_startdate(self):
        """Phase 'time' field is HH:MM in local time derived from startdate."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000600,
                    "state": 1,
                    "hr": {},
                    "rr": {},
                    "snoring": {},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        expected_time = self._ts_to_hhmm(1740000000)
        assert result["phases"][0]["time"] == expected_time

    # --- Test: rr and snoring data not included in output ---

    def test_rr_and_snoring_not_in_output(self):
        """The output should not include raw rr or snoring data."""
        raw_body = {
            "series": [
                {
                    "startdate": 1740000000,
                    "enddate": 1740000900,
                    "state": 1,
                    "hr": {"1740000000": 62},
                    "rr": {"1740000000": 15},
                    "snoring": {"1740000000": 42},
                }
            ],
            "model": 32,
            "model_id": 32,
        }

        result = format_sleep_details(raw_body)

        assert "rr" not in result
        assert "snoring" not in result
        # Also not in phases
        assert "rr" not in result["phases"][0]
        assert "snoring" not in result["phases"][0]


class TestExportToCsv:
    """Tests for export_to_csv(data_type, records) -> dict.

    Writes formatted health data to a CSV file and returns a summary dict
    with file_path, rows count, and data_type.
    """

    # --- Helpers ---

    @staticmethod
    def _cleanup_export_files():
        """Remove any /tmp/withings_export_* files left from previous test runs."""
        for f in glob.glob("/tmp/withings_export_*"):
            os.remove(f)

    @staticmethod
    def _read_csv_lines(file_path):
        """Read a CSV file and return rows as a list of lists."""
        with open(file_path, newline="") as f:
            reader = csv.reader(f)
            return list(reader)

    # --- Test: writes CSV file to /tmp with correct naming pattern ---

    def test_writes_csv_file_to_tmp_with_correct_naming_pattern(self):
        """export_to_csv creates a file matching /tmp/withings_export_{data_type}_{timestamp}.csv."""
        self._cleanup_export_files()

        # Given
        records = [
            {"date": "2025-02-20", "steps": 8432, "calories": 2150.7}
        ]

        # When
        result = export_to_csv("activity", records)

        # Then
        file_path = result["file_path"]
        assert file_path.startswith("/tmp/withings_export_activity_")
        assert file_path.endswith(".csv")
        # The timestamp portion should be a valid integer
        basename = os.path.basename(file_path)
        # Pattern: withings_export_activity_1234567890.csv
        parts = basename.replace(".csv", "").split("_")
        timestamp_part = parts[-1]
        assert timestamp_part.isdigit()

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Test: CSV has correct header row for measurements ---

    def test_csv_has_correct_header_for_measurements(self):
        """Measurements CSV header is 'date' plus all measurement names from the first record."""
        self._cleanup_export_files()

        # Given: formatted measurement records with Weight and Body fat
        records = [
            {"date": "2025-02-20", "Weight (kg)": 75.5, "Body fat (%)": 22.1},
            {"date": "2025-02-21", "Weight (kg)": 75.3, "Body fat (%)": 21.9},
        ]

        # When
        result = export_to_csv("measurements", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        header = rows[0]
        assert header[0] == "date"
        # Remaining columns come from the first record's keys minus "date"
        assert "Weight (kg)" in header
        assert "Body fat (%)" in header
        assert len(header) == 3  # date + 2 measurement types

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV has correct header row for activity ---

    def test_csv_has_correct_header_for_activity(self):
        """Activity CSV header has the exact expected columns in order."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "steps": 8432, "calories": 2150.7,
                "total_calories": 2800.2, "distance_km": 6.2, "elevation_m": 12.3,
                "light_activity_min": 120, "moderate_activity_min": 30,
                "intense_activity_min": 15, "hr_average": 72, "hr_min": 52, "hr_max": 145,
            }
        ]

        # When
        result = export_to_csv("activity", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        expected_header = [
            "date", "steps", "calories", "total_calories", "distance_km",
            "elevation_m", "light_activity_min", "moderate_activity_min",
            "intense_activity_min", "hr_average", "hr_min", "hr_max",
        ]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV has correct header row for sleep ---

    def test_csv_has_correct_header_for_sleep(self):
        """Sleep CSV header has the exact expected columns in order."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "total_sleep_hours": 6.5, "deep_hours": 1.2,
                "light_hours": 3.5, "rem_hours": 1.8, "awake_hours": 0.5,
                "sleep_score": 82, "hr_average": 58,
            }
        ]

        # When
        result = export_to_csv("sleep", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        expected_header = [
            "date", "total_sleep_hours", "deep_hours", "light_hours",
            "rem_hours", "awake_hours", "sleep_score", "hr_average",
        ]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV has correct header row for workouts ---

    def test_csv_has_correct_header_for_workouts(self):
        """Workouts CSV header has the exact expected columns in order."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "type": "Run", "duration_min": 32,
                "calories": 380.5, "distance_km": 4.8, "elevation_m": 25.0,
                "steps": 4200, "hr_average": 145, "hr_min": 120, "hr_max": 172,
                "spo2_average": 96,
            }
        ]

        # When
        result = export_to_csv("workouts", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        expected_header = [
            "date", "type", "duration_min", "calories", "distance_km",
            "elevation_m", "steps", "hr_average", "hr_min", "hr_max", "spo2_average",
        ]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV has correct header for heart_rate hourly ---

    def test_csv_has_correct_header_for_heart_rate_hourly(self):
        """Heart rate hourly CSV header is hour,avg,min,max,samples."""
        self._cleanup_export_files()

        # Given: heart_rate data with "hourly" key
        records = {
            "hourly": [
                {"hour": "08:00", "avg": 72, "min": 65, "max": 80, "samples": 10},
            ]
        }

        # When
        result = export_to_csv("heart_rate", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        expected_header = ["hour", "avg", "min", "max", "samples"]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV has correct header for heart_rate daily ---

    def test_csv_has_correct_header_for_heart_rate_daily(self):
        """Heart rate daily CSV header is date,avg,min,max."""
        self._cleanup_export_files()

        # Given: heart_rate data with "daily" key
        records = {
            "daily": [
                {"date": "2025-02-20", "avg": 72, "min": 55, "max": 95},
            ]
        }

        # When
        result = export_to_csv("heart_rate", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        expected_header = ["date", "avg", "min", "max"]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: CSV body rows match input data ---

    def test_csv_body_rows_match_input_data(self):
        """Data rows in the CSV contain the correct values from input records."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "total_sleep_hours": 6.5, "deep_hours": 1.2,
                "light_hours": 3.5, "rem_hours": 1.8, "awake_hours": 0.5,
                "sleep_score": 82, "hr_average": 58,
            },
            {
                "date": "2025-02-21", "total_sleep_hours": 7.0, "deep_hours": 1.5,
                "light_hours": 3.0, "rem_hours": 2.0, "awake_hours": 0.5,
                "sleep_score": 85, "hr_average": 56,
            },
        ]

        # When
        result = export_to_csv("sleep", records)

        # Then
        rows = self._read_csv_lines(result["file_path"])
        assert len(rows) == 3  # header + 2 data rows

        # First data row
        assert rows[1][0] == "2025-02-20"
        assert rows[1][1] == "6.5"
        assert rows[1][2] == "1.2"
        assert rows[1][7] == "58"

        # Second data row
        assert rows[2][0] == "2025-02-21"
        assert rows[2][1] == "7.0"
        assert rows[2][5] == "0.5"
        assert rows[2][6] == "85"

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: returns summary dict with file_path, rows, data_type ---

    def test_returns_summary_dict_with_file_path_rows_data_type(self):
        """Return value is a dict with 'file_path', 'rows', and 'data_type' keys."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "type": "Run", "duration_min": 32,
                "calories": 380.5, "distance_km": 4.8, "elevation_m": 25.0,
                "steps": 4200, "hr_average": 145, "hr_min": 120, "hr_max": 172,
                "spo2_average": 96,
            }
        ]

        # When
        result = export_to_csv("workouts", records)

        # Then
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "rows" in result
        assert "data_type" in result
        assert result["rows"] == 1
        assert result["data_type"] == "workouts"

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: empty records creates file with header only, rows=0 ---

    def test_empty_records_creates_file_with_header_only_rows_zero(self):
        """An empty records list still creates the file with header row and returns rows=0."""
        self._cleanup_export_files()

        # Given
        records = []

        # When
        result = export_to_csv("activity", records)

        # Then
        assert result["rows"] == 0
        assert os.path.exists(result["file_path"])

        rows = self._read_csv_lines(result["file_path"])
        # Should have exactly the header row
        assert len(rows) == 1
        expected_header = [
            "date", "steps", "calories", "total_calories", "distance_km",
            "elevation_m", "light_activity_min", "moderate_activity_min",
            "intense_activity_min", "hr_average", "hr_min", "hr_max",
        ]
        assert rows[0] == expected_header

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: truncation string messages in records list are skipped ---

    def test_truncation_string_messages_in_records_list_are_skipped(self):
        """String entries (truncation messages) in the records list are ignored."""
        self._cleanup_export_files()

        # Given: records list with a truncation message mixed in
        records = [
            {
                "date": "2025-02-20", "steps": 8432, "calories": 2150.7,
                "total_calories": 2800.2, "distance_km": 6.2, "elevation_m": 12.3,
                "light_activity_min": 120, "moderate_activity_min": 30,
                "intense_activity_min": 15, "hr_average": 72, "hr_min": 52, "hr_max": 145,
            },
            "... and 15 more records (truncated)",
            {
                "date": "2025-02-21", "steps": 5000, "calories": 1800.0,
                "total_calories": 2400.0, "distance_km": 4.0, "elevation_m": 5.0,
                "light_activity_min": 90, "moderate_activity_min": 20,
                "intense_activity_min": 10, "hr_average": 68, "hr_min": 50, "hr_max": 130,
            },
        ]

        # When
        result = export_to_csv("activity", records)

        # Then: only 2 dict records written, string skipped
        assert result["rows"] == 2

        rows = self._read_csv_lines(result["file_path"])
        assert len(rows) == 3  # header + 2 data rows
        assert rows[1][0] == "2025-02-20"
        assert rows[2][0] == "2025-02-21"

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: file path starts with /tmp/withings_export_ ---

    def test_file_path_starts_with_tmp_withings_export(self):
        """The returned file_path always starts with /tmp/withings_export_."""
        self._cleanup_export_files()

        # Given
        records = [{"date": "2025-02-20", "Weight (kg)": 75.5}]

        # When
        result = export_to_csv("measurements", records)

        # Then
        assert result["file_path"].startswith("/tmp/withings_export_")

        # Cleanup
        os.remove(result["file_path"])

    # --- Test: returned file_path actually exists on disk ---

    def test_returned_file_path_actually_exists_on_disk(self):
        """The file at the returned file_path actually exists after the call."""
        self._cleanup_export_files()

        # Given
        records = [
            {
                "date": "2025-02-20", "total_sleep_hours": 6.5, "deep_hours": 1.2,
                "light_hours": 3.5, "rem_hours": 1.8, "awake_hours": 0.5,
                "sleep_score": 82, "hr_average": 58,
            }
        ]

        # When
        result = export_to_csv("sleep", records)

        # Then
        assert os.path.exists(result["file_path"])
        assert os.path.isfile(result["file_path"])

        # Cleanup
        os.remove(result["file_path"])
