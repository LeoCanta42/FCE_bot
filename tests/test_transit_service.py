"""Unit tests for transit search and timetable calculation service."""

import pytest
from fce_bot.core.models import TransportType, FilterType
from fce_bot.services.transit_service import transit_service


def test_search_stops():
    """Verify stop search returns matching records."""
    stops = transit_service.search_stops("Milo")
    assert len(stops) > 0
    assert any("MILO" in s.stop_name.upper() for s in stops)


def test_get_stops_by_type():
    """Verify retrieval of stops filtered by transport mode."""
    metro_stops = transit_service.get_stops_by_type(TransportType.METRO)
    assert len(metro_stops) >= 10
    names = [s.stop_name for s in metro_stops]
    assert "MONTE PO" in names
    assert "BORGO" in names


def test_direct_train_trip():
    """Verify finding direct train trips between Paternò and Randazzo."""
    trips = transit_service.find_trips(
        origin="PATERNO'",
        destination="RANDAZZO",
        target_time="08:00",
        transport_type=TransportType.TRENO,
        filter_type=FilterType.DEPARTURE_AFTER
    )
    assert len(trips) > 0
    first = trips[0]
    assert first.is_direct is True
    assert first.departure_time >= "08:00"
    assert first.duration_minutes > 0


def test_metro_trip():
    """Verify finding metro trips between Monte Po and Borgo."""
    trips = transit_service.find_trips(
        origin="MONTE PO",
        destination="BORGO",
        target_time="09:00",
        transport_type=TransportType.METRO
    )
    assert len(trips) > 0
    assert trips[0].segments[0].transport_type == TransportType.METRO


def test_unresolvable_stop_returns_empty():
    """Verify query with nonexistent stop name handles gracefully."""
    trips = transit_service.find_trips(
        origin="NON_EXISTENT_STATION_XYZ",
        destination="RANDAZZO",
        target_time="10:00"
    )
    assert trips == []


def test_metro_does_not_return_train_trips():
    """Verify that searching train stations with METRO transport type returns no trips."""
    trips = transit_service.find_trips(
        origin="PATERNO'",
        destination="RANDAZZO",
        target_time="08:00",
        transport_type=TransportType.METRO
    )
    assert trips == []


def test_transport_type_from_str():
    """Verify string parsing of transport modes."""
    assert TransportType.from_str("METRO") == TransportType.METRO
    assert TransportType.from_str("Metropolitana") == TransportType.METRO
    assert TransportType.from_str("TRENO") == TransportType.TRENO
    assert TransportType.from_str("TR") == TransportType.TRENO
    assert TransportType.from_str("BUS") == TransportType.BUS
    assert TransportType.from_str("QUALSIASI") == TransportType.QUALSIASI
