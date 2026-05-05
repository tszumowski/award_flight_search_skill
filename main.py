"""Flight Hunter CLI — Search award flight availability on PointsYeah.

Usage:
    uv run main.py --origin JFK --destination LAX --days 7
    uv run main.py explore --from JFK --to WEU --days 7
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import date, timedelta

import httpx
from dotenv import load_dotenv

from src import (
    ExplorerFlightOption,
    FlightOption,
    LocationFilter,
    PointsYeahClient,
    explore_flights,
    search_flights,
)
from src.locations import REGIONS, parse_locations

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

SEARCH_CSV_COLUMNS = [
    "date",
    "origin_code",
    "destination_code",
    "origin_city",
    "destination_city",
    "carrier",
    "program_name",
    "cabin",
    "stops",
    "duration_minutes",
    "miles",
    "tax",
    "seats_available",
    "transfer_programs",
    "detail_url",
]

EXPLORE_CSV_COLUMNS = SEARCH_CSV_COLUMNS + ["updated_at"]


def _flight_to_row(flight: FlightOption) -> dict:
    """Convert a FlightOption to a CSV row dict."""
    return {
        "date": flight.date,
        "origin_code": flight.origin.code,
        "destination_code": flight.destination.code,
        "origin_city": flight.origin.city,
        "destination_city": flight.destination.city,
        "carrier": flight.carrier,
        "program_name": flight.program_name,
        "cabin": flight.cabin,
        "stops": flight.stops,
        "duration_minutes": flight.duration_minutes,
        "miles": flight.miles,
        "tax": flight.tax,
        "seats_available": flight.seats_available if flight.seats_available else "",
        "transfer_programs": ";".join(flight.transfer_program_names),
        "detail_url": flight.detail_url or "",
    }


def _explorer_flight_to_row(flight: ExplorerFlightOption) -> dict:
    """Convert an ExplorerFlightOption to a CSV row dict."""
    row = _flight_to_row(flight)
    row["updated_at"] = flight.updated_at_iso or ""
    return row


def write_csv(path: str, rows: list[dict], columns: list[str]) -> None:
    """Write rows to a CSV file."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# JSONL detail fetching
# ---------------------------------------------------------------------------


def fetch_details(flights: list[FlightOption], jsonl_path: str) -> None:
    """Fetch detail_url JSONs and write one per line to a JSONL file."""
    with open(jsonl_path, "w") as f:
        for flight in flights:
            if not flight.detail_url:
                continue
            try:
                resp = httpx.get(flight.detail_url, timeout=15)
                resp.raise_for_status()
                detail = resp.json()
                detail["_meta"] = {
                    "date": flight.date,
                    "origin": flight.origin.code,
                    "destination": flight.destination.code,
                    "carrier": flight.carrier,
                    "cabin": flight.cabin,
                    "miles": flight.miles,
                }
                f.write(json.dumps(detail) + "\n")
            except Exception as exc:
                logger.warning(f"Failed to fetch details for {flight.origin.code}->{flight.destination.code}: {exc}")


# ---------------------------------------------------------------------------
# Table printing
# ---------------------------------------------------------------------------


def print_search_table(flights: list[FlightOption]) -> None:
    """Print a formatted table of search results to stdout."""
    if not flights:
        print("No flights found.")
        return

    header = f"{'Date':<12} {'Route':<14} {'Carrier':<6} {'Program':<28} {'Cabin':<10} {'Stops':<6} {'Duration':<10} {'Miles':>8} {'Tax':>7} {'Seats':>5} {'Transfers'}"
    print(header)
    print("-" * len(header))

    for f in flights:
        route = f"{f.origin.code}-{f.destination.code}"
        dur = f.duration_formatted
        seats = str(f.seats_available) if f.seats_available else "-"
        transfers = ", ".join(f.transfer_program_names[:3])
        if len(f.transfer_program_names) > 3:
            transfers += f" +{len(f.transfer_program_names) - 3}"

        print(
            f"{f.date:<12} {route:<14} {f.carrier:<6} {f.program_name:<28} "
            f"{f.cabin:<10} {f.stops:<6} {dur:<10} {f.miles:>8,} {f.tax:>7.2f} {seats:>5} {transfers}"
        )

    print(f"\nTotal: {len(flights)} flights")


