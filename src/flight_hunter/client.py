"""HTTP client for PointsYeah API."""

import logging
from typing import Any

import httpx

from .auth import PointsYeahAuth

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.pointsyeah.com"
DEFAULT_TIMEOUT = 30.0


class PointsYeahClient:
    """HTTP client for interacting with the PointsYeah API."""

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize the API client.

        Args:
            username: PointsYeah account email
            password: PointsYeah account password
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._auth = PointsYeahAuth(username, password)
        self._client: httpx.Client | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": self._auth.id_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.pointsyeah.com",
            "Referer": "https://www.pointsyeah.com/",
        }

    def _ensure_authenticated(self) -> None:
        """Ensure we have valid authentication."""
        if not self._auth.is_authenticated:
            self._auth.authenticate()

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint (e.g., "/v2/live/user/membership")
            params: Optional query parameters

        Returns:
            JSON response as dictionary
        """
        self._ensure_authenticated()
        client = self._get_client()

        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        logger.debug(f"GET {url} params={params}")

        response = client.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Response: {data}")
        return data

    def post(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> dict:
        """Make a POST request to the API.

        Args:
            endpoint: API endpoint
            json_data: JSON body data

        Returns:
            JSON response as dictionary
        """
        self._ensure_authenticated()
        client = self._get_client()

        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        logger.debug(f"POST {url} data={json_data}")

        response = client.post(url, headers=self._get_headers(), json=json_data)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Response: {data}")
        return data

    def get_membership(self) -> dict:
        """Get user membership information."""
        return self.get("/v2/live/user/membership")

    def get_preferences(self) -> dict:
        """Get user preferences."""
        return self.get("/v2/live/user/get_preferences")

    def get_flight_history(self) -> dict:
        """Get user's flight search history."""
        return self.get("/v2/live/flight/history")

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "PointsYeahClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
