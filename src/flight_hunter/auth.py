"""AWS Cognito authentication for PointsYeah API."""

import logging
import os
from dataclasses import dataclass

from pycognito import Cognito

logger = logging.getLogger(__name__)

# PointsYeah Cognito configuration (discovered via browser inspection)
COGNITO_USER_POOL_ID = os.environ.get(
    "POINTSYEAH_COGNITO_USER_POOL_ID",
    "us-east-1_X8bWjbCZF",
)
COGNITO_CLIENT_ID = os.environ.get(
    "POINTSYEAH_COGNITO_CLIENT_ID",
    "3im8jrentts1pguuouv5s57gfu",
)
COGNITO_REGION = os.environ.get(
    "POINTSYEAH_COGNITO_REGION",
    "us-east-1",
)


@dataclass
class AuthTokens:
    """Authentication tokens from Cognito."""

    id_token: str
    access_token: str
    refresh_token: str


class PointsYeahAuth:
    """Handle authentication with PointsYeah via AWS Cognito."""

    def __init__(
        self,
        username: str,
        password: str,
        user_pool_id: str = COGNITO_USER_POOL_ID,
        client_id: str = COGNITO_CLIENT_ID,
    ):
        """Initialize authentication handler.

        Args:
            username: PointsYeah account email
            password: PointsYeah account password
            user_pool_id: AWS Cognito User Pool ID
            client_id: AWS Cognito Client ID
        """
        self.username = username
        self.password = password
        self._cognito = Cognito(
            user_pool_id=user_pool_id,
            client_id=client_id,
            username=username,
        )
        self._tokens: AuthTokens | None = None

    def authenticate(self) -> AuthTokens:
        """Authenticate with Cognito and return tokens.

        Returns:
            AuthTokens containing id_token, access_token, and refresh_token

        Raises:
            Exception: If authentication fails
        """
        logger.info(f"Authenticating user: {self.username}")

        try:
            self._cognito.authenticate(password=self.password)

            self._tokens = AuthTokens(
                id_token=self._cognito.id_token,
                access_token=self._cognito.access_token,
                refresh_token=self._cognito.refresh_token,
            )

            logger.info("Authentication successful")
            return self._tokens

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def refresh(self) -> AuthTokens:
        """Refresh the authentication tokens.

        Returns:
            New AuthTokens

        Raises:
            Exception: If refresh fails or no tokens exist
        """
        if not self._tokens:
            raise ValueError("No tokens to refresh. Call authenticate() first.")

        logger.info("Refreshing authentication tokens")

        try:
            self._cognito.renew_access_token()

            self._tokens = AuthTokens(
                id_token=self._cognito.id_token,
                access_token=self._cognito.access_token,
                refresh_token=self._cognito.refresh_token,
            )

            logger.info("Token refresh successful")
            return self._tokens

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise

    @property
    def id_token(self) -> str:
        """Get the current ID token (used for API authorization)."""
        if not self._tokens:
            raise ValueError("Not authenticated. Call authenticate() first.")
        return self._tokens.id_token

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._tokens is not None


def get_auth_token(username: str, password: str) -> str:
    """Convenience function to get an authentication token.

    Args:
        username: PointsYeah account email
        password: PointsYeah account password

    Returns:
        JWT ID token for API authorization
    """
    auth = PointsYeahAuth(username, password)
    auth.authenticate()
    return auth.id_token
