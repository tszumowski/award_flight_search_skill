# Flight Hunter

Search award flight availability on [PointsYeah.com](https://pointsyeah.com) using airline miles and credit card points.

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **A [PointsYeah.com](https://pointsyeah.com) account** — free tier works

## Quick Start

```bash
git clone <this-repo>
cd flight_hunter

# Install dependencies
uv sync

# Set credentials
export POINTSYEAH_USERNAME="your_email@example.com"
export POINTSYEAH_PASSWORD="your_password"

# Search flights
uv run main.py --origin JFK --destination LAX --days 7
```

## Credentials

Flight Hunter checks for credentials in this order:

1. **Environment variables** — `POINTSYEAH_USERNAME` and `POINTSYEAH_PASSWORD`
2. **`.env` file** — loaded automatically by the CLI

## CLI Usage

### Live Search

```bash
# Basic: JFK to LAX, next 4 days
uv run main.py -o JFK -d LAX

# Custom dates
uv run main.py -o JFK -d LAX --start-date 2026-03-01 --end-date 2026-03-05

# Business class only
uv run main.py -o JFK -d CDG --cabin Business

# Multiple origins/destinations (searches all route combinations)
uv run main.py -o SFO -o OAK -d JFK -d BOS

# Fetch full flight details (JSONL)
uv run main.py -o JFK -d LAX --fetch-details
```

### Explorer Search

```bash
# JFK to Western Europe
uv run main.py explore -f JFK -t WEU --days 7

# NY/NJ to Caribbean, Business class
uv run main.py explore -f NY -f NJ -t CAR --cabin Business

# US to Anywhere, weekends only
uv run main.py explore -f US -t ANW --weekend-only

# Sorted by duration
uv run main.py explore -f JFK -t WEU --sort duration
```

### Output

Results are saved as CSV files:
- Search: `flights_ORIGIN_to_DEST_DATE.csv`
- Explorer: `explore_FROM_to_TO_DATE.csv`

Use `--fetch-details` for full flight details as JSONL.

## Programmatic Usage

```python
from datetime import date, timedelta
from src import PointsYeahClient, search_flights

with PointsYeahClient("email@example.com", "password") as client:
    results = search_flights(
        client=client,
        origin="JFK",
        destination="LAX",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=10),
    )

    for flight in results.flights:
        print(f"{flight.date}: {flight.miles:,} miles ({flight.cabin})")
```

### Explorer Search

```python
from src import PointsYeahClient, explore_flights, LocationFilter

with PointsYeahClient("email@example.com", "password") as client:
    results = explore_flights(
        client=client,
        departure=LocationFilter(states=["NY", "NJ"]),
        arrival=LocationFilter(regions=["WEU"]),
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=14),
        cabins=["Business"],
    )

    for flight in results.flights:
        print(f"{flight.origin.code} -> {flight.destination.code}: "
              f"{flight.miles:,} miles (updated {flight.updated_ago})")
```

## Project Structure

```
flight_hunter/
├── src/                    # Core Python library
│   ├── auth.py             # AWS Cognito authentication
│   ├── client.py           # HTTP API client
│   ├── models.py           # Pydantic data models
│   ├── search.py           # Live flight search
│   ├── explorer.py         # Explorer (cached) search
│   └── locations.py        # Region/state/country constants
├── skills/                 # Agent skill definitions
│   ├── flight-search/
│   └── travel-planning/
├── examples/               # Runnable example scripts
├── main.py                 # CLI entry point
├── build_comparison.py     # HTML comparison generator
├── tests/                  # Test suite
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

## Skills

This repository includes portable skill definitions in `skills/`:

- **`skills/flight-search/SKILL.md`** — Flight search with miles/points
- **`skills/travel-planning/SKILL.md`** — Destination research and trip planning

These are standard markdown files with YAML frontmatter, usable by Claude Code, OpenCode, and other agentic platforms.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/test_core_library.py -v
```

## Troubleshooting

### "No PointsYeah credentials found"
Set credentials via environment variables or `.env` file.

### Tests fail with "No module named 'pycognito'"
Make sure you're running tests through uv:
```bash
uv sync --extra dev
uv run pytest tests/ -v
```
