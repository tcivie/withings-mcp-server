# Withings MCP Server

An MCP (Model Context Protocol) server for integration with the Withings Health API. This server provides access to health data including body measurements, activities, sleep, and more.

## Features

- **OAuth2 Authentication** with the Withings API
- **Body Measurements**: Weight, body fat, muscle mass, blood pressure, heart rate, SpO2, etc.
- **Activity Data**: Steps, calories, distance, elevation
- **Sleep Data**: Sleep duration, deep sleep, REM sleep, wake-up counts
- **Workout Data**: Training sessions and details
- **Heart Rate**: Intraday heart rate measurements

## Installation

1. **Clone repository and install dependencies:**

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

2. **Create Withings API Credentials:**

   - Go to [Withings Developer Dashboard](https://developer.withings.com/dashboard/)
   - Create a new application
   - Note your `Client ID` and `Client Secret`
   - Set the Redirect URI to `http://localhost:8080/callback`

3. **Configure environment variables:**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
WITHINGS_CLIENT_ID=your_client_id_here
WITHINGS_CLIENT_SECRET=your_client_secret_here
WITHINGS_REDIRECT_URI=http://localhost:8080/callback
```

## Project Structure

```
withings-mcp-server/
├── src/
│   └── withings_mcp_server/
│       ├── __init__.py
│       ├── auth.py          # OAuth2 authentication
│       └── server.py        # MCP server implementation
├── tests/
│   ├── __init__.py
│   └── test_withings.py     # Manual test script
├── generate_tokens.py       # Token generation script
├── .env.example             # Example environment variables
├── .gitignore
├── pyproject.toml
└── README.md
```

## Testing the Installation

Before using the MCP server, you can verify the connection with the test script:

```bash
# Activate virtual environment if not already done
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the test script
python tests/test_withings.py
```

The test script will guide you through the OAuth flow and test various API endpoints:
- ✓ OAuth authentication
- ✓ User information
- ✓ Body measurements (last 30 days)
- ✓ Activity data (last 7 days)
- ✓ Sleep data (last 7 days)

## Authentication

Before first use, you need to generate OAuth2 tokens. **Tokens are automatically saved to the `.env` file and refreshed when needed.**

### Quick Start: Token Generation

Use the dedicated token generation script:

```bash
python generate_tokens.py
```

The script will guide you through all steps:
1. ✓ Check your API credentials
2. ✓ Generate the authorization URL
3. ✓ Exchange the code for tokens
4. ✓ Save tokens automatically to `.env`
5. ✓ Verify tokens with a test API call

### Alternative: Using Test Script

You can also use the test script which combines OAuth flow and API tests:

```bash
python tests/test_withings.py
```

### Manual Authentication

1. **Get authorization URL:**

   Use the `get_authorization_url` tool to generate an OAuth URL

2. **Authenticate in browser:**

   Open the URL in your browser and authorize access

3. **Receive authorization code:**

   After successful authorization, you'll be redirected to your Redirect URI with a `code` parameter

4. **Token management:**

   Access and Refresh Tokens are automatically:
   - Saved to the `.env` file
   - Refreshed when expired
   - Updated after each refresh

## Available Tools

### `get_authorization_url`
Generates an OAuth2 authorization URL.

**Parameters:**
- `scope` (optional): OAuth scopes (default: "user.info,user.metrics,user.activity")

### `get_user_info`
Retrieves user information.

### `get_measurements`
Retrieves body measurements.

**Parameters:**
- `meastype` (optional): Measurement type
  - `1`: Weight (kg)
  - `4`: Height (m)
  - `5`: Fat-free mass (kg)
  - `6`: Body fat percentage (%)
  - `8`: Fat mass (kg)
  - `9`: Diastolic blood pressure (mmHg)
  - `10`: Systolic blood pressure (mmHg)
  - `11`: Heart rate (bpm)
  - `12`: Temperature (°C)
  - `54`: SpO2 (%)
  - `71`: Body temperature (°C)
  - `76`: Muscle mass (kg)
  - `88`: Bone mass (kg)
  - `91`: Pulse wave velocity (m/s)
- `category` (optional): Category (1=real, 2=user_objective)
- `startdate` (optional): Start date (YYYY-MM-DD or Unix timestamp)
- `enddate` (optional): End date (YYYY-MM-DD or Unix timestamp)
- `lastupdate` (optional): Only measurements since this timestamp

### `get_activity`
Retrieves daily activity data.

**Parameters:**
- `startdateymd` (optional): Start date (YYYY-MM-DD)
- `enddateymd` (optional): End date (YYYY-MM-DD)
- `lastupdate` (optional): Only activities since this timestamp

### `get_sleep_summary`
Retrieves sleep summary.

**Parameters:**
- `startdateymd` (optional): Start date (YYYY-MM-DD)
- `enddateymd` (optional): End date (YYYY-MM-DD)
- `lastupdate` (optional): Only sleep data since this timestamp

### `get_sleep_details`
Retrieves detailed sleep data with all sleep phases.

**Parameters:**
- `startdate` (optional): Start date (YYYY-MM-DD or Unix timestamp)
- `enddate` (optional): End date (YYYY-MM-DD or Unix timestamp)

### `get_workouts`
Retrieves workout/training sessions.

**Parameters:**
- `startdateymd` (optional): Start date (YYYY-MM-DD)
- `enddateymd` (optional): End date (YYYY-MM-DD)

### `get_heart_rate`
Retrieves heart rate measurements over a time period.

**Parameters:**
- `startdate` (optional): Start date (YYYY-MM-DD or Unix timestamp)
- `enddate` (optional): End date (YYYY-MM-DD or Unix timestamp)

## MCP Configuration

To use the server with Claude Desktop, add the following to your MCP configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "withings": {
      "command": "python",
      "args": ["-m", "withings_mcp_server"],
      "env": {
        "WITHINGS_CLIENT_ID": "your_client_id",
        "WITHINGS_CLIENT_SECRET": "your_client_secret",
        "WITHINGS_ACCESS_TOKEN": "your_access_token",
        "WITHINGS_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

## Example Usage

After configuration, you can make the following requests in Claude Desktop:

```
"Show me my weight measurements from the last 7 days"
"How many steps did I walk today?"
"How was my sleep quality last night?"
"Show me my heart rate data from today"
```

## API Documentation

For more details about the Withings API:
- [Withings API Reference](https://developer.withings.com/api-reference/)
- [Developer Dashboard](https://developer.withings.com/dashboard/)

## License

MIT

## Notes

- Tokens are automatically refreshed when they expire
- All dates can be specified as YYYY-MM-DD or Unix timestamp
- The API is subject to Withings rate limits (see API documentation)
