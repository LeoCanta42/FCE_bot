"""Inline keyboards for Telegram bot interaction."""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from fce_bot.core.models import TransportType, FilterType, Stop


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main dashboard menu buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚌 Orario Bus", callback_data="doc_bus"),
            InlineKeyboardButton("🚆 Orario Treni", callback_data="doc_train"),
        ],
        [
            InlineKeyboardButton("🚇 Orario Metro", callback_data="doc_metro"),
            InlineKeyboardButton("🔍 Cerca Linea / Orari", callback_data="wizard_start"),
        ],
        [
            InlineKeyboardButton("📢 Ultime Notizie", callback_data="news_latest"),
            InlineKeyboardButton("🤖 Assistente AI", callback_data="ai_help"),
        ],
        [
            InlineKeyboardButton("📄 Tutti i Documenti PDF", callback_data="doc_all"),
            InlineKeyboardButton("ℹ️ Guida & Info", callback_data="help_info"),
        ],
    ])


def transport_select_keyboard() -> InlineKeyboardMarkup:
    """Step 1: Choose mode of transport."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚌 Bus / Autolinee", callback_data="tt_bus"),
            InlineKeyboardButton("🚆 Treno (Superficie)", callback_data="tt_train"),
        ],
        [
            InlineKeyboardButton("🚇 Metropolitana", callback_data="tt_metro"),
            InlineKeyboardButton("🚍 Tutti i Mezzi", callback_data="tt_any"),
        ],
        [
            InlineKeyboardButton("⬅️ Menu Principale", callback_data="menu_main"),
        ],
    ])


def stops_pagination_keyboard(
    stops: List[Stop],
    page: int = 0,
    is_departure: bool = True,
    page_size: int = 8
) -> InlineKeyboardMarkup:
    """Paginated inline keyboard for choosing departure/arrival stops."""
    total_stops = len(stops)
    total_pages = max(1, (total_stops + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * page_size
    page_stops = stops[start_idx : start_idx + page_size]

    cb_prefix = "dep_stop:" if is_departure else "arr_stop:"
    nav_prefix = "page_dep:" if is_departure else "page_arr:"

    keyboard = []
    # 2 buttons per row
    row = []
    for s in page_stops:
        display_name = s.stop_name[:24]
        row.append(InlineKeyboardButton(display_name, callback_data=f"{cb_prefix}{s.stop_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prec", callback_data=f"{nav_prefix}{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Succ ➡️", callback_data=f"{nav_prefix}{page + 1}"))
    keyboard.append(nav_row)

    # Back button
    keyboard.append([
        InlineKeyboardButton("⬅️ Indietro", callback_data="wizard_start" if is_departure else "back_to_departure")
    ])

    return InlineKeyboardMarkup(keyboard)


def filter_type_keyboard() -> InlineKeyboardMarkup:
    """Step 3: Choose filtering condition for schedule lookup."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕒 Partenza vicino l'ora scelta", callback_data=f"filt:{FilterType.DEPARTURE_NEAR.value}"),
        ],
        [
            InlineKeyboardButton("🏁 Arrivo vicino l'ora scelta", callback_data=f"filt:{FilterType.ARRIVAL_NEAR.value}"),
        ],
        [
            InlineKeyboardButton("⏱ Dalla partenza in poi (consigliato)", callback_data=f"filt:{FilterType.DEPARTURE_AFTER.value}"),
        ],
        [
            InlineKeyboardButton("⌛ Prima dell'orario di arrivo", callback_data=f"filt:{FilterType.ARRIVAL_BEFORE.value}"),
        ],
        [
            InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_arrival"),
        ],
    ])


def hours_keyboard() -> InlineKeyboardMarkup:
    """Step 4: Choose target hour."""
    hours = [
        "05:00", "06:00", "07:00", "08:00",
        "09:00", "10:00", "11:00", "12:00",
        "13:00", "14:00", "15:00", "16:00",
        "17:00", "18:00", "19:00", "20:00",
        "21:00", "22:00"
    ]
    keyboard = []
    row = []
    for h in hours:
        row.append(InlineKeyboardButton(h, callback_data=f"hour:{h}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)


def documents_keyboard(metro_url: str, train_url: str, bus_url: str) -> InlineKeyboardMarkup:
    """Keyboard with direct external links to download PDF schedules."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚇 Scarica PDF Metro", url=metro_url)],
        [InlineKeyboardButton("🚆 Scarica PDF Treni Superficie", url=train_url)],
        [InlineKeyboardButton("🚌 Scarica PDF Autolinee", url=bus_url)],
        [InlineKeyboardButton("⬅️ Menu Principale", callback_data="menu_main")],
    ])
