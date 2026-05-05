"""Shared test fixtures."""

import os
import pytest
from pathlib import Path


@pytest.fixture
def project_dir():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def credentials():
    """Get PointsYeah credentials from environment.

    Tests using this fixture are skipped if credentials are not available.
    """
    username = os.getenv("POINTSYEAH_USERNAME")
    password = os.getenv("POINTSYEAH_PASSWORD")
    if not username or not password:
        pytest.skip("POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD not set")
    return username, password
