#!/usr/bin/env bash
# Runner for local bot and periodic news checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

ACTION="${1:-all}"

case "$ACTION" in
    bot)
        echo "🚀 Starting FCE Telegram Bot (polling mode)..."
        exec python main.py bot
        ;;
    web)
        echo "🌐 Starting FCE Web & REST API..."
        exec python main.py serve --host 0.0.0.0 --port 8000
        ;;
    news)
        echo "📢 Starting News Checker Daemon..."
        exec python main.py news-worker
        ;;
    sync)
        echo "🔄 Synchronizing GTFS Timetables..."
        exec python main.py sync-gtfs
        ;;
    all)
        echo "🚀 Starting FCE Bot and News daemon..."
        python main.py news-worker &
        PID_NEWS=$!
        python main.py bot &
        PID_BOT=$!

        trap "kill $PID_NEWS $PID_BOT 2>/dev/null || true" EXIT
        wait
        ;;
    *)
        echo "Usage: $0 {bot|web|news|sync|all}"
        exit 1
        ;;
esac
