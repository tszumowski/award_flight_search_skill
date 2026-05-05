#!/usr/bin/env python3
"""Explorer (cached) search example with region filtering.

Run with:
    uv run examples/explorer_search.py

Requires POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables.
"""

import os
from datetime import date, timedelta

from flight_hunter import PointsYeahClient, explore_flights, LocationFilter


def main():
    username = os.environ.get("POINTSYEAH_USERNAME")
    password = os.environ.get("POINTSYEAH_PASSWORD")

    if not username or not password:
        print("Error: Set POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables")
        return

    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=14)

    print(f"Explorer search: JFK -> Western Europe from {start} to {end}")

    with PointsYeahClient(username, password) as client:
        results = explore_flights(
            client=client,
            departure=LocationFilter(airports=["JFK"]),
            arrival=LocationFilter(regions=["WEU"]),
            start_date=start,
            end_date=end,
            cabins=["Business"],
            max_results=10,
        )

    print(f"Found {results.count} flights (total available: {results.total_available}):")
    for flight in results.flights:
        print(
            f"  {flight.date}: {flight.origin.code} -> {flight.destination.code} "
            f"({flight.destination.city}) | {flight.carrier} {flight.cabin} "
            f"| {flight.miles:,} miles | Updated: {flight.updated_ago}"
        )


if __name__ == "__main__":
    main()
