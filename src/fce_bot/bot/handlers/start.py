"""Handler for start, help, and navigation commands."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.bot.keyb import main_menu_keyboard
from fce_bot.data.users_repo import UsersRepository

logger = logging.getLogger(__name__)
users_repo = UsersRepository()

WELCOME_TEXT = """🌋 *Benvenuto su FCE Circumetnea Bot!*

Il tuo assistente completo per gli orari e la mobilità della **Ferrovia Circumetnea** e **Metropolitana di Catania**.

Cosa puoi fare:
• 🔍 *Cerca Linea / Orari:* wizard guidato per trovare corse dirette o con cambio.
• 🤖 *Assistente AI:* scrivi una frase qualsiasi in chat (es. _"Come vado da Catania a Bronte alle 14?"_) per ricevere subito una risposta intelligente!
• 📢 *Ultime Notizie:* avvisi in tempo reale su scioperi, modifiche e orari.
• 📄 *Documenti:* link ufficiali aggiornati ai PDF degli orari FCE.

Scegli un'opzione dal menu sottostante:"""

HELP_TEXT = """📖 *Guida all'uso del bot:*

1. *Ricerca Guidata:* premi *Cerca Linea / Orari*, seleziona il mezzo (Bus, Treno, Metro o Tutti), scegli la fermata di partenza e arrivo, ed infine l'orario.

2. *Scorciatoia Comando:*
Puoi cercare direttamente senza usare i bottoni:
`/viaggio Catania - Bronte 14:00`
`/viaggio Randazzo Paternò`

3. *Assistente AI:*
Puoi scrivere liberamente come a una persona:
_"A che ora c'è la metro da Monte Po a Stesicoro?"_
_"C'è un treno da Randazzo alle 12:30?"_

4. *Fermate:*
`/fermate Milo` per vedere tutte le stazioni che contengono "Milo".

5. *Privacy:*
Il bot memorizza esclusivamente il chat_id e la data di ultimo accesso per permetterti di ricevere eventuali avvisi di servizio. I dati inattivi da oltre 60 giorni vengono eliminati automaticamente."""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    chat = update.effective_chat
    if user and chat:
        users_repo.register_or_update(
            chat_id=chat.id,
            username=user.username,
            first_name=user.first_name
        )

    # Clear wizard session state
    context.user_data.clear()

    await update.effective_message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.effective_message.reply_text(
        HELP_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the ID of current chat (useful for configuring notification channels)."""
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(
        f"🆔 ID di questa chat: `{chat_id}`",
        parse_mode="Markdown"
    )
