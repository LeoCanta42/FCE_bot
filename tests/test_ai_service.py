"""Unit tests for AI trip planning assistant and entity extractor."""

import pytest
from fce_bot.core.models import TransportType
from fce_bot.services.ai_service import ai_service


def test_extract_entities_standard_format():
    """Verify origin, destination, and time extraction."""
    text = "Come posso andare da Paterno a Randazzo alle 14:30 in treno?"
    origin, dest, time_val, ttype = ai_service.extract_entities(text)
    assert origin.upper() == "PATERNO"
    assert dest.upper() == "RANDAZZO"
    assert time_val == "14:30"
    assert ttype == TransportType.TRENO


def test_extract_entities_metro():
    """Verify metro query extraction."""
    text = "C'è la metro da Monte Po a Borgo alle 9?"
    origin, dest, time_val, ttype = ai_service.extract_entities(text)
    assert "MONTE PO" in origin.upper()
    assert "BORGO" in dest.upper()
    assert time_val == "09:00"
    assert ttype == TransportType.METRO


def test_ai_answer_query():
    """Verify answer generation with factual itineraries."""
    text = "Da Paterno a Randazzo alle 08:30"
    resp = ai_service.answer_query(text)
    assert resp.origin is not None
    assert resp.destination is not None
    assert resp.itineraries_count > 0
    assert "randazzo" in resp.answer.lower()


def test_ai_ticket_query():
    """Verify ticket purchase inquiry returns clean text without markdown link artifacts."""
    resp = ai_service.answer_query("Dove posso acquistare i biglietti FCE?")
    assert len(resp.answer) > 20
    # Should not contain raw markdown link brackets like [Orari Metro](http...)
    assert "](" not in resp.answer
    assert any(w in resp.answer.lower() for w in ["bigliett", "titoli di viaggio", "acquist"])


def test_ai_documents_clean_answer():
    """Verify document request advises consulting official schedules without dumping raw URLs."""
    resp = ai_service.answer_query("Vorrei scaricare la tabella PDF degli orari")
    assert "](" not in resp.answer
    assert "orari" in resp.answer.lower()


def test_ai_arrival_query_paterno_adrano():
    """Verify natural language query asking to arrive by a specific time."""
    query = "Trovami una soluzione che mi faccia arrivare da Paterno ad Adrano per le 15"
    resp = ai_service.answer_query(query)
    assert resp.origin is not None and "paterno" in resp.origin.lower()
    assert resp.destination is not None and "adrano" in resp.destination.lower()
    assert resp.time == "15:00"
    assert resp.itineraries_count > 0
    assert any(hour in resp.answer for hour in ["14:", "14.5", "14.1", "14.2"])
