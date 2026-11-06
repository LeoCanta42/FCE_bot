"""Command-line interface for FCE Bot operations."""

import sys
import argparse
import asyncio
import logging
from fce_bot.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)
logger = logging.getLogger("fce_bot.cli")


def run_bot() -> None:
    """Run Telegram bot using standard Long Polling (ideal for local/VPS/Docker)."""
    from fce_bot.bot.bot_app import create_bot_application

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured! Please set it in .env")
        sys.exit(1)

    logger.info("Starting FCE Telegram Bot in polling mode...")
    app = create_bot_application()
    app.run_polling()


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Run local FastAPI web server & REST API."""
    import uvicorn
    logger.info("Starting FastAPI server on http://%s:%d...", host, port)
    uvicorn.run("api.index:app", host=host, port=port, reload=reload)


def sync_gtfs() -> None:
    """Download and sync latest GTFS feed from circumetnea.it."""
    from fce_bot.data.gtfs_loader import download_and_sync_gtfs
    logger.info("Synchronizing GTFS feed...")
    stops, trips, st = download_and_sync_gtfs()
    logger.info("GTFS sync completed: %d stops, %d trips, %d stop_times", stops, trips, st)


def check_news() -> None:
    """Check for new articles once and broadcast."""
    from fce_bot.bot.bot_app import create_bot_application
    from fce_bot.bot.handlers.news import check_and_broadcast_news

    app = create_bot_application()

    async def _run():
        await app.initialize()
        count = await check_and_broadcast_news(app.bot)
        logger.info("News check finished: %d new announcements broadcasted", count)

    asyncio.run(_run())


def run_news_worker(interval_seconds: int = 1800) -> None:
    """Run persistent worker checking for news at regular intervals."""
    import time
    logger.info("Starting periodic news worker (checking every %d seconds)...", interval_seconds)
    while True:
        try:
            check_news()
        except Exception as e:
            logger.error("Error during scheduled news check: %s", e)
        time.sleep(interval_seconds)


def show_stats() -> None:
    """Print current system statistics."""
    from fce_bot.data.users_repo import UsersRepository
    from fce_bot.data.db import get_db

    repo = UsersRepository()
    stats = repo.get_stats()
    with get_db() as conn:
        cur = conn.cursor()
        stops = cur.execute("SELECT count(*) FROM stops").fetchone()[0]
        trips = cur.execute("SELECT count(*) FROM trips").fetchone()[0]
        st = cur.execute("SELECT count(*) FROM stop_times").fetchone()[0]
        routes = cur.execute("SELECT count(*) FROM routes").fetchone()[0]

    print("=== FCE Bot System Statistics ===")
    print(f"Users Total:        {stats['total_users']}")
    print(f"Subscribed Users:   {stats['subscribed_users']}")
    print(f"Active (30d):       {stats['active_last_30_days']}")
    print(f"GTFS Routes:        {routes}")
    print(f"GTFS Stops:         {stops}")
    print(f"GTFS Trips:         {trips}")
    print(f"GTFS Stop Times:    {st}")


def main() -> None:
    parser = argparse.ArgumentParser(description="FCE Circumetnea Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("bot", help="Run Telegram bot in polling mode")
    web_p = subparsers.add_parser("serve", help="Run web server")
    web_p.add_argument("--host", default="0.0.0.0", help="Host address")
    web_p.add_argument("--port", type=int, default=8000, help="Port")
    web_p.add_argument("--reload", action="store_true", help="Enable auto-reload")

    subparsers.add_parser("sync-gtfs", help="Download and parse official GTFS feed")
    subparsers.add_parser("check-news", help="Check for new articles and broadcast")
    worker_p = subparsers.add_parser("news-worker", help="Run news polling loop daemon")
    worker_p.add_argument("--interval", type=int, default=1800, help="Check interval in seconds")
    subparsers.add_parser("stats", help="Print system statistics")

    args = parser.parse_args()

    if args.command == "bot":
        run_bot()
    elif args.command == "serve":
        run_server(host=args.host, port=args.port, reload=args.reload)
    elif args.command == "sync-gtfs":
        sync_gtfs()
    elif args.command == "check-news":
        check_news()
    elif args.command == "news-worker":
        run_news_worker(interval_seconds=args.interval)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
