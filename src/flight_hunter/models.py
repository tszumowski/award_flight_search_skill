"""Data models for flight search results."""

from datetime import datetime
from pydantic import BaseModel, Field


# Mapping of airline codes to their frequent flyer program names
PROGRAM_NAMES: dict[str, str] = {
    "AA": "American Airlines AAdvantage",
    "AC": "Air Canada Aeroplan",
    "AF": "Air France-KLM Flying Blue",
    "AM": "Aeromexico Club Premier",
    "AR": "Aerolineas Argentinas Plus",
    "AS": "Alaska Airlines Mileage Plan",
    "AV": "Avianca LifeMiles",
    "AY": "Finnair Plus",
    "B6": "JetBlue TrueBlue",
    "BA": "British Airways Executive Club",
    "CX": "Cathay Pacific Asia Miles",
    "DL": "Delta SkyMiles",
    "EK": "Emirates Skywards",
    "EY": "Etihad Guest",
    "IB": "Iberia Plus",
    "JL": "Japan Airlines Mileage Bank",
    "KE": "Korean Air SKYPASS",
    "KL": "Air France-KLM Flying Blue",
    "LH": "Lufthansa Miles & More",
    "NH": "ANA Mileage Club",
    "NK": "Spirit Free Spirit",
    "QF": "Qantas Frequent Flyer",
    "QR": "Qatar Airways Privilege Club",
    "SK": "SAS EuroBonus",
    "SQ": "Singapore Airlines KrisFlyer",
    "TK": "Turkish Airlines Miles&Smiles",
    "UA": "United MileagePlus",
    "VA": "Virgin Australia Velocity",
    "VS": "Virgin Atlantic Flying Club",
    "WN": "Southwest Rapid Rewards",
}


# Programs and banks sent in API payloads (matches what the PointsYeah website sends)
ALL_PROGRAMS = ["AR","AM","AC","KL","AS","AA","AV","DL","EK","EY","AY","B6","LH","QF","SK","SQ","NK","TK","UA","VS","VA"]
ALL_BANKS = ["Amex", "Bilt", "Capital One", "Chase", "Citi", "WF"]


def get_program_name(code: str) -> str:
    """Get the full program name from airline code."""
    return PROGRAM_NAMES.get(code, code)


class Airport(BaseModel):
    """Airport information."""

    code: str
    city: str
    country_name: str


class TransferProgram(BaseModel):
    """Points transfer program information."""

    bank: str
    code: str
    bonus_percentage: float = 0


