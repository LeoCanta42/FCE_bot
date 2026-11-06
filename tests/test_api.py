"""Integration tests for FastAPI endpoints."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from starlette.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fce-bot"


def test_home_page():
    """Verify HTML home dashboard loads."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Circumetnea" in resp.text


def test_favicon():
    """Verify favicon route returns 204."""
    resp = client.get("/favicon.ico")
    assert resp.status_code == 204


def test_api_stops():
    """Verify stops API endpoint."""
    resp = client.get("/api/stops?query=Milo")
    assert resp.status_code == 200
    stops = resp.json()
    assert len(stops) > 0
    assert any("MILO" in s["name"].upper() for s in stops)


def test_api_stops_type_filtering():
    """Verify stops API filtered by transport mode."""
    resp = client.get("/api/stops?type=METRO&limit=100")
    assert resp.status_code == 200
    stops = resp.json()
    assert len(stops) == 12
    assert all(s["metro"] is True for s in stops)


def test_api_timetable():
    """Verify timetable lookup API endpoint."""
    resp = client.get("/api/timetable?origin=PATERNO'&destination=RANDAZZO&time=08:00")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    assert len(data["itineraries"]) > 0


def test_api_timetable_mode_filtering():
    """Verify transport mode strict filtering in timetable queries."""
    # Searching train route under METRO must return 0 results
    resp_metro_err = client.get("/api/timetable?origin=PATERNO'&destination=RANDAZZO&transport=METRO")
    assert resp_metro_err.status_code == 200
    assert resp_metro_err.json()["count"] == 0

    # Searching train route under TRENO must return train results
    resp_train = client.get("/api/timetable?origin=PATERNO'&destination=RANDAZZO&transport=TRENO")
    assert resp_train.status_code == 200
    train_data = resp_train.json()
    assert train_data["count"] > 0
    for it in train_data["itineraries"]:
        for seg in it["segments"]:
            assert seg["type"] == "TRENO"

    # Searching metro route under METRO must return metro results
    resp_metro = client.get("/api/timetable?origin=MONTE PO&destination=STESICORO&transport=METRO")
    assert resp_metro.status_code == 200
    metro_data = resp_metro.json()
    assert metro_data["count"] > 0
    for it in metro_data["itineraries"]:
        for seg in it["segments"]:
            assert seg["type"] == "METRO"


def test_api_documents():
    """Verify documents API endpoint."""
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "metro_url" in data
    assert "train_url" in data
    assert "bus_url" in data


def test_api_ai_ask():
    """Verify AI trip assistant API endpoint."""
    resp = client.post("/api/ai/ask", json={"question": "Da Paterno a Randazzo alle 08:30"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["itineraries_count"] > 0
