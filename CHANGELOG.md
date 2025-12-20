# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-20

### Added
- Initial release of Withings MCP Server
- OAuth2 authentication with automatic token refresh
- Token generation script with local callback server
- Support for body measurements (weight, body fat, muscle mass, blood pressure, heart rate, SpO2, etc.)
- Support for activity data (steps, calories, distance, elevation)
- Support for sleep data (duration, deep sleep, REM sleep, wake-up counts)
- Support for workout/training sessions
- Support for intraday heart rate measurements
- MCP server implementation with 7 tools
- Comprehensive documentation and setup instructions
- Example environment configuration
- Test suite for API integration

### Tools
- `get_user_info` - Get user account information
- `get_measurements` - Retrieve body measurements
- `get_activity` - Get daily activity data
- `get_sleep_summary` - Get sleep summaries
- `get_sleep_details` - Get detailed sleep phase data
- `get_workouts` - Retrieve workout sessions
- `get_heart_rate` - Get heart rate measurements
- `get_authorization_url` - Generate OAuth URLs

[1.0.0]: https://github.com/schimmmi/withings-mcp-server/releases/tag/v1.0.0