def print_explore_table(flights: list[ExplorerFlightOption]) -> None:
    """Print a formatted table of explorer results to stdout."""
    if not flights:
        print("No flights found.")
        return

    header = f"{'Date':<12} {'Route':<14} {'Carrier':<6} {'Program':<28} {'Cabin':<10} {'Stops':<6} {'Duration':<10} {'Miles':>8} {'Tax':>7} {'Updated':<16} {'Transfers'}"
    print(header)
    print("-" * len(header))

    for f in flights:
        route = f"{f.origin.code}-{f.destination.code}"
        dur = f.duration_formatted
        updated = f.updated_ago
        transfers = ", ".join(f.transfer_program_names[:3])
        if len(f.transfer_program_names) > 3:
            transfers += f" +{len(f.transfer_program_names) - 3}"

        print(
            f"{f.date:<12} {route:<14} {f.carrier:<6} {f.program_name:<28} "
            f"{f.cabin:<10} {f.stops:<6} {dur:<10} {f.miles:>8,} {f.tax:>7.2f} {updated:<16} {transfers}"
        )

    print(f"\nTotal: {len(flights)} flights")


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


def get_credentials() -> tuple[str, str]:
    """Get PointsYeah credentials from environment.

    Returns:
        (username, password) tuple

    Raises:
        SystemExit: If credentials are missing
    """
    username = os.getenv("POINTSYEAH_USERNAME")
    password = os.getenv("POINTSYEAH_PASSWORD")
    if not username or not password:
        print(
            "Error: POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD must be set.\n"
            "Set them as environment variables or in a .env file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return username, password


# ---------------------------------------------------------------------------
# Search command
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    """Execute the search command."""
    username, password = get_credentials()

    origins = [o.upper() for o in args.origin]
    destinations = [d.upper() for d in args.destination]

    start = args.start_date
    end = args.end_date
    if start is None:
        start = date.today()
    if end is None:
        end = start + timedelta(days=args.days - 1)

    cabins = args.cabin if args.cabin else None
    max_results = args.max_results

    all_flights: list[FlightOption] = []

    with PointsYeahClient(username, password) as client:
        for orig in origins:
            for dest in destinations:
                print(f"Searching {orig} -> {dest} ({start} to {end})...")
                results = search_flights(
                    client=client,
                    origin=orig,
                    destination=dest,
                    start_date=start,
                    end_date=end,
                    cabins=cabins,
                    max_results=max_results,
                )
                all_flights.extend(results.flights)
                print(f"  Found {results.count} flights")

    # Sort by miles
    all_flights.sort(key=lambda f: f.miles)

    # Determine output filename
    if args.output:
        csv_path = args.output
    else:
        orig_str = "_".join(origins)
        dest_str = "_".join(destinations)
        csv_path = f"flights_{orig_str}_to_{dest_str}_{date.today().isoformat()}.csv"

    # Write CSV
    rows = [_flight_to_row(f) for f in all_flights]
    write_csv(csv_path, rows, SEARCH_CSV_COLUMNS)
    print(f"\nSaved {len(all_flights)} flights to {csv_path}")

    # Optionally fetch details
    if args.fetch_details:
        jsonl_path = csv_path.rsplit(".", 1)[0] + ".jsonl"
        print(f"Fetching flight details to {jsonl_path}...")
        fetch_details(all_flights, jsonl_path)
        print(f"Saved details to {jsonl_path}")

    # Print table
    if not args.no_print:
        print()
        print_search_table(all_flights)


# ---------------------------------------------------------------------------
# Explore command
# ---------------------------------------------------------------------------


def cmd_explore(args: argparse.Namespace) -> None:
    """Execute the explore command."""
    username, password = get_credentials()

    from_codes = [c.upper() for c in getattr(args, "from")]
    to_codes = [c.upper() for c in args.to]

    departure = parse_locations(from_codes)
    arrival = parse_locations(to_codes)

    start = args.start_date
    end = args.end_date
    if start is None:
        start = date.today()
    if end is None:
        end = start + timedelta(days=args.days - 1)

    cabins = args.cabin if args.cabin else None
    weekend_only = args.weekend_only
    sort = args.sort
    max_results = args.max_results

    print(f"Exploring {departure.summary()} -> {arrival.summary()} ({start} to {end})...")

    with PointsYeahClient(username, password) as client:
        results = explore_flights(
            client=client,
            departure=departure,
            arrival=arrival,
            start_date=start,
            end_date=end,
            cabins=cabins,
            max_results=max_results,
            weekend_only=weekend_only,
            sort=sort,
        )

    all_flights = results.flights
    print(f"Found {len(all_flights)} flights")

    # Determine output filename
    if args.output:
        csv_path = args.output
    else:
        from_str = "_".join(from_codes)
        to_str = "_".join(to_codes)
        csv_path = f"explore_{from_str}_to_{to_str}_{date.today().isoformat()}.csv"

    # Write CSV
    rows = [_explorer_flight_to_row(f) for f in all_flights]
    write_csv(csv_path, rows, EXPLORE_CSV_COLUMNS)
    print(f"Saved {len(all_flights)} flights to {csv_path}")

    # Print table
    if not args.no_print:
        print()
        print_explore_table(all_flights)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_date(s: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    return date.fromisoformat(s)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="flight-hunter",
        description="Search award flight availability on PointsYeah.com",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- search (default) ---
    search_parser = subparsers.add_parser("search", help="Live flight search between airports")
    search_parser.add_argument("-o", "--origin", action="append", required=True, help="Origin airport code (can repeat)")
    search_parser.add_argument("-d", "--destination", action="append", required=True, help="Destination airport code (can repeat)")
    search_parser.add_argument("--days", type=int, default=4, help="Number of days to search (default: 4)")
    search_parser.add_argument("--cabin", action="append", help="Cabin class filter (can repeat)")
    search_parser.add_argument("--start-date", type=parse_date, default=None, help="Start date (YYYY-MM-DD)")
    search_parser.add_argument("--end-date", type=parse_date, default=None, help="End date (YYYY-MM-DD)")
    search_parser.add_argument("--max-results", type=int, default=500, help="Max results (default: 500)")
    search_parser.add_argument("--output", help="Custom output CSV filename")
    search_parser.add_argument("--fetch-details", action="store_true", help="Download full flight details (JSONL)")
    search_parser.add_argument("--no-print", action="store_true", help="Save CSV only, no console table")
    search_parser.set_defaults(func=cmd_search)

    # Also add search args to the top-level parser for default subcommand behavior
    parser.add_argument("-o", "--origin", action="append", help="Origin airport code (can repeat)")
    parser.add_argument("-d", "--destination", action="append", help="Destination airport code (can repeat)")
    parser.add_argument("--days", type=int, default=4, help="Number of days to search (default: 4)")
    parser.add_argument("--cabin", action="append", help="Cabin class filter (can repeat)")
    parser.add_argument("--start-date", type=parse_date, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=parse_date, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-results", type=int, default=500, help="Max results (default: 500)")
    parser.add_argument("--output", help="Custom output CSV filename")
    parser.add_argument("--fetch-details", action="store_true", help="Download full flight details (JSONL)")
    parser.add_argument("--no-print", action="store_true", help="Save CSV only, no console table")

    # --- explore ---
    explore_parser = subparsers.add_parser("explore", help="Search cached flights with region/country/state filtering")
    explore_parser.add_argument("-f", "--from", action="append", required=True, dest="from", help="Origin location code (can repeat)")
    explore_parser.add_argument("-t", "--to", action="append", required=True, help="Destination location code (can repeat)")
    explore_parser.add_argument("--days", type=int, default=7, help="Number of days to search (default: 7)")
    explore_parser.add_argument("--cabin", action="append", help="Cabin class filter (can repeat)")
    explore_parser.add_argument("--start-date", type=parse_date, default=None, help="Start date (YYYY-MM-DD)")
    explore_parser.add_argument("--end-date", type=parse_date, default=None, help="End date (YYYY-MM-DD)")
    explore_parser.add_argument("--weekend-only", action="store_true", help="Weekend departures only")
    explore_parser.add_argument("--sort", choices=["miles", "duration", "tax"], default="miles", help="Sort order (default: miles)")
    explore_parser.add_argument("--max-results", type=int, default=500, help="Max results (default: 500)")
    explore_parser.add_argument("--output", help="Custom output CSV filename")
    explore_parser.add_argument("--no-print", action="store_true", help="Save CSV only, no console table")
    explore_parser.set_defaults(func=cmd_explore)

    return parser


def main() -> None:
    """Entry point."""
    logging.basicConfig(level=logging.WARNING)
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "explore":
        cmd_explore(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.origin and args.destination:
        # Default subcommand: treat top-level --origin/--destination as search
        args.func = cmd_search
        cmd_search(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
