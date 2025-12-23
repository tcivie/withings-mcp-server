"""OAuth2 authentication for Withings API."""

import os
from typing import Optional
from pathlib import Path
import httpx
from datetime import datetime, timedelta


class WithingsAuth:
    """Handles OAuth2 authentication for Withings API."""

    BASE_URL = "https://wbsapi.withings.net"
    AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
    TOKEN_URL = f"{BASE_URL}/v2/oauth2"

    def __init__(self, env_file: Optional[str] = None):
        # Lazy-load env_file only when needed for writes
        self._env_file_path = env_file
        self._env_file_cached: Optional[Path] = None

        self.client_id = os.getenv("WITHINGS_CLIENT_ID")
        self.client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
        self.redirect_uri = os.getenv("WITHINGS_REDIRECT_URI", "http://localhost:8080/callback")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Load tokens from environment if available
        self.access_token = os.getenv("WITHINGS_ACCESS_TOKEN")
        self.refresh_token = os.getenv("WITHINGS_REFRESH_TOKEN")

    @property
    def env_file(self) -> Path:
        """Lazy-load env file path only when needed."""
        if self._env_file_cached is None:
            self._env_file_cached = (
                Path(self._env_file_path) if self._env_file_path
                else self._find_env_file()
            )
        return self._env_file_cached

    def _find_env_file(self) -> Path:
        """Find .env file in current directory or parent directories."""
        # First try to find from project root (where server.py is installed)
        project_root = Path(__file__).parent.parent.parent
        project_env = project_root / ".env"
        if project_env.exists():
            return project_env

        # Then try current directory and parent directories
        current = Path.cwd()
        while current != current.parent:
            env_path = current / ".env"
            if env_path.exists():
                return env_path
            current = current.parent

        # If not found, return .env in project root (not cwd to avoid permission issues)
        return project_env

    def get_authorization_url(self, scope: str = "user.info,user.metrics,user.activity") -> str:
        """Generate OAuth2 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": "random_state_string"
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"

    async def exchange_code_for_token(self, code: str, save_to_env: bool = True) -> dict:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "action": "requesttoken",
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 0:
                body = data["body"]
                self.access_token = body["access_token"]
                self.refresh_token = body["refresh_token"]
                expires_in = body.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                # Automatically save tokens to .env
                if save_to_env:
                    self._save_tokens_to_env()

                return body
            else:
                raise Exception(f"Token exchange failed: {data}")

    async def refresh_access_token(self, save_to_env: bool = True) -> dict:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise Exception("No refresh token available")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "action": "requesttoken",
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 0:
                body = data["body"]
                self.access_token = body["access_token"]
                self.refresh_token = body["refresh_token"]
                expires_in = body.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                # Automatically save refreshed tokens to .env
                if save_to_env:
                    self._save_tokens_to_env()

                return body
            else:
                raise Exception(f"Token refresh failed: {data}")

    async def ensure_valid_token(self):
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.access_token:
            raise Exception("No access token available. Please authenticate first.")

        # If no expiry time is set, try to use the token
        # If it fails with 401, the API will tell us and we can refresh
        if self.token_expires_at is None:
            # Token loaded from env without expiry - try a test request
            # If it fails, the caller will need to handle it
            return

        # Refresh if token expires in less than 5 minutes
        if datetime.now() >= self.token_expires_at - timedelta(minutes=5):
            await self.refresh_access_token()

    def get_headers(self) -> dict:
        """Get authorization headers for API requests."""
        if not self.access_token:
            raise Exception("No access token available")
        return {"Authorization": f"Bearer {self.access_token}"}

    def _save_tokens_to_env(self):
        """Save tokens to .env file."""
        if not self.access_token or not self.refresh_token:
            return

        # Read existing .env content
        env_content = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()

        # Update tokens
        env_content['WITHINGS_ACCESS_TOKEN'] = self.access_token
        env_content['WITHINGS_REFRESH_TOKEN'] = self.refresh_token

        # Write back to file
        with open(self.env_file, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

    async def save_tokens(self):
        """Save current tokens to .env file."""
        self._save_tokens_to_env()
