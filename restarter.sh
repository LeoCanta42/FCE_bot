#!/usr/bin/env bash
# Safe process manager for FCE Bot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.bot.pid"
ACTION="${1:-status}"

stop_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 Stopping FCE Bot process (PID: $PID)..."
            kill "$PID" || true
            sleep 1
        fi
        rm -f "$PID_FILE"
        echo "✅ Bot stopped."
    else
        echo "ℹ️ No running bot PID found."
    fi
}

start_bot() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️ Bot is already running with PID $(cat "$PID_FILE")"
        return
    fi

    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi

    echo "🚀 Starting FCE Bot in background..."
    nohup python main.py bot > bot.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ FCE Bot started with PID $(cat "$PID_FILE") (logs in bot.log)"
}

case "$ACTION" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        stop_bot
        sleep 1
        start_bot
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "🟢 FCE Bot is RUNNING (PID: $(cat "$PID_FILE"))"
        else
            echo "🔴 FCE Bot is STOPPED"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
