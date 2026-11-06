"""Document links and PDF download handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.services.documents_service import documents_service
from fce_bot.bot.keyb import documents_keyboard, main_menu_keyboard

logger = logging.getLogger(__name__)


async def documents_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /documenti command."""
    docs = documents_service.get_documents()
    text = (
        "📄 *Documenti e Tabelle Orari Ufficiali FCE*\n\n"
        "Puoi scaricare direttamente i PDF ufficiali aggiornati dal sito Circumetnea:"
    )
    await update.effective_message.reply_text(
        text,
        reply_markup=documents_keyboard(docs.metro_url, docs.train_url, docs.bus_url),
        parse_mode="Markdown"
    )


async def documents_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data

    docs = documents_service.get_documents()

    if data == "doc_all":
        text = (
            "📄 *Documenti e Tabelle Orari Ufficiali FCE*\n\n"
            "Seleziona il documento da scaricare in formato PDF:"
        )
        await query.edit_message_text(
            text,
            reply_markup=documents_keyboard(docs.metro_url, docs.train_url, docs.bus_url),
            parse_mode="Markdown"
        )
        return

    if data == "doc_metro":
        await query.message.reply_text(
            f"🚇 *Orario Metropolitana di Catania:*\n{docs.metro_url}",
            parse_mode="Markdown"
        )
        return

    if data == "doc_train":
        await query.message.reply_text(
            f"🚆 *Orario Treni Superficie (Circumetnea):*\n{docs.train_url}",
            parse_mode="Markdown"
        )
        return

    if data == "doc_bus":
        await query.message.reply_text(
            f"🚌 *Orario Autolinee (Bus):*\n{docs.bus_url}",
            parse_mode="Markdown"
        )
        return
