---
name: flight-search
description: Search award flight availability using PointsYeah. Use when user asks about flights with miles/points, award availability, cheap redemptions, or PointsYeah.
---

# Flight Search Skill

Search award flight availability on PointsYeah.com using the `flight_hunter` Python library.

## Installation

```bash
# Install directly from GitHub
pip install git+https://github.com/tszumowski/award_flight_search_skill.git

# Or clone and install in editable mode
git clone https://github.com/tszumowski/award_flight_search_skill.git
cd award_flight_search_skill
pip install -e .
```

This installs the `flight_hunter` Python package and the `flight-hunter` CLI command.

## Set Credentials

Create a `.env` file or export environment variables:

```bash
export POINTSYEAH_USERNAME="your_email@example.com"
export POINTSYEAH_PASSWORD="your_password"
```

## Quick Start — CLI

```bash
# Search JFK to LAX for next 4 days
flight-hunter -o JFK -d LAX

# Search with custom dates and cabin filter
flight-hunter -o JFK -d CDG --start-date 2026-03-01 --end-date 2026-03-07 --cabin Business

# Explorer search: JFK to Western Europe
flight-hunter explore -f JFK -t WEU --days 7

# Multiple origins/destinations (all combinations)
flight-hunter -o SFO -o OAK -d JFK -d BOS --days 7
```

## Quick Start — Programmatic

```python
from datetime import date, timedelta
from flight_hunter import PointsYeahClient, search_flights

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

## API Reference

### `search_flights(client, origin, destination, start_date, end_date, cabins=None, max_results=100)`

Live search for award flights between specific airports.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | PointsYeahClient | Yes | Authenticated client instance |
| `origin` | str | Yes | Airport code (JFK) or metro code (NYC) |
| `destination` | str | Yes | Airport code or metro code |
| `start_date` | date | Yes | Search start date |
| `end_date` | date | Yes | Search end date |
| `cabins` | list[str] | No | ["Economy", "Premium Economy", "Business", "First"] |
| `max_results` | int | No | Default: 100 |

**Returns:** `SearchResults` with `.flights` list, `.count`, `.origin_code`, `.destination_code`

### `explore_flights(client, departure, arrival, start_date, end_date, cabins=None, max_results=500, weekend_only=False, sort="miles")`

Explorer search using cached data with flexible location filtering.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | PointsYeahClient | Yes | Authenticated client instance |
| `departure` | LocationFilter | Yes | Origin locations |
| `arrival` | LocationFilter | Yes | Destination locations |
| `start_date` | date | Yes | Search start date |
| `end_date` | date | Yes | Search end date |
| `cabins` | list[str] | No | Cabin class filter |
| `max_results` | int | No | Default: 500 |
| `weekend_only` | bool | No | Filter to weekend departures |
| `sort` | str | No | "miles", "duration", or "tax" |

**Returns:** `ExplorerSearchResults` with `.flights`, `.count`, `.total_available`

### `explore_flights_aggregate(client, departure, arrival, start_date, end_date, cabins=None)`

Returns one best-value flight per destination airport.

**Returns:** `dict[str, ExplorerFlightOption]` mapping airport code to best flight

### `LocationFilter`

Flexible location filter supporting multiple location types:

```python
from flight_hunter import LocationFilter

# Airports only
LocationFilter(airports=["JFK", "EWR"])

# US states
LocationFilter(states=["NY", "NJ"])

# Regions
LocationFilter(regions=["WEU", "CAR"])

# Countries
LocationFilter(countries=["US", "FR"])

# Continents
LocationFilter(continents=["EU", "NA"])
```

## Location Code Types

Codes are auto-detected by format:

| Type | Examples | Format |
|------|----------|--------|
| Airports | JFK, LAX, CDG | 3 letters |
| Regions | WEU, CAR, SEA | Known 3-letter codes |
| States | CA, NY, TX, BC | 2 letters (US/Canada) |
| Countries | US, FR, JP | 2-letter ISO |
| Continents | EU, NA, AS | 2 letters |
| Wildcard | ANW | Anywhere |

### Region Codes

| Code | Region |
|------|--------|
| WEU | Western Europe |
| EEU | Eastern Europe |
| CAR | Caribbean |
| SAM | South America |
| CAM | Central America |
| SEA | Southeast Asia |
| NEA | Northeast Asia |
| SAS | South Asia |
| OCE | Oceania |
| AFR | Africa |
| MEA | Middle East |
| ANW | Anywhere |

## Presenting Results

After receiving results, present them in a formatted table. Highlight:
- Best value options (lowest miles)
- Non-stop flights
- Transfer program availability (Chase UR, Amex MR, Capital One, etc.)
- For explorer results, include data freshness (`updated_ago` field)

## Troubleshooting

- **"No PointsYeah credentials found"**: Set `POINTSYEAH_USERNAME` and `POINTSYEAH_PASSWORD` environment variables or create a `.env` file
- **No results**: Try broader dates, different airports/regions, or use explorer for cached data
- **Authentication failed**: Verify your PointsYeah email and password are correct

## CSV Output Format

Each search saves a CSV with these columns:
- `date`, `origin_code`, `destination_code`, `origin_city`, `destination_city`
- `carrier`, `program_name`, `cabin`, `stops`, `duration_minutes`
- `miles`, `tax`, `seats_available`, `transfer_programs`, `detail_url`

Explorer CSV additionally includes `updated_at`.
