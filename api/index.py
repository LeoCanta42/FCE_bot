"""Vercel Serverless Function entry point."""

import sys
from pathlib import Path

# Ensure src/ is on sys.path for Vercel execution environment
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fce_bot.config import settings
from fce_bot.api.router import router

app = FastAPI(
    title="Ferrovia Circumetnea (FCE) Transit & Bot API",
    description="Official GTFS transit schedule API, Telegram Webhook, News service and AI trip planner for FCE.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
