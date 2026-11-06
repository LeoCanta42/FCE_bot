#!/usr/bin/env bash
# Reset script to rebuild local database and test environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Resetting FCE Bot database and caches..."

# Remove old databases if needed
rm -f fce_lines.db users.db

# Ensure virtualenv is active if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run GTFS sync to rebuild database from official Circumetnea open data
python main.py sync-gtfs

echo "✅ Database and cache reset complete! You can now start the bot with: python main.py bot"
