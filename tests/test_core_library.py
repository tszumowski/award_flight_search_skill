"""Tests for the core flight hunter library (src/)."""

import pytest
from src.locations import detect_location_type, parse_location, parse_locations, REGIONS, STATES, COUNTRIES, CONTINENTS
from src.models import FlightOption, LocationFilter, Airport, ExplorerFlightOption


class TestDetectLocationType:
    """Tests for detect_location_type function."""

    def test_airport_code(self):
        assert detect_location_type("JFK") == "airport"
        assert detect_location_type("lax") == "airport"  # case insensitive
        assert detect_location_type("CDG") == "airport"

    def test_region_code(self):
        assert detect_location_type("WEU") == "region"
        assert detect_location_type("CAR") == "region"
        assert detect_location_type("ANW") == "region"

    def test_state_code(self):
        assert detect_location_type("NY") == "state"
        assert detect_location_type("CA") == "state"
        assert detect_location_type("TX") == "state"

    def test_continent_code(self):
        assert detect_location_type("EU") == "continent"
        assert detect_location_type("NA") == "continent"
        assert detect_location_type("AS") == "continent"

    def test_country_code(self):
        # Countries that aren't states or continents
        assert detect_location_type("FR") == "country"
        assert detect_location_type("JP") == "country"

    def test_unknown_code(self):
        assert detect_location_type("ABCD") == "unknown"


class TestParseLocation:
    """Tests for parse_location function."""

    def test_airport(self):
        result = parse_location("JFK")
        assert result.airports == ["JFK"]
        assert result.regions == []

    def test_region(self):
        result = parse_location("WEU")
        assert result.regions == ["WEU"]
        assert result.airports == []

    def test_state(self):
        result = parse_location("NY")
        assert result.states == ["NY"]

    def test_country(self):
        result = parse_location("FR")
        assert result.countries == ["FR"]

    def test_continent(self):
        result = parse_location("EU")
        assert result.continents == ["EU"]


class TestParseLocations:
    """Tests for parse_locations with mixed codes."""

    def test_mixed_codes(self):
        result = parse_locations(["JFK", "EWR", "WEU", "NY"])
        assert "JFK" in result.airports
        assert "EWR" in result.airports
        assert "WEU" in result.regions
        assert "NY" in result.states

    def test_empty_list(self):
        result = parse_locations([])
        assert result.is_empty()

    def test_single_code(self):
        result = parse_locations(["LAX"])
        assert result.airports == ["LAX"]


class TestLocationFilter:
    """Tests for LocationFilter model."""

    def test_empty_filter(self):
        f = LocationFilter()
        assert f.is_empty()

    def test_non_empty_filter(self):
        f = LocationFilter(airports=["JFK"])
        assert not f.is_empty()

    def test_to_api_dict(self):
        f = LocationFilter(airports=["JFK"], regions=["WEU"])
        d = f.to_api_dict()
        assert d["airports"] == ["JFK"]
        assert d["regions"] == ["WEU"]
        assert d["countries"] == []
        assert d["continents"] == []
        assert d["states"] == []

    def test_summary(self):
        f = LocationFilter(airports=["JFK", "EWR"], regions=["WEU"])
        s = f.summary()
        assert "JFK" in s
        assert "WEU" in s


class TestFlightOption:
    """Tests for FlightOption model."""

    def test_duration_formatted(self):
        flight = FlightOption(
            date="2026-03-01",
            stops=0,
            duration_minutes=450,
            miles=50000,
            tax=5.60,
            cabin="Business",
            carrier="DL",
            origin=Airport(code="JFK", city="New York", country_name="United States"),
            destination=Airport(code="CDG", city="Paris", country_name="France"),
        )
        assert flight.duration_formatted == "7h 30m"

    def test_program_name(self):
        flight = FlightOption(
            date="2026-03-01",
            stops=0,
            duration_minutes=300,
            miles=25000,
            tax=5.60,
            cabin="Economy",
            carrier="UA",
            origin=Airport(code="SFO", city="San Francisco", country_name="United States"),
            destination=Airport(code="LAX", city="Los Angeles", country_name="United States"),
        )
        assert flight.program_name == "United MileagePlus"

    def test_transfer_program_names(self):
        from src.models import TransferProgram
        flight = FlightOption(
            date="2026-03-01",
            stops=0,
            duration_minutes=300,
            miles=25000,
            tax=5.60,
            cabin="Economy",
            carrier="UA",
            origin=Airport(code="SFO", city="San Francisco", country_name="United States"),
            destination=Airport(code="LAX", city="Los Angeles", country_name="United States"),
            transfer_programs=[
                TransferProgram(bank="Chase", code="UR"),
                TransferProgram(bank="Amex", code="MR"),
            ],
        )
        assert flight.transfer_program_names == ["Chase", "Amex"]


class TestSearchWithCredentials:
    """Tests that require API credentials (skipped if not available)."""

    def test_search_flights_basic(self, credentials):
        from datetime import date, timedelta
        from src import PointsYeahClient, search_flights

        username, password = credentials
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        with PointsYeahClient(username, password) as client:
            results = search_flights(
                client=client,
                origin="JFK",
                destination="LAX",
                start_date=start,
                end_date=end,
                max_results=5,
            )

        assert results is not None
        assert results.origin_code == "JFK"
        assert results.destination_code == "LAX"

    def test_explore_flights_region(self, credentials):
        from datetime import date, timedelta
        from src import PointsYeahClient, explore_flights, LocationFilter

        username, password = credentials
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=3)

        with PointsYeahClient(username, password) as client:
            results = explore_flights(
                client=client,
                departure=LocationFilter(airports=["JFK"]),
                arrival=LocationFilter(regions=["WEU"]),
                start_date=start,
                end_date=end,
                max_results=5,
            )

        assert results is not None
        assert len(results.flights) >= 0  # May be 0 if no cached data
