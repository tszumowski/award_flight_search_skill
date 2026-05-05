"""Flight Hunter - PointsYeah flight search library."""

from .client import PointsYeahClient
from .models import (
    FlightOption,
    SearchResults,
    # Explorer models
    ExplorerFlightOption,
    ExplorerSearchResults,
    LocationFilter,
)
from .search import search_flights, search_flights_simple
from .explorer import (
    explore_flights,
    explore_flights_simple,
    explore_flights_aggregate,
    get_filter_ranges,
)
from .locations import (
    REGIONS,
    STATES,
    COUNTRIES,
    CONTINENTS,
    parse_location,
    parse_locations,
    detect_location_type,
)

__all__ = [
    # Client
    "PointsYeahClient",
    # Live search
    "FlightOption",
    "SearchResults",
    "search_flights",
    "search_flights_simple",
    # Explorer search
    "ExplorerFlightOption",
    "ExplorerSearchResults",
    "LocationFilter",
    "explore_flights",
    "explore_flights_simple",
    "explore_flights_aggregate",
    "get_filter_ranges",
    # Location utilities
    "REGIONS",
    "STATES",
    "COUNTRIES",
    "CONTINENTS",
    "parse_location",
    "parse_locations",
    "detect_location_type",
]