class FlightOption(BaseModel):
    """A single flight option from the search results."""

    date: str = Field(description="Flight date in YYYY-MM-DD format")
    stops: int = Field(description="Number of stops (0 for non-stop)")
    departure_time: str | None = Field(
        default=None, description="Departure time in HH:MM format"
    )
    arrival_time: str | None = Field(
        default=None, description="Arrival time in HH:MM format"
    )
    duration_minutes: int = Field(description="Total flight duration in minutes")
    miles: int = Field(description="Points/miles required")
    tax: float = Field(description="Additional taxes and fees in USD")
    cabin: str = Field(description="Cabin class (Economy, Business, First, etc.)")
    carrier: str = Field(description="Airline program code (e.g., DL, UA, AA)")
    origin: Airport = Field(description="Departure airport")
    destination: Airport = Field(description="Arrival airport")
    seats_available: int | None = Field(
        default=None, description="Number of seats available"
    )
    transfer_programs: list[TransferProgram] = Field(
        default_factory=list,
        description="Credit card/bank programs that can transfer to this airline",
    )
    detail_url: str | None = Field(
        default=None, description="URL to detailed flight information"
    )

    @property
    def duration_formatted(self) -> str:
        """Return duration as 'Xh Ym' format."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def transfer_program_names(self) -> list[str]:
        """Return list of transfer program names (credit card programs)."""
        return [p.bank for p in self.transfer_programs]

    @property
    def program_name(self) -> str:
        """Return the full airline loyalty program name (miles currency needed)."""
        return get_program_name(self.carrier)


class SearchResults(BaseModel):
    """Container for flight search results."""

    flights: list[FlightOption] = Field(default_factory=list)
    origin_code: str
    destination_code: str
    start_date: str
    end_date: str

    @property
    def count(self) -> int:
        """Return number of flight options."""
        return len(self.flights)


# =============================================================================
# Explorer Models (for cached/pre-crawled data with region support)
# =============================================================================


class LocationFilter(BaseModel):
    """Flexible location filter supporting multiple location types.

    Used for explorer searches that can filter by airports, regions,
    countries, continents, or US/Canada states.
    """

    airports: list[str] = Field(
        default_factory=list, description="Airport codes (e.g., JFK, LAX)"
    )
    regions: list[str] = Field(
        default_factory=list,
        description="Region codes (e.g., WEU for Western Europe, CAR for Caribbean)",
    )
    countries: list[str] = Field(
        default_factory=list, description="Country codes (e.g., US, FR, JP)"
    )
    continents: list[str] = Field(
        default_factory=list, description="Continent codes (e.g., EU, NA, AS)"
    )
    states: list[str] = Field(
        default_factory=list,
        description="US/Canada state codes (e.g., CA, NY, TX, BC, ON)",
    )

    def to_api_dict(self) -> dict:
        """Convert to API request format."""
        return {
            "airports": self.airports,
            "continents": self.continents,
            "countries": self.countries,
            "regions": self.regions,
            "states": self.states,
        }

    def is_empty(self) -> bool:
        """Check if no location filters are set."""
        return not any(
            [self.airports, self.regions, self.countries, self.continents, self.states]
        )

    def summary(self) -> str:
        """Return a human-readable summary of the location filter."""
        parts = []
        if self.airports:
            parts.append(f"airports: {', '.join(self.airports)}")
        if self.regions:
            parts.append(f"regions: {', '.join(self.regions)}")
        if self.countries:
            parts.append(f"countries: {', '.join(self.countries)}")
        if self.continents:
            parts.append(f"continents: {', '.join(self.continents)}")
        if self.states:
            parts.append(f"states: {', '.join(self.states)}")
        return "; ".join(parts) if parts else "any"


class ExplorerFlightOption(FlightOption):
    """Flight option with explorer-specific fields.

    Extends FlightOption with data freshness timestamps and additional
    metadata from the explorer/cached search results.
    """

    created_at: int | None = Field(
        default=None, description="Unix timestamp (ms) when data was first crawled"
    )
    updated_at: int | None = Field(
        default=None, description="Unix timestamp (ms) when data was last updated"
    )
    image_url: str | None = Field(
        default=None, description="City/destination image URL"
    )
    latitude: float | None = Field(
        default=None, description="Destination latitude"
    )
    longitude: float | None = Field(
        default=None, description="Destination longitude"
    )
    premium_cabin_percentage: int = Field(
        default=0, description="Percentage of flight in premium cabin"
    )

    @property
    def updated_at_datetime(self) -> datetime | None:
        """Convert updated_at timestamp to datetime object."""
        if self.updated_at is None:
            return None
        return datetime.fromtimestamp(self.updated_at / 1000)

    @property
    def updated_at_iso(self) -> str | None:
        """Return updated_at as ISO format string for CSV export."""
        dt = self.updated_at_datetime
        if dt is None:
            return None
        return dt.isoformat()

    @property
    def updated_ago(self) -> str:
        """Return human-readable time since last update.

        Returns strings like "14 hours ago", "2 days ago", "a day ago".
        """
        if self.updated_at is None:
            return "unknown"

        now = datetime.now()
        updated = self.updated_at_datetime
        if updated is None:
            return "unknown"

        delta = now - updated
        total_seconds = delta.total_seconds()

        if total_seconds < 0:
            return "just now"

        minutes = int(total_seconds / 60)
        hours = int(total_seconds / 3600)
        days = int(total_seconds / 86400)

        if minutes < 1:
            return "just now"
        elif minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif hours < 24:
            if hours == 1:
                return "an hour ago"
            return f"{hours} hours ago"
        elif days == 1:
            return "a day ago"
        elif days < 7:
            return f"{days} days ago"
        elif days < 14:
            return "a week ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} weeks ago"
        else:
            months = days // 30
            if months == 1:
                return "a month ago"
            return f"{months} months ago"


class ExplorerSearchResults(BaseModel):
    """Container for explorer search results.

    Unlike SearchResults, this uses LocationFilter for flexible
    origin/destination specification and includes total_available count.
    """

    flights: list[ExplorerFlightOption] = Field(default_factory=list)
    departure: LocationFilter = Field(default_factory=LocationFilter)
    arrival: LocationFilter = Field(default_factory=LocationFilter)
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    total_available: int | None = Field(
        default=0, description="Total results available from API"
    )

    @property
    def count(self) -> int:
        """Return number of flight options fetched."""
        return len(self.flights)
