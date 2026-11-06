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


def test_news_item_formatting():
    """Verify Italian date formatting and WordPress boilerplate removal."""
    from fce_bot.core.models import NewsItem
    from fce_bot.bot.handlers.news import format_news_digest

    item = NewsItem(
        title="Abbonamenti UNICT FCE-AMTS 2026/2027",
        link="https://www.circumetnea.it/abbonamenti/",
        published_date="Tue, 06 Oct 2026 11:50:06 +0000",
        summary="Gli studenti universitari ... L'articolo Abbonamenti UNICT proviene da Ferrovia Circumetnea ."
    )

    assert item.format_date_italian() == "06 Ottobre 2026"
    assert "proviene da Ferrovia Circumetnea" not in item.get_clean_summary()

    digest = format_news_digest([item])
    assert "1️⃣ *Abbonamenti UNICT FCE-AMTS 2026/2027*" in digest
    assert "06 Ottobre 2026" in digest
