"""Circumetnea official news service (RSS feed parser and notification detector)."""

import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

from fce_bot.config import settings
from fce_bot.core.models import NewsItem
from fce_bot.data.db import get_db

logger = logging.getLogger(__name__)


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and clean up whitespace."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class NewsService:
    """Manages fetching, caching, and broadcasting Circumetnea news."""

    def __init__(self, db_path=None, rss_url=None):
        self.db_path = db_path
        self.rss_url = rss_url or settings.CIRCUMETNEA_RSS_URL
        self.headers = {
            "User-Agent": "FCE-Bot/2.0 (+https://github.com/Leonardo0101/FCE_bot)"
        }

    def fetch_news(self, limit: int = 10) -> List[NewsItem]:
        """Fetch latest news items from RSS feed, falling back to HTML scraping if needed."""
        try:
            return self._fetch_from_rss(limit)
        except Exception as e:
            logger.warning("RSS fetch failed (%s), falling back to web scraping", e)
            try:
                return self._fetch_from_web(limit)
            except Exception as e_web:
                logger.error("Web scraping news fallback also failed: %s", e_web)
                return []

    def _fetch_from_rss(self, limit: int = 10) -> List[NewsItem]:
        """Parse the official Circumetnea WordPress RSS feed."""
        resp = requests.get(self.rss_url, headers=self.headers, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        items = channel.findall("item")
        results: List[NewsItem] = []

        for it in items[:limit]:
            title = it.findtext("title") or "Avviso Circumetnea"
            link = it.findtext("link") or ""
            pub_date = it.findtext("pubDate") or ""
            desc = it.findtext("description") or ""
            guid = it.findtext("guid") or link

            results.append(NewsItem(
                title=clean_html(title),
                link=link.strip(),
                published_date=pub_date.strip(),
                summary=clean_html(desc),
                guid=guid.strip()
            ))

        return results

    def _fetch_from_web(self, limit: int = 10) -> List[NewsItem]:
        """Fallback scraper from https://www.circumetnea.it/category/news/."""
        url = "https://www.circumetnea.it/category/news/"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.find_all("article")
        results: List[NewsItem] = []

        for art in articles[:limit]:
            title_tag = art.find(["h2", "h3", "h4", "h5"])
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            a_tag = art.find("a", href=True)
            link = a_tag["href"] if a_tag else url

            date_tag = art.find(class_=re.compile("date|time|published", re.I))
            pub_date = date_tag.get_text(strip=True) if date_tag else None

            desc_tag = art.find(class_=re.compile("excerpt|content|entry-summary", re.I))
            summary = desc_tag.get_text(strip=True) if desc_tag else None

            results.append(NewsItem(
                title=title,
                link=link,
                published_date=pub_date,
                summary=summary,
                guid=link
            ))

        return results

    def check_for_new_articles(self) -> List[NewsItem]:
        """Fetch current news, compare against SQLite cache, insert and return unnotified items."""
        fetched = self.fetch_news(limit=10)
        if not fetched:
            return []

        new_items: List[NewsItem] = []

        with get_db(self.db_path) as conn:
            cur = conn.cursor()

            # Check if this is the very first run (empty cache)
            count = cur.execute("SELECT count(*) as cnt FROM news_cache").fetchone()["cnt"]
            if count == 0:
                # Seed cache so we don't spam all historical news on initial setup
                logger.info("Initializing news cache with current %d articles", len(fetched))
                for item in fetched:
                    cur.execute("""
                        INSERT OR IGNORE INTO news_cache (guid, title, link, pub_date)
                        VALUES (?, ?, ?, ?)
                    """, (item.guid or item.link, item.title, item.link, item.published_date))
                return []

            for item in fetched:
                guid = item.guid or item.link
                exists = cur.execute("SELECT 1 FROM news_cache WHERE guid = ?", (guid,)).fetchone()
                if not exists:
                    cur.execute("""
                        INSERT INTO news_cache (guid, title, link, pub_date)
                        VALUES (?, ?, ?, ?)
                    """, (guid, item.title, item.link, item.published_date))
                    new_items.append(item)

        if new_items:
            logger.info("Discovered %d new Circumetnea news articles!", len(new_items))
        return new_items


news_service = NewsService()
