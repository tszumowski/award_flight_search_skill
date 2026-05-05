"""Tests for the Flight Hunter CLI (main.py)."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


PROJECT_DIR = Path(__file__).parent.parent


def run_cli(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run the CLI and return the completed process."""
    cmd = [sys.executable, str(PROJECT_DIR / "main.py")] + list(args)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_DIR),
        env=run_env,
    )


class TestCLIHelp:
    """Tests for CLI help and usage."""

    def test_help_flag(self):
        result = run_cli("--help")
        assert result.returncode == 0
        assert "Search award flight availability" in result.stdout

    def test_search_help(self):
        result = run_cli("search", "--help")
        assert result.returncode == 0
        assert "--origin" in result.stdout

    def test_explore_help(self):
        result = run_cli("explore", "--help")
        assert result.returncode == 0
        assert "--from" in result.stdout


class TestCLIMissingArgs:
    """Tests for missing/invalid arguments."""

    def test_no_args_shows_help(self):
        result = run_cli()
        # Should exit non-zero or show help
        assert result.returncode != 0 or "usage" in result.stdout.lower()

    def test_search_missing_origin(self):
        result = run_cli("search", "-d", "LAX")
        assert result.returncode != 0

    def test_search_missing_destination(self):
        result = run_cli("search", "-o", "JFK")
        assert result.returncode != 0

    def test_explore_missing_from(self):
        result = run_cli("explore", "-t", "WEU")
        assert result.returncode != 0

    def test_explore_missing_to(self):
        result = run_cli("explore", "-f", "JFK")
        assert result.returncode != 0


class TestCLIMissingCredentials:
    """Tests for credential handling."""

    def test_search_no_credentials(self):
        # Run without POINTSYEAH credentials
        env = {k: v for k, v in os.environ.items() if not k.startswith("POINTSYEAH")}
        # Also prevent .env from being loaded by setting empty values
        env["POINTSYEAH_USERNAME"] = ""
        env["POINTSYEAH_PASSWORD"] = ""
        result = run_cli("search", "-o", "JFK", "-d", "LAX", env=env)
        assert result.returncode != 0
        assert "POINTSYEAH" in result.stderr


class TestCLISearchWithCredentials:
    """CLI search tests requiring credentials."""

    @pytest.fixture(autouse=True)
    def check_credentials(self, credentials):
        """Skip if no credentials."""
        pass

    def test_search_basic(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output = f.name
        try:
            result = run_cli(
                "search", "-o", "JFK", "-d", "LAX",
                "--days", "2", "--max-results", "5",
                "--output", output, "--no-print",
            )
            assert result.returncode == 0
            assert Path(output).exists()
            # Check CSV has header
            content = Path(output).read_text()
            assert "date" in content
            assert "origin_code" in content
            assert "miles" in content
        finally:
            Path(output).unlink(missing_ok=True)

    def test_search_cabin_filter(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output = f.name
        try:
            result = run_cli(
                "search", "-o", "JFK", "-d", "LAX",
                "--cabin", "Business", "--days", "2",
                "--max-results", "5", "--output", output, "--no-print",
            )
            assert result.returncode == 0
        finally:
            Path(output).unlink(missing_ok=True)

    def test_search_no_print(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output = f.name
        try:
            result = run_cli(
                "search", "-o", "JFK", "-d", "LAX",
                "--days", "1", "--max-results", "3",
                "--output", output, "--no-print",
            )
            assert result.returncode == 0
            # With --no-print, stdout should not have the table header
            assert "Carrier" not in result.stdout or "Route" not in result.stdout
        finally:
            Path(output).unlink(missing_ok=True)


class TestCLIExploreWithCredentials:
    """CLI explore tests requiring credentials."""

    @pytest.fixture(autouse=True)
    def check_credentials(self, credentials):
        """Skip if no credentials."""
        pass

    def test_explore_basic(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output = f.name
        try:
            result = run_cli(
                "explore", "-f", "JFK", "-t", "WEU",
                "--days", "3", "--max-results", "5",
                "--output", output, "--no-print",
            )
            assert result.returncode == 0
            assert Path(output).exists()
            content = Path(output).read_text()
            assert "updated_at" in content
        finally:
            Path(output).unlink(missing_ok=True)

    def test_explore_weekend_only(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output = f.name
        try:
            result = run_cli(
                "explore", "-f", "JFK", "-t", "WEU",
                "--days", "14", "--weekend-only",
                "--max-results", "5", "--output", output, "--no-print",
            )
            assert result.returncode == 0
        finally:
            Path(output).unlink(missing_ok=True)
