"""Unit tests for news service and document scrapers."""

import pytest
from fce_bot.services.news_service import news_service, clean_html
from fce_bot.services.documents_service import documents_service


def test_clean_html():
    """Verify HTML tag stripping."""
    raw = "<p>Test <strong>bold</strong> text</p>"
    cleaned = clean_html(raw)
    assert cleaned == "Test bold text"


def test_documents_urls():
    """Verify official PDF documents resolver returns valid circumetnea links."""
    docs = documents_service.get_documents()
    assert "circumetnea.it" in docs.metro_url
    assert "circumetnea.it" in docs.train_url
    assert "circumetnea.it" in docs.bus_url
