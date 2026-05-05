"""Location constants and utilities for explorer searches.

This module contains region, state, continent, and country codes used
by the PointsYeah explorer API, along with utilities for auto-detecting
location types from user input.
"""

from .models import LocationFilter


# =============================================================================
# Region Codes
# =============================================================================

REGIONS: dict[str, str] = {
    "WEU": "Western Europe",
    "EEU": "Eastern Europe",
    "CAR": "Caribbean",
    "SAM": "South America",
    "CAM": "Central America",
    "NAM": "North America",
    "SEA": "Southeast Asia",
    "NEA": "Northeast Asia",
    "SAS": "South Asia",
    "OCE": "Oceania",
    "AFR": "Africa",
    "MEA": "Middle East",
    "ANW": "Anywhere",  # Special wildcard for any destination
}


# =============================================================================
# Continent Codes
# =============================================================================

CONTINENTS: dict[str, str] = {
    "AF": "Africa",
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America",
}


# =============================================================================
# US State Codes
# =============================================================================

US_STATES: dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "PR": "Puerto Rico",
    "VI": "U.S. Virgin Islands",
    "GU": "Guam",
}


# =============================================================================
# Canadian Province Codes
# =============================================================================

CANADA_PROVINCES: dict[str, str] = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}

# Combined US states and Canadian provinces
STATES: dict[str, str] = {**US_STATES, **CANADA_PROVINCES}


# =============================================================================
# Common Country Codes (ISO 3166-1 alpha-2)
# =============================================================================

# Note: This is a subset of commonly searched countries.
# The API likely accepts any valid ISO country code.
COUNTRIES: dict[str, str] = {
    "US": "United States",
    "CA": "Canada",  # Also a state code - context matters
    "MX": "Mexico",
    "GB": "United Kingdom",
    "FR": "France",
    "DE": "Germany",
    "IT": "Italy",
    "ES": "Spain",
    "PT": "Portugal",
    "NL": "Netherlands",
    "BE": "Belgium",
    "CH": "Switzerland",
    "AT": "Austria",
    "GR": "Greece",
    "JP": "Japan",
    "KR": "South Korea",
    "CN": "China",
    "TW": "Taiwan",
    "HK": "Hong Kong",
    "SG": "Singapore",
    "TH": "Thailand",
    "VN": "Vietnam",
    "PH": "Philippines",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "AU": "Australia",
    "NZ": "New Zealand",
    "BR": "Brazil",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "AE": "United Arab Emirates",
    "IL": "Israel",
    "EG": "Egypt",
    "ZA": "South Africa",
    "IN": "India",
}


# =============================================================================
# Location Type Detection
# =============================================================================


def detect_location_type(code: str) -> str:
    """Detect the type of a location code.

    Args:
        code: A location code (e.g., "JFK", "WEU", "CA", "US")

    Returns:
        One of: "airport", "region", "state", "country", "continent", "unknown"

    Detection priority:
        1. Known region codes (3-letter, in REGIONS dict)
        2. Known continent codes (2-letter, in CONTINENTS dict)
        3. Known state codes (2-letter, in STATES dict)
        4. 3-letter codes assumed to be airports
        5. 2-letter codes assumed to be countries
        6. Unknown
    """
    code = code.upper()

    # Check known region codes first (3-letter)
    if code in REGIONS:
        return "region"

    # Check known continent codes (2-letter)
    if code in CONTINENTS:
        return "continent"

    # Check known state codes (2-letter)
    # Note: Some overlap with countries (e.g., CA = California or Canada)
    # We prioritize states since they're more commonly used in this context
    if code in STATES:
        return "state"

    # 3-letter codes are assumed to be airports
    if len(code) == 3:
        return "airport"

    # 2-letter codes not in states/continents are assumed to be countries
    if len(code) == 2:
        return "country"

    return "unknown"


def parse_location(code: str) -> LocationFilter:
    """Parse a location code into a LocationFilter.

    Auto-detects the location type and creates a LocationFilter
    with the appropriate field populated.

    Args:
        code: A location code (e.g., "JFK", "WEU", "CA", "US")

    Returns:
        LocationFilter with the appropriate field populated

    Example:
        >>> parse_location("JFK")
        LocationFilter(airports=["JFK"])
        >>> parse_location("WEU")
        LocationFilter(regions=["WEU"])
        >>> parse_location("CA")
        LocationFilter(states=["CA"])
    """
    code = code.upper()
    location_type = detect_location_type(code)

    if location_type == "airport":
        return LocationFilter(airports=[code])
    elif location_type == "region":
        return LocationFilter(regions=[code])
    elif location_type == "state":
        return LocationFilter(states=[code])
    elif location_type == "country":
        return LocationFilter(countries=[code])
    elif location_type == "continent":
        return LocationFilter(continents=[code])
    else:
        # Default to treating unknown codes as airports
        return LocationFilter(airports=[code])


def parse_locations(codes: list[str]) -> LocationFilter:
    """Parse multiple location codes into a single LocationFilter.

    Combines multiple location codes into one LocationFilter,
    grouping them by their detected types.

    Args:
        codes: List of location codes

    Returns:
        LocationFilter with all locations grouped by type

    Example:
        >>> parse_locations(["JFK", "EWR", "WEU"])
        LocationFilter(airports=["JFK", "EWR"], regions=["WEU"])
    """
    result = LocationFilter()

    for code in codes:
        code = code.upper()
        location_type = detect_location_type(code)

        if location_type == "airport":
            result.airports.append(code)
        elif location_type == "region":
            result.regions.append(code)
        elif location_type == "state":
            result.states.append(code)
        elif location_type == "country":
            result.countries.append(code)
        elif location_type == "continent":
            result.continents.append(code)
        else:
            # Default to airport for unknown codes
            result.airports.append(code)

    return result


def get_region_name(code: str) -> str:
    """Get the full name of a region code."""
    return REGIONS.get(code.upper(), code)


def get_state_name(code: str) -> str:
    """Get the full name of a state/province code."""
    return STATES.get(code.upper(), code)


def get_country_name(code: str) -> str:
    """Get the full name of a country code."""
    return COUNTRIES.get(code.upper(), code)
