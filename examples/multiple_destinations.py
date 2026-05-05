#!/usr/bin/env python3
"""Search multiple destinations and find the best miles value.

Run with:
    uv run examples/multiple_destinations.py

Requires POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables.
"""

import os
from datetime import date, timedelta

from flight_hunter import PointsYeahClient, explore_flights_aggregate, LocationFilter


def main():
    username = os.environ.get("POINTSYEAH_USERNAME")
    password = os.environ.get("POINTSYEAH_PASSWORD")

    if not username or not password:
        print("Error: Set POINTSYEAH_USERNAME and POINTSYEAH_PASSWORD environment variables")
        return

    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=7)

    print(f"Finding best Business class options from NYC to Europe, {start} to {end}")

    with PointsYeahClient(username, password) as client:
        results = explore_flights_aggregate(
            client=client,
            departure=LocationFilter(airports=["JFK", "EWR", "LGA"]),
            arrival=LocationFilter(regions=["WEU", "EEU"]),
            start_date=start,
            end_date=end,
            cabins=["Business"],
        )

    print(f"Found best options for {len(results)} destinations:")
    sorted_results = sorted(results.items(), key=lambda x: x[1].miles)
    for airport_code, flight in sorted_results[:10]:
        print(
            f"  {airport_code} ({flight.destination.city}): "
            f"{flight.miles:,} miles on {flight.carrier} | "
            f"{flight.duration_formatted} | Updated: {flight.updated_ago}"
        )


if __name__ == "__main__":
    main()
