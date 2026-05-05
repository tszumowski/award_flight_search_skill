# Flight Hunter

Search award flight availability on [PointsYeah.com](https://pointsyeah.com) using airline miles and credit card points.

## What This Is

A Python library and CLI for searching PointsYeah's award flight database, plus portable skill definitions for AI agents.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/tszumowski/award_flight_search_skill.git

# Or clone and install in editable mode (for development)
git clone https://github.com/tszumowski/award_flight_search_skill.git
cd award_flight_search_skill
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set credentials
export POINTSYEAH_USERNAME="your_email@example.com"
export POINTSYEAH_PASSWORD="your_password"

# Search flights
flight-hunter -o JFK -d CDG --cabin Business
```

## CLI Usage

```bash
# Live search: JFK to Paris, next 4 days
flight-hunter -o JFK -d CDG

# Explorer search: US to Western Europe
flight-hunter explore -f US -t WEU --days 7

# Business class (case-insensitive: "business", "biz", etc.)
flight-hunter -o JFK -d CDG --cabin Business
```

Results are saved as CSV files in the current directory.

## Programmatic Usage

```python
from datetime import date, timedelta
from flight_hunter import PointsYeahClient, search_flights

with PointsYeahClient("email@example.com", "password") as client:
    results = search_flights(
        client=client,
        origin="JFK",
        destination="CDG",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=10),
        cabins=["Business"],
    )

    for flight in results.flights:
        print(f"{flight.date}: {flight.miles:,} miles ({flight.cabin})")
```

## Skills

Portable skill definitions for AI agents in `skills/`:

- **`skills/flight-search/SKILL.md`** — Award flight search workflows
- **`skills/travel-planning/SKILL.md`** — Destination research and trip planning

These are standard markdown files with YAML frontmatter, usable by Claude Code, OpenCode, and other agentic platforms.

## Agent Guidance

See `AGENTS.md` for skill activation triggers. When users ask about flights, miles, or award availability, the `flight-search` skill activates automatically.

## Examples

Runnable example scripts in `examples/`:

- `basic_search.py` — Simple live search
- `explorer_search.py` — Region/country search
- `multiple_destinations.py` — Multi-city searches

## Credentials

Set via environment variables or `.env` file:

```
POINTSYEAH_USERNAME=your_email@example.com
POINTSYEAH_PASSWORD=your_password
```

## Search Types

| Type | Use Case |
|------|----------|
| **Live Search** | Specific route, real-time airline availability |
| **Explorer** | Region/country/state, cached dataset |

Live Search queries airlines directly. Explorer searches a pre-cached dataset updated on a schedule. Results may differ for the same route.
