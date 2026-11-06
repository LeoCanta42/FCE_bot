"""FastAPI REST router for webhooks, Vercel cron, REST transit endpoints and Web UI."""

import logging
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Request, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from telegram import Update

from fce_bot.config import settings
from fce_bot.core.models import TransportType, FilterType, AIQueryRequest, AIQueryResponse, NewsItem, DocumentsInfo
from fce_bot.services.transit_service import transit_service
from fce_bot.services.news_service import news_service
from fce_bot.services.documents_service import documents_service
from fce_bot.services.ai_service import ai_service
from fce_bot.bot.bot_app import create_bot_application
from fce_bot.bot.handlers.news import check_and_broadcast_news
from fce_bot.data.users_repo import UsersRepository

logger = logging.getLogger(__name__)
router = APIRouter()

# Cached Telegram Application instance for serverless invocations
_telegram_app = None


def get_telegram_app():
    global _telegram_app
    if _telegram_app is None:
        _telegram_app = create_bot_application()
    return _telegram_app


# ==========================================
# Telegram Webhook & Cron Endpoints
# ==========================================

@router.post("/api/webhook")
@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """Handle incoming Telegram updates forwarded via Webhook."""
    if settings.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        data = await request.json()
        app = get_telegram_app()
        # Initialize application if not yet running
        if not app.running:
            await app.initialize()

        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error("Error processing telegram webhook: %s", e)
        return JSONResponse(status_code=500, content={"ok": False, "error": "Internal processing error"})


@router.get("/api/cron/news")
@router.get("/cron/news")
async def cron_news_checker(
    authorization: Optional[str] = Header(None),
    secret: Optional[str] = Query(None)
):
    """Scheduled task invoked by Vercel Cron to check news and broadcast updates."""
    if settings.CRON_SECRET:
        token = (authorization or "").replace("Bearer ", "") or secret
        if token != settings.CRON_SECRET:
            raise HTTPException(status_code=403, detail="Invalid cron authorization secret")

    app = get_telegram_app()
    if not app.running:
        await app.initialize()

    sent_count = await check_and_broadcast_news(app.bot)
    return {
        "status": "ok",
        "broadcast_sent": sent_count,
        "message": f"Broadcasted {sent_count} new announcements"
    }


# ==========================================
# REST Transit & AI Endpoints
# ==========================================

@router.get("/api/stops")
async def list_stops(
    query: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50
):
    """Search or list transit stops."""
    ttype = TransportType.from_str(type) if type else None
    if query:
        stops = transit_service.search_stops(query, transport_type=ttype, limit=limit)
    else:
        stops = transit_service.get_stops_by_type(ttype or TransportType.QUALSIASI, limit=limit)
    return [
        {
            "id": s.stop_id,
            "name": s.stop_name,
            "lat": s.lat,
            "lon": s.lon,
            "bus": s.has_bus,
            "train": s.has_train,
            "metro": s.has_metro,
        }
        for s in stops
    ]


@router.get("/api/timetable")
async def get_timetable(
    origin: str,
    destination: str,
    time: str = "08:00",
    transport: Optional[str] = "QUALSIASI",
    filter: Optional[str] = "near_partenza2",
    limit: int = 10
):
    """Query transit timetable between two stops."""
    ttype = TransportType.from_str(transport or "")
    ftype = FilterType(filter) if filter in [e.value for e in FilterType] else FilterType.DEPARTURE_AFTER
    itineraries = transit_service.find_trips(
        origin=origin,
        destination=destination,
        target_time=time,
        transport_type=ttype,
        filter_type=ftype,
        limit=limit
    )
    return {
        "origin": origin,
        "destination": destination,
        "requested_time": time,
        "count": len(itineraries),
        "itineraries": [
            {
                "departure_stop": it.departure_stop,
                "departure_time": it.departure_time,
                "arrival_stop": it.arrival_stop,
                "arrival_time": it.arrival_time,
                "duration_minutes": it.duration_minutes,
                "direct": it.is_direct,
                "segments": [
                    {
                        "type": seg.transport_type.value,
                        "route": seg.route_name,
                        "headsign": seg.headsign,
                        "departure_stop": seg.departure_stop,
                        "departure_time": seg.departure_time,
                        "arrival_stop": seg.arrival_stop,
                        "arrival_time": seg.arrival_time,
                        "duration_minutes": seg.duration_minutes
                    }
                    for seg in it.segments
                ]
            }
            for it in itineraries
        ]
    }


@router.get("/api/news")
async def get_news(limit: int = 10) -> List[NewsItem]:
    """Retrieve latest Circumetnea news."""
    return news_service.fetch_news(limit=limit)


@router.get("/api/documents")
async def get_documents() -> DocumentsInfo:
    """Retrieve official PDF timetable download links."""
    return documents_service.get_documents()


@router.post("/api/ai/ask")
async def ai_trip_advisor(req: AIQueryRequest) -> AIQueryResponse:
    """Natural Language Trip Planning Assistant API."""
    return ai_service.answer_query(req.question)


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "fce-bot",
        "version": "2.0.0"
    }


# ==========================================
# PWA & Static Assets Endpoints
# ==========================================

STATIC_DIR = Path(__file__).resolve().parent / "static"
ICONS_DIR = STATIC_DIR / "icons"
SW_PATH = STATIC_DIR / "sw.js"


@router.get("/manifest.webmanifest", include_in_schema=False)
@router.get("/manifest.json", include_in_schema=False)
async def web_manifest():
    """Serve PWA Web App Manifest prioritizing crisp vector SVG graphics."""
    manifest_data = {
        "name": "Ferrovia Circumetnea & Metro",
        "short_name": "FCE Orari",
        "description": "Orari ufficiali, itinerari e avvisi di servizio per Ferrovia Circumetnea e Metropolitana di Catania",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#991b1b",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            }
        ]
    }
    return JSONResponse(
        content=manifest_data,
        media_type="application/manifest+json"
    )


@router.get("/sw.js", include_in_schema=False)
async def service_worker():
    """Serve PWA Service Worker script at root scope."""
    if SW_PATH.exists():
        content = SW_PATH.read_text(encoding="utf-8")
        return Response(
            content=content,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    raise HTTPException(status_code=404, detail="Service worker not found")


@router.get("/static/icons/{filename}", include_in_schema=False)
async def serve_icon(filename: str):
    """Serve PWA application vector and raster icons."""
    file_path = ICONS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Icon not found")
    if filename.endswith(".svg"):
        media_type = "image/svg+xml"
    elif filename.endswith(".ico"):
        media_type = "image/x-icon"
    else:
        media_type = "image/png"
    return Response(
        content=file_path.read_bytes(),
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=604800"}
    )


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve crisp favicon matching icon.svg graphics."""
    ico_path = ICONS_DIR / "favicon.ico"
    if ico_path.exists():
        return Response(
            content=ico_path.read_bytes(),
            media_type="image/x-icon",
            headers={"Cache-Control": "public, max-age=604800"}
        )
    svg_path = ICONS_DIR / "icon.svg"
    if svg_path.exists():
        return Response(
            content=svg_path.read_bytes(),
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=604800"}
        )
    return Response(status_code=204)


# ==========================================
# Interactive Web Dashboard
# ==========================================

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"


@router.get("/", response_class=HTMLResponse)
async def home_dashboard():
    """Serve responsive passenger-facing transit dashboard."""
    docs = documents_service.get_documents()
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    content = (
        template.replace("__METRO_URL__", docs.metro_url)
        .replace("__TRAIN_URL__", docs.train_url)
        .replace("__BUS_URL__", docs.bus_url)
    )
    return HTMLResponse(content=content)
