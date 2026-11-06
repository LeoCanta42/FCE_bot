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
    """Verify favicon route returns valid icon."""
    resp = client.get("/favicon.ico")
    assert resp.status_code == 200
    assert any(t in resp.headers["content-type"] for t in ("image/x-icon", "image/png", "image/svg+xml"))


def test_pwa_manifest_and_sw():
    """Verify PWA manifest and service worker routes."""
    # Manifest prioritizing SVG vector icon
    resp_m = client.get("/manifest.webmanifest")
    assert resp_m.status_code == 200
    m_data = resp_m.json()
    assert m_data["name"] == "Ferrovia Circumetnea & Metro"
    assert m_data["display"] == "standalone"
    assert m_data["icons"][0]["src"] == "/static/icons/icon.svg"
    assert "svg" in m_data["icons"][0]["type"]
    assert len(m_data["icons"]) >= 3

    # Service Worker
    resp_sw = client.get("/sw.js")
    assert resp_sw.status_code == 200
    assert "javascript" in resp_sw.headers["content-type"]
    assert "CACHE_NAME" in resp_sw.text
    assert resp_sw.headers.get("service-worker-allowed") == "/"

    # Static Icon
    resp_icon = client.get("/static/icons/icon.svg")
    assert resp_icon.status_code == 200
    assert "svg" in resp_icon.headers["content-type"]


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


def test_gdpr_user_erasure_and_manual_opt_in():
    """Verify GDPR right to erasure (Art. 17) and explicit news opt-in in UsersRepository."""
    from fce_bot.data.users_repo import UsersRepository
    repo = UsersRepository()
    test_chat_id = 999888777

    # 1. Normal interaction: user must NOT be automatically subscribed to news broadcasts
    repo.register_or_update(chat_id=test_chat_id)
    assert repo.is_user_subscribed(test_chat_id) is False
    subscribed = repo.get_subscribed_chat_ids()
    assert str(test_chat_id) not in subscribed

    # 2. Explicit manual opt-in via button: user is subscribed
    repo.subscribe_user(chat_id=test_chat_id, username="tester")
    assert repo.is_user_subscribed(test_chat_id) is True
    assert str(test_chat_id) in repo.get_subscribed_chat_ids()

    # 3. Explicit manual opt-out via button
    repo.unsubscribe_user(chat_id=test_chat_id)
    assert repo.is_user_subscribed(test_chat_id) is False
    assert str(test_chat_id) not in repo.get_subscribed_chat_ids()

    # 4. Erase user (Right to Erasure)
    deleted = repo.delete_user(test_chat_id)
    assert deleted is True


def test_admin_security_by_default():
    """Verify that unconfigured admin list securely rejects unauthorized users."""
    from fce_bot.bot.handlers.admin import is_admin
    # When admin_user_ids is empty, any random ID must be rejected
    assert is_admin(123456789) is False
