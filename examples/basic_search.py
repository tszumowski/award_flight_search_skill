#!/usr/bin/env python3
"""Basic flight search example.

Run with:
    uv run examples/basic_search.py

Requires POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables.
"""

import os
from datetime import date, timedelta

from flight_hunter import PointsYeahClient, search_flights


def main():
    username = os.environ.get("POINTSYEAH_USERNAME")
    password = os.environ.get("POINTSYEAH_PASSWORD")

    if not username or not password:
        print("Error: Set POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables")
        return

    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=3)

    print(f"Searching JFK -> LAX from {start} to {end}...")

    with PointsYeahClient(username, password) as client:
        results = search_flights(
            client=client,
            origin="JFK",
            destination="LAX",
            start_date=start,
            end_date=end,
            max_results=5,
        )

    print(f"Found {results.count} flights:")
    for flight in results.flights:
        print(
            f"  {flight.date}: {flight.origin.code} -> {flight.destination.code} "
            f"| {flight.carrier} {flight.cabin} | {flight.miles:,} miles + ${flight.tax} "
            f"| {flight.duration_formatted} ({flight.stops} stops)"
        )


if __name__ == "__main__":
    main()
