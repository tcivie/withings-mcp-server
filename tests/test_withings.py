"""Test script for Withings MCP Server.

This script helps you test the Withings API integration manually.
It guides you through OAuth authentication and lets you test various API endpoints.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from withings_mcp_server.auth import WithingsAuth

# Load environment variables
load_dotenv()


async def test_oauth_flow():
    """Test OAuth authentication flow."""
    print("\n=== OAuth Authentication Test ===\n")

    auth = WithingsAuth()

    if not auth.client_id or not auth.client_secret:
        print("❌ Error: WITHINGS_CLIENT_ID and WITHINGS_CLIENT_SECRET must be set in .env file")
        return None

    # Check if we already have tokens
    if auth.access_token and auth.refresh_token:
        print("✓ Access token and refresh token found in environment")
        try:
            await auth.ensure_valid_token()
            print("✓ Token is valid (or refreshed successfully)")
            return auth
        except Exception as e:
            print(f"⚠ Token validation failed: {e}")
            print("  You may need to re-authenticate")

    # Generate authorization URL
    print("No valid tokens found. Starting OAuth flow...\n")
    auth_url = auth.get_authorization_url()
    print(f"1. Visit this URL in your browser:\n   {auth_url}\n")
    print("2. Authorize the application")
    print("3. You will be redirected to your redirect URI with a 'code' parameter")

    code = input("\n4. Enter the authorization code: ").strip()

    if not code:
        print("❌ No code provided")
        return None

    try:
        tokens = await auth.exchange_code_for_token(code)
        print("\n✓ Authentication successful!")
        print(f"✓ Tokens automatically saved to {auth.env_file}")
        print(f"\nYour tokens:")
        print(f"  ACCESS_TOKEN: {tokens['access_token'][:20]}...")
        print(f"  REFRESH_TOKEN: {tokens['refresh_token'][:20]}...")
        return auth
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return None


async def test_user_info(auth: WithingsAuth):
    """Test getting user information."""
    print("\n=== User Info Test ===\n")

    try:
        import httpx
        headers = auth.get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://wbsapi.withings.net/v2/user",
                headers=headers,
                params={"action": "getdevice"}
            )
            data = response.json()

            if data.get("status") == 0:
                print("✓ User info retrieved successfully")
                print(f"\nDevices: {len(data.get('body', {}).get('devices', []))}")
                for device in data.get('body', {}).get('devices', []):
                    print(f"  - {device.get('type')}: {device.get('model')}")
            else:
                print(f"❌ API Error: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_measurements(auth: WithingsAuth):
    """Test getting measurements."""
    print("\n=== Measurements Test ===\n")

    try:
        import httpx
        headers = auth.get_headers()

        # Get measurements from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://wbsapi.withings.net/measure",
                headers=headers,
                params={
                    "action": "getmeas",
                    "startdate": int(start_date.timestamp()),
                    "enddate": int(end_date.timestamp()),
                }
            )
            data = response.json()

            if data.get("status") == 0:
                measuregrps = data.get('body', {}).get('measuregrps', [])
                print(f"✓ Found {len(measuregrps)} measurement groups")

                # Show latest 5 measurements
                for grp in measuregrps[:5]:
                    date = datetime.fromtimestamp(grp['date'])
                    print(f"\n  Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
                    for measure in grp['measures']:
                        mtype = measure['type']
                        value = measure['value'] * (10 ** measure['unit'])
                        type_name = {
                            1: "Weight (kg)",
                            4: "Height (m)",
                            5: "Fat Free Mass (kg)",
                            6: "Fat Ratio (%)",
                            8: "Fat Mass Weight (kg)",
                            9: "Diastolic BP (mmHg)",
                            10: "Systolic BP (mmHg)",
                            11: "Heart Rate (bpm)",
                            12: "Temperature (°C)",
                            54: "SpO2 (%)",
                            76: "Muscle Mass (kg)",
                            88: "Bone Mass (kg)",
                        }.get(mtype, f"Type {mtype}")
                        print(f"    - {type_name}: {value:.2f}")
            else:
                print(f"❌ API Error: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_activity(auth: WithingsAuth):
    """Test getting activity data."""
    print("\n=== Activity Test ===\n")

    try:
        import httpx
        headers = auth.get_headers()

        # Get last 7 days of activity
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://wbsapi.withings.net/v2/measure",
                headers=headers,
                params={
                    "action": "getactivity",
                    "startdateymd": start_date.strftime("%Y-%m-%d"),
                    "enddateymd": end_date.strftime("%Y-%m-%d"),
                }
            )
            data = response.json()

            if data.get("status") == 0:
                activities = data.get('body', {}).get('activities', [])
                print(f"✓ Found {len(activities)} activity days")

                for activity in activities:
                    print(f"\n  Date: {activity.get('date')}")
                    print(f"    - Steps: {activity.get('steps', 0)}")
                    print(f"    - Distance: {activity.get('distance', 0)} m")
                    print(f"    - Calories: {activity.get('calories', 0)} kcal")
                    print(f"    - Elevation: {activity.get('elevation', 0)} m")
            else:
                print(f"❌ API Error: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_sleep(auth: WithingsAuth):
    """Test getting sleep data."""
    print("\n=== Sleep Test ===\n")

    try:
        import httpx
        headers = auth.get_headers()

        # Get last 7 days of sleep
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://wbsapi.withings.net/v2/sleep",
                headers=headers,
                params={
                    "action": "getsummary",
                    "startdateymd": start_date.strftime("%Y-%m-%d"),
                    "enddateymd": end_date.strftime("%Y-%m-%d"),
                }
            )
            data = response.json()

            if data.get("status") == 0:
                series = data.get('body', {}).get('series', [])
                print(f"✓ Found {len(series)} sleep sessions")

                for sleep in series:
                    start = datetime.fromtimestamp(sleep['startdate'])
                    end = datetime.fromtimestamp(sleep['enddate'])
                    duration = (end - start).total_seconds() / 3600

                    print(f"\n  Date: {start.strftime('%Y-%m-%d')}")
                    print(f"    - Duration: {duration:.1f} hours")
                    print(f"    - Deep sleep: {sleep.get('deepsleepduration', 0) / 3600:.1f} hours")
                    print(f"    - Light sleep: {sleep.get('lightsleepduration', 0) / 3600:.1f} hours")
                    print(f"    - REM sleep: {sleep.get('remsleepduration', 0) / 3600:.1f} hours")
                    print(f"    - Wake up count: {sleep.get('wakeupcount', 0)}")
            else:
                print(f"❌ API Error: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Withings MCP Server Test Script")
    print("=" * 60)

    # Test OAuth
    auth = await test_oauth_flow()
    if not auth:
        print("\n❌ Authentication failed. Cannot proceed with API tests.")
        return

    # Run API tests
    await test_user_info(auth)
    await test_measurements(auth)
    await test_activity(auth)
    await test_sleep(auth)

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


def main():
    """Main entry point."""
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
