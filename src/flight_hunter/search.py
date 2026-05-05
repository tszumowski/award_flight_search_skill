"""Flight search functionality using PointsYeah API."""

import logging
from datetime import date
from typing import Any

from .client import PointsYeahClient
from .models import ALL_BANKS, ALL_PROGRAMS, Airport, FlightOption, SearchResults, TransferProgram

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT = "/v2/live/explorer/search"

CABIN_ALIASES = {
    "economy": "Economy",
    "y": "Economy",
    "premium economy": "Premium Economy",
    "pe": "Premium Economy",
    "premium": "Premium Economy",
    "premium_economy": "Premium Economy",
    "business": "Business",
    "biz": "Business",
    "j": "Business",
    "c": "Business",
    "d": "Business",
    "i": "Business",
    "first": "First",
    "f": "First",
    "a": "First",
    "p": "First",
}


def _normalize_cabin(cabin: str) -> str:
    """Normalize cabin class name to API-expected Title Case.

    Handles lowercase, uppercase, mixed case, and common abbreviations.

    Args:
        cabin: Cabin class name in any case format

    Returns:
        Normalized cabin name matching API expectations
    """
    key = cabin.strip().lower().replace("_", " ")
    if key in CABIN_ALIASES:
        return CABIN_ALIASES[key]
    # Fallback: title case the input
    return key.title()


def _build_search_payload(
    origin: str,
    destination: str,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """Build the search request payload.

    Args:
        origin: Origin airport code (e.g., "JFK")
        destination: Destination airport code (e.g., "LAX")
        start_date: Start date for the search range
        end_date: End date for the search range
        cabins: List of cabin classes to include (case-insensitive)
        page: Page number for pagination
        page_size: Number of results per page

    Returns:
        Request payload dictionary
    """
    if cabins is None:
        cabins = ["Economy", "Premium Economy", "Business", "First"]
    else:
        cabins = [_normalize_cabin(c) for c in cabins]

    return {
        "departure": {
            "airports": [origin],
            "continents": [],
            "countries": [],
            "regions": [],
            "states": [],
        },
        "arrival": {
            "airports": [destination],
            "continents": [],
            "countries": [],
            "regions": [],
            "states": [],
        },
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "banks": ALL_BANKS,
        "programs": ALL_PROGRAMS,
        "cabins": cabins,
        "premium_cabin_percentage": 0,
        "trip": "",
        "sort": "miles",
        "pagination": {"page": page, "page_size": page_size},
        "seats": 1,
        "weekend_only": False,
        "collection": False,
    }


def _parse_flight_result(result: dict[str, Any]) -> FlightOption:
    """Parse a single flight result from the API response.

    Args:
        result: Raw flight result dictionary from API

    Returns:
        FlightOption model instance
    """
    departure = result.get("departure", {})
    arrival = result.get("arrival", {})

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

    return FlightOption(
        date=result.get("departure_date", ""),
        stops=result.get("stops", 0),
        departure_time=None,  # Not available in search results
        arrival_time=None,  # Not available in search results
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
    )


def search_flights(
    client: PointsYeahClient,
    origin: str,
    destination: str,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
    max_results: int = 100,
    fetch_all: bool = True,
) -> SearchResults:
    """Search for award flights on PointsYeah.

    Args:
        client: Authenticated PointsYeahClient instance
        origin: Origin airport code (e.g., "JFK") or metro code (e.g., "NYC")
        destination: Destination airport code (e.g., "LAX") or metro code
        start_date: Start date for the search range
        end_date: End date for the search range (1-4 days from start recommended)
        cabins: List of cabin classes to include (default: all cabins)
        max_results: Maximum number of results to return
        fetch_all: If True, paginate through all results up to max_results.
                   This ensures all cabin classes are included when searching
                   metro codes (like NYC) that may return hundreds of results.

    Returns:
        SearchResults containing list of FlightOption objects

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If dates are invalid

    Example:
        >>> from datetime import date
        >>> from flight_hunter import PointsYeahClient, search_flights
        >>>
        >>> client = PointsYeahClient("user@example.com", "password")
        >>> results = search_flights(
        ...     client,
        ...     origin="JFK",
        ...     destination="LAX",
        ...     start_date=date(2026, 1, 15),
        ...     end_date=date(2026, 1, 18),
        ... )
        >>> for flight in results.flights:
        ...     print(f"{flight.date}: {flight.miles} miles, {flight.cabin}")
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    days_range = (end_date - start_date).days
    if days_range > 90:
        logger.warning(f"Date range of {days_range} days is large; results may be limited")

    logger.info(f"Searching flights: {origin} → {destination} ({start_date} to {end_date})")

    all_flights: list[FlightOption] = []
    seen_urls: set[str] = set()
    page = 1
    page_size = 100  # Request 100, API may return fewer
    total_available = 0

    while len(all_flights) < max_results:
        payload = _build_search_payload(
            origin=origin.upper(),
            destination=destination.upper(),
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
            page=page,
            page_size=page_size,
        )

        response = client.post(SEARCH_ENDPOINT, json_data=payload)

        if not response.get("results"):
            if page == 1:
                logger.info("No flights found matching criteria")
            break

        results = response.get("results", [])
        total_available = response.get("total", 0)

        new_count = 0
        dup_count = 0
        for r in results:
            if len(all_flights) >= max_results:
                break
            detail_url = r.get("detail_url", "")
            if detail_url in seen_urls:
                dup_count += 1
                continue
            seen_urls.add(detail_url)
            all_flights.append(_parse_flight_result(r))
            new_count += 1

        if dup_count > 0:
            logger.debug(f"Page {page}: {dup_count} duplicates skipped")
        logger.debug(f"Page {page}: fetched {new_count} new results (total so far: {len(all_flights)}, available: {total_available})")

        # Stop if not fetching all pages
        if not fetch_all:
            break

        # Stop if no more results (empty page or all duplicates)
        if len(results) == 0 or new_count == 0:
            break

        page += 1

    logger.info(f"Found {len(all_flights)} unique flights (total available: {total_available})")

    return SearchResults(
        flights=all_flights,
        origin_code=origin.upper(),
        destination_code=destination.upper(),
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )


def search_flights_simple(
    username: str,
    password: str,
    origin: str,
    destination: str,
    start_date: date,
    end_date: date,
    cabins: list[str] | None = None,
) -> list[FlightOption]:
    """Simple convenience function to search for flights.

    Creates a client, authenticates, and searches in one call.

    Args:
        username: PointsYeah account email
        password: PointsYeah account password
        origin: Origin airport code (e.g., "JFK")
        destination: Destination airport code (e.g., "LAX")
        start_date: Start date for the search range
        end_date: End date for the search range

    Returns:
        List of FlightOption objects

    Example:
        >>> from datetime import date
        >>> from flight_hunter import search_flights_simple
        >>>
        >>> flights = search_flights_simple(
        ...     "user@example.com", "password",
        ...     origin="JFK", destination="LAX",
        ...     start_date=date(2026, 1, 15),
        ...     end_date=date(2026, 1, 18),
        ... )
    """
    with PointsYeahClient(username, password) as client:
        results = search_flights(
            client=client,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
        )
        return results.flights
