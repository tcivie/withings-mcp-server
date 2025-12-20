#!/usr/bin/env python3
"""
Token Generation Script for Withings MCP Server.

This script helps you generate OAuth2 tokens for the Withings API.
It will guide you through the authentication process and automatically
save the tokens to your .env file.

Usage:
    python generate_tokens.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from withings_mcp_server.auth import WithingsAuth

# Global variable to store the authorization code
authorization_code = None
code_received_event = threading.Event()


def print_header():
    """Print script header."""
    print("=" * 70)
    print("  Withings MCP Server - Token Generation")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print section header."""
    print()
    print(f"--- {title} " + "-" * (65 - len(title)))
    print()


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def do_GET(self):
        """Handle GET request to callback URL."""
        global authorization_code

        # Parse the URL
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/callback':
            # Extract the authorization code from query parameters
            query_params = parse_qs(parsed_path.query)

            if 'code' in query_params:
                authorization_code = query_params['code'][0]

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                html = """
                    <html>
                    <head><title>Authorization Successful</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: green;">&#10003; Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                """
                self.wfile.write(html.encode('utf-8'))

                # Signal that code has been received
                code_received_event.set()
            else:
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                error = query_params.get('error', ['Unknown error'])[0]
                html = f"""
                    <html>
                    <head><title>Authorization Failed</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: red;">&#10007; Authorization Failed</h1>
                        <p>Error: {error}</p>
                        <p>Please close this window and try again.</p>
                    </body>
                    </html>
                """
                self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def start_callback_server(port: int = 8080):
    """Start HTTP server to receive OAuth callback."""
    server = HTTPServer(('localhost', port), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server


def check_credentials(auth: WithingsAuth) -> bool:
    """Check if credentials are configured."""
    if not auth.client_id or not auth.client_secret:
        print("❌ Error: Missing Withings API credentials!")
        print()
        print("Please configure the following in your .env file:")
        print("  - WITHINGS_CLIENT_ID")
        print("  - WITHINGS_CLIENT_SECRET")
        print("  - WITHINGS_REDIRECT_URI (optional, default: http://localhost:8080/callback)")
        print()
        print("Get your credentials from: https://developer.withings.com/dashboard/")
        return False
    return True


async def generate_tokens():
    """Main token generation flow."""
    print_header()

    # Load environment variables
    load_dotenv()

    # Initialize auth
    auth = WithingsAuth()

    # Check credentials
    print_section("Step 1: Checking Configuration")
    if not check_credentials(auth):
        return False

    print("✓ Client ID found")
    print("✓ Client Secret found")
    print(f"✓ Redirect URI: {auth.redirect_uri}")

    # Check for existing tokens
    print_section("Step 2: Checking Existing Tokens")
    if auth.access_token and auth.refresh_token:
        print("⚠  Found existing tokens in environment")
        print()
        choice = input("Do you want to generate new tokens? (y/N): ").strip().lower()
        if choice != 'y':
            print("Cancelled. Existing tokens will be kept.")
            return True

    # Generate authorization URL
    print_section("Step 3: Authorization")
    scope = input("Enter OAuth scopes (press Enter for default): ").strip()
    if not scope:
        scope = "user.info,user.metrics,user.activity"

    # Start callback server
    print("Starting local callback server on http://localhost:8080...")
    server = start_callback_server(8080)

    auth_url = auth.get_authorization_url(scope)

    print()
    print("Opening browser for authorization...")
    print()
    print("If the browser doesn't open automatically, visit this URL:")
    print(f"   {auth_url}")
    print()
    print("After authorization, you'll be automatically redirected back.")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for code (with timeout)
    print("Waiting for authorization...")
    if not code_received_event.wait(timeout=300):  # 5 minute timeout
        print()
        print("❌ Error: Authorization timeout")
        print("Please try again")
        server.shutdown()
        return False

    # Get the code
    global authorization_code
    code = authorization_code

    if not code:
        print()
        print("❌ Error: No code received")
        server.shutdown()
        return False

    print("✓ Authorization code received!")
    server.shutdown()

    # Exchange code for tokens
    print_section("Step 4: Exchanging Code for Tokens")
    print("Contacting Withings API...")

    try:
        tokens = await auth.exchange_code_for_token(code)

        print()
        print("✓ Successfully obtained tokens!")
        print(f"✓ Tokens saved to: {auth.env_file}")
        print()
        print("Token details:")
        print(f"  - Access Token:  {tokens['access_token'][:30]}...")
        print(f"  - Refresh Token: {tokens['refresh_token'][:30]}...")
        print(f"  - Expires in:    {tokens.get('expires_in', 'N/A')} seconds")
        print(f"  - User ID:       {tokens.get('userid', 'N/A')}")

        print_section("Step 5: Verification")
        print("Testing token by fetching user info...")

        # Quick test
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
                devices = data.get('body', {}).get('devices', [])
                print(f"✓ Token is valid! Found {len(devices)} device(s)")
                if devices:
                    print()
                    print("Connected devices:")
                    for device in devices:
                        print(f"  - {device.get('model', 'Unknown')} ({device.get('type', 'Unknown type')})")
            else:
                print(f"⚠  Token obtained but verification failed: {data}")

        print()
        print("=" * 70)
        print("  SUCCESS! Your Withings MCP Server is ready to use.")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run the test script: python tests/test_withings.py")
        print("  2. Configure Claude Desktop with your MCP server")
        print("  3. Start using Withings data in Claude!")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        print("Please check:")
        print("  - The authorization code is correct and not expired")
        print("  - Your client credentials are valid")
        print("  - Your internet connection is working")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(generate_tokens())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print()
        print("Cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
