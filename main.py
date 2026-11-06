"""Main entry point for running FCE Bot."""

import sys
from pathlib import Path

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from fce_bot.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default action when invoked with no arguments: start bot
        sys.argv.append("bot")
    main()
