"""Explorer search functionality for cached/pre-crawled award flight data.

This module provides search functions for the PointsYeah Explorer API,
which returns cached flight data from other users' searches. Unlike live
searches, explorer results include data freshness timestamps and support
region-based location filtering.
"""

import logging
from datetime import date
from typing import Any

from .client import PointsYeahClient
from .models import (
    ALL_BANKS,
    ALL_PROGRAMS,
    Airport,
    ExplorerFlightOption,
    ExplorerSearchResults,
    LocationFilter,
    TransferProgram,
)

logger = logging.getLogger(__name__)

EXPLORER_SEARCH_ENDPOINT = "/v2/live/explorer/search"
EXPLORER_AGGREGATE_ENDPOINT = "/v2/live/explorer/search/aggregate"
EXPLORER_FILTER_RANGE_ENDPOINT = "/v2/live/explorer/get_filter_range"


def _build_explorer_payload(
    departure: LocationFilter,
    arrival: LocationFilter,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
    banks: list[str] | None = None,
    programs: list[str] | None = None,
    seats: int = 1,
    weekend_only: bool = False,
    sort: str = "miles",
    premium_cabin_percentage: int = 0,
    collection: bool = True,
    page: int = 1,
    page_size: int = 100,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Build the explorer search request payload.

    Args:
        departure: Origin location filter
        arrival: Destination location filter
        start_date: Start date for the search range
        end_date: End date for the search range
        cabins: List of cabin classes to include
        banks: List of credit card banks to filter by
        programs: List of airline programs to filter by
        seats: Number of seats required
        weekend_only: Filter to weekend departures only
        sort: Sort order ("miles", "duration", "tax", "updated")
        premium_cabin_percentage: Minimum percentage in premium cabin
        collection: Include collection flag (usually True for explorer)
        page: Page number for pagination
        page_size: Number of results per page
        group_by: Group results by field (e.g., "arrival_airport")

    Returns:
        Request payload dictionary
    """
    if cabins is None:
        cabins = ["Economy", "Premium Economy", "Business", "First"]

    payload = {
        "departure": departure.to_api_dict(),
        "arrival": arrival.to_api_dict(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "banks": banks if banks is not None else ALL_BANKS,
        "programs": programs if programs is not None else ALL_PROGRAMS,
        "cabins": cabins,
        "premium_cabin_percentage": premium_cabin_percentage,
        "trip": "",
        "sort": sort,
        "pagination": {"page": page, "page_size": page_size},
        "seats": seats,
        "weekend_only": weekend_only,
        "collection": collection,
    }

    if group_by:
        payload["group_by"] = group_by

    return payload


def _parse_explorer_result(result: dict[str, Any]) -> ExplorerFlightOption:
    """Parse a single explorer result from the API response.

    Args:
        result: Raw flight result dictionary from API

    Returns:
        ExplorerFlightOption model instance
    """
    departure = result.get("departure") or {}
    arrival = result.get("arrival") or {}

    origin = Airport(
        code=departure.get("code", ""),
        city=departure.get("city", ""),
        country_name=departure.get("country_name", ""),
    )

    dest = Airport(
        code=arrival.get("code", ""),
        city=arrival.get("city", ""),
        country_name=arrival.get("country_name", ""),
    )

    transfer_programs = [
        TransferProgram(
            bank=t.get("bank", ""),
            code=t.get("code", ""),
            bonus_percentage=t.get("bonus_percentage", 0),
        )
        for t in result.get("transfer", [])
    ]

    return ExplorerFlightOption(
        date=result.get("departure_date", ""),
        stops=result.get("stops", 0),
        departure_time=None,
        arrival_time=None,
        duration_minutes=result.get("duration", 0),
        miles=result.get("miles", 0),
        tax=result.get("tax", 0.0),
        cabin=result.get("cabin", ""),
        carrier=result.get("program", ""),
        origin=origin,
        destination=dest,
        seats_available=result.get("seats"),
        transfer_programs=transfer_programs,
        detail_url=result.get("detail_url"),
        # Explorer-specific fields
        created_at=result.get("created_at"),
        updated_at=result.get("updated_at"),
        image_url=result.get("img"),
        latitude=arrival.get("latitude"),
        longitude=arrival.get("longitude"),
        premium_cabin_percentage=result.get("premium_cabin_percentage", 0),
    )


def explore_flights(
    client: PointsYeahClient,
    departure: LocationFilter,
    arrival: LocationFilter,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
    banks: list[str] | None = None,
    programs: list[str] | None = None,
    max_results: int = 500,
    seats: int = 1,
    weekend_only: bool = False,
    sort: str = "miles",
    fetch_all: bool = True,
) -> ExplorerSearchResults:
    """Search for cached award flights with flexible location filters.

    This searches the PointsYeah explorer database, which contains
    pre-crawled flight data from other users' searches. Results include
    data freshness timestamps (updated_at).

    Args:
        client: Authenticated PointsYeahClient instance
        departure: Origin location filter (airports, regions, states, etc.)
        arrival: Destination location filter
        start_date: Start date for the search range
        end_date: End date for the search range
        cabins: List of cabin classes to include (default: all)
        banks: List of credit card banks to filter by
        programs: List of airline programs to filter by
        max_results: Maximum number of results to return
        seats: Number of seats required (default: 1)
        weekend_only: Filter to weekend departures only
        sort: Sort order - "miles", "duration", "tax" (default: "miles")
        fetch_all: If True, paginate through all results up to max_results

    Returns:
        ExplorerSearchResults containing list of ExplorerFlightOption objects

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If dates are invalid

    Example:
        >>> from datetime import date, timedelta
        >>> from flight_hunter import PointsYeahClient, explore_flights, LocationFilter
        >>>
        >>> with PointsYeahClient("user@example.com", "password") as client:
        ...     results = explore_flights(
        ...         client=client,
        ...         departure=LocationFilter(airports=["JFK"]),
        ...         arrival=LocationFilter(regions=["WEU"]),
        ...         start_date=date.today() + timedelta(days=7),
        ...         end_date=date.today() + timedelta(days=14),
        ...     )
        ...     for flight in results.flights:
        ...         print(f"{flight.destination.code}: {flight.miles:,} miles "
        ...               f"(updated {flight.updated_ago})")
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    days_range = (end_date - start_date).days
    if days_range > 90:
        logger.warning(f"Date range of {days_range} days is large; results may be limited")

    logger.info(
        f"Explorer search: {departure.summary()} → {arrival.summary()} "
        f"({start_date} to {end_date})"
    )

    all_flights: list[ExplorerFlightOption] = []
    page = 1
    page_size = 100
    total_available = 0

    while len(all_flights) < max_results:
        payload = _build_explorer_payload(
            departure=departure,
            arrival=arrival,
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
            banks=banks,
            programs=programs,
            seats=seats,
            weekend_only=weekend_only,
            sort=sort,
            page=page,
            page_size=page_size,
        )

        response = client.post(EXPLORER_SEARCH_ENDPOINT, json_data=payload)

        if not response.get("results"):
            if page == 1:
                logger.info("No flights found matching criteria")
            break

        results = response.get("results", [])
        total_val = response.get("total")
        total_available = total_val if total_val is not None else 0

        for r in results:
            if len(all_flights) >= max_results:
                break
            all_flights.append(_parse_explorer_result(r))

        logger.debug(
            f"Page {page}: fetched {len(results)} results "
            f"(total so far: {len(all_flights)}, available: {total_available})"
        )

        # Stop if we've fetched all available results
        if total_available and len(all_flights) >= total_available:
            break

        # Stop if not fetching all pages
        if not fetch_all:
            break

        # Stop if no more results (empty page)
        if len(results) == 0:
            break

        page += 1

    logger.info(f"Found {len(all_flights)} flights (total available: {total_available})")

    return ExplorerSearchResults(
        flights=all_flights,
        departure=departure,
        arrival=arrival,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_available=total_available,
    )


def explore_flights_aggregate(
    client: PointsYeahClient,
    departure: LocationFilter,
    arrival: LocationFilter,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
    **kwargs,
) -> dict[str, ExplorerFlightOption]:
    """Get best flight per destination airport (for map/summary views).

    This uses the aggregate endpoint which groups results by arrival airport,
    returning only the best option for each destination.

    Args:
        client: Authenticated PointsYeahClient instance
        departure: Origin location filter
        arrival: Destination location filter
        start_date: Start date for the search range
        end_date: End date for the search range
        cabins: List of cabin classes to include
        **kwargs: Additional arguments passed to payload builder

    Returns:
        Dictionary mapping destination airport codes to ExplorerFlightOption

    Example:
        >>> results = explore_flights_aggregate(
        ...     client, departure, arrival, start_date, end_date
        ... )
        >>> for airport, flight in results.items():
        ...     print(f"{airport}: {flight.miles:,} miles")
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    logger.info(
        f"Explorer aggregate search: {departure.summary()} → {arrival.summary()}"
    )

    payload = _build_explorer_payload(
        departure=departure,
        arrival=arrival,
        start_date=start_date,
        end_date=end_date,
        cabins=cabins,
        page=1,
        page_size=9999,  # Get all results in one request
        group_by="arrival_airport",
        **kwargs,
    )

    response = client.post(EXPLORER_AGGREGATE_ENDPOINT, json_data=payload)

    results: dict[str, ExplorerFlightOption] = {}
    for r in response.get("results", []):
        flight = _parse_explorer_result(r)
        if flight.destination.code:
            results[flight.destination.code] = flight

    logger.info(f"Found {len(results)} destinations")
    return results


def get_filter_ranges(
    client: PointsYeahClient,
    departure: LocationFilter,
    arrival: LocationFilter,
    start_date: date,
    end_date: date,
) -> dict[str, int | float]:
    """Get min/max values for search filters.

    Useful for displaying filter ranges in UI or validating user input.

    Args:
        client: Authenticated PointsYeahClient instance
        departure: Origin location filter
        arrival: Destination location filter
        start_date: Start date for the search range
        end_date: End date for the search range

    Returns:
        Dictionary with keys: min_points, max_points, min_tax, max_tax,
        min_duration, max_duration

    Example:
        >>> ranges = get_filter_ranges(client, departure, arrival, start, end)
        >>> print(f"Points range: {ranges['min_points']} - {ranges['max_points']}")
    """
    payload = {
        "departure": departure.to_api_dict(),
        "arrival": arrival.to_api_dict(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    response = client.post(EXPLORER_FILTER_RANGE_ENDPOINT, json_data=payload)

    return {
        "min_points": response.get("min_points", 0),
        "max_points": response.get("max_points", 0),
        "min_tax": response.get("min_tax", 0),
        "max_tax": response.get("max_tax", 0),
        "min_duration": response.get("min_duration", 0),
        "max_duration": response.get("max_duration", 0),
    }


def explore_flights_simple(
    username: str,
    password: str,
    departure: LocationFilter,
    arrival: LocationFilter,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
) -> list[ExplorerFlightOption]:
    """Simple convenience function to search explorer flights.

    Creates a client, authenticates, and searches in one call.

    Args:
        username: PointsYeah account email
        password: PointsYeah account password
        departure: Origin location filter
        arrival: Destination location filter
        start_date: Start date for the search range
        end_date: End date for the search range
        cabins: List of cabin classes to include

    Returns:
        List of ExplorerFlightOption objects

    Example:
        >>> from datetime import date, timedelta
        >>> from flight_hunter import explore_flights_simple, LocationFilter
        >>>
        >>> flights = explore_flights_simple(
        ...     "user@example.com", "password",
        ...     departure=LocationFilter(airports=["JFK"]),
        ...     arrival=LocationFilter(regions=["WEU"]),
        ...     start_date=date.today() + timedelta(days=7),
        ...     end_date=date.today() + timedelta(days=14),
        ... )
    """
    with PointsYeahClient(username, password) as client:
        results = explore_flights(
            client=client,
            departure=departure,
            arrival=arrival,
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
        )
        return results.flights
