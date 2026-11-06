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

1. *Ricerca Guidata:* premi *Cerca Linea / Orari*, seleziona il mezzo (Bus, Treno, Metro o Tutti), scegli l'iniziale o la fermata di partenza e arrivo, ed infine l'orario.

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

5. *Avvisi e Notifiche:*
Puoi iscriverti agli avvisi in tempo reale su scioperi e ritardi premendo il pulsante *Notifiche & Avvisi* o inviando il comando /iscriviti (e disattivare con /disiscriviti).

6. *Privacy:*
Il bot memorizza esclusivamente il `chat_id` e la data di ultimo accesso per permetterti di ricevere eventuali avvisi di servizio qualora tu decida di iscriverti manualmente. Nessun messaggio broadcast viene inviato senza la tua esplicita iscrizione.

👨‍💻 *Sviluppatore & Progetto:*
Creato e sviluppato da *LeoCanta42*.
Progetto open-source disponibile su [GitHub](https://github.com/LeoCanta42/FCE_bot)."""


PRIVACY_TEXT = """🔒 *Informativa sulla Privacy & GDPR (Regolamento UE 2016/679)*

• *Finalità del servizio:* Questo bot fornisce informazioni su orari, linee e avvisi di servizio della Ferrovia Circumetnea e Metropolitana di Catania.
• *Consenso e Notifiche (Art. 6/7):* Nessun utente viene iscritto automaticamente agli avvisi di servizio. La ricezione delle notifiche avviene esclusivamente su richiesta manuale tramite pulsante dedicato o comando /iscriviti.
• *Dati trattati (Minimizzazione Art. 5):* Viene memorizzato unicamente il tuo ID tecnico di chat Telegram (`chat_id`), necessario esclusivamente per recapitare gli avvisi ufficiali di servizio da te richiesti.
• *Nessun tracciamento o profilazione:* Non raccogliamo dati personali, non utilizziamo strumenti di profilazione e nessun dato viene ceduto a terzi.
• *Periodo di conservazione:* I dati di utilizzo inattivi da oltre 60 giorni vengono eliminati automaticamente dal database.
• *Diritto alla cancellazione (Art. 17 - Oblio):* Puoi richiedere la cancellazione immediata e totale di qualsiasi informazione associata al tuo account inviando il comando /cancella."""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and 'menu_main' callback."""
    chat = update.effective_chat
    if chat and getattr(chat, "type", None) in ("channel", "group", "supergroup"):
        return

    if chat:
        # GDPR data minimization: store only technical chat_id
        users_repo.register_or_update(chat_id=chat.id)

    # Clear wizard session state
    context.user_data.clear()

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                WELCOME_TEXT,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Start command edit notice: %s", e)
    else:
        await update.effective_message.reply_text(
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command and 'help_info' callback."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                HELP_TEXT,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Help command edit notice: %s", e)
    else:
        await update.effective_message.reply_text(
            HELP_TEXT,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display GDPR privacy policy (/privacy)."""
    await update.effective_message.reply_text(
        PRIVACY_TEXT,
        parse_mode="Markdown"
    )


async def cancella_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute GDPR Art. 17 Right to Erasure (/cancella or /stop)."""
    chat = update.effective_chat
    if chat:
        users_repo.delete_user(chat.id)
    context.user_data.clear()
    await update.effective_message.reply_text(
        "🗑️ *Dati eliminati con successo (GDPR Art. 17)*\n\n"
        "Il tuo identificativo e l'iscrizione alle notifiche sono stati rimossi definitivamente dal database.\n"
        "Non riceverai più alcun avviso di servizio.\n\n"
        "Se in futuro vorrai tornare a utilizzare il bot, potrai semplicemente inviare nuovamente il comando /start.",
        parse_mode="Markdown"
    )


async def chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the ID of current chat (useful for configuring notification channels)."""
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(
        f"🆔 ID di questa chat: `{chat_id}`",
        parse_mode="Markdown"
    )
