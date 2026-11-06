"""Circumetnea official PDF timetable documents scraper and resolver."""

import logging
import requests
from bs4 import BeautifulSoup
from fce_bot.config import settings
from fce_bot.core.models import DocumentsInfo

logger = logging.getLogger(__name__)

# Fallback known links in case website scraping is temporarily unreachable
DEFAULT_METRO_URL = "https://www.circumetnea.it/download/orario-metro/?wpdmdl=18207"
DEFAULT_TRAIN_URL = "https://www.circumetnea.it/download/orario-treni-in-vigore-dal-16-marzo-2026/?wpdmdl=17850"
DEFAULT_BUS_URL = "https://www.circumetnea.it/download/orario-autolinee-in-vigore-dal-5-ottobre-2026/?wpdmdl=18300"


class DocumentsService:
    """Finds direct download URLs for official PDF schedules on circumetnea.it."""

    def __init__(self, base_url: str = None):
        self.url = base_url or settings.CIRCUMETNEA_LINES_URL
        self.headers = {
            "User-Agent": "FCE-Bot/2.0 (+https://github.com/Leonardo0101/FCE_bot)"
        }

    def get_documents(self) -> DocumentsInfo:
        """Fetch current document download URLs from 'le nostre linee' page."""
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            metro_url = None
            train_url = None
            bus_url = None

            # Look through all download links and headings
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = (a.get_text() or "").lower()
                href_lower = href.lower()

                if "download" in href_lower or ".pdf" in href_lower:
                    if "metro" in href_lower or "metro" in text:
                        if not metro_url:
                            metro_url = href
                    elif "tren" in href_lower or "ferrovia" in text or "tren" in text:
                        if not train_url:
                            train_url = href
                    elif "autolinee" in href_lower or "bus" in href_lower or "autolinee" in text:
                        if not bus_url:
                            bus_url = href

            return DocumentsInfo(
                metro_url=metro_url or DEFAULT_METRO_URL,
                train_url=train_url or DEFAULT_TRAIN_URL,
                bus_url=bus_url or DEFAULT_BUS_URL,
            )
        except Exception as e:
            logger.warning("Failed to scrape documents page (%s), using defaults", e)
            return DocumentsInfo(
                metro_url=DEFAULT_METRO_URL,
                train_url=DEFAULT_TRAIN_URL,
                bus_url=DEFAULT_BUS_URL
            )


documents_service = DocumentsService()
