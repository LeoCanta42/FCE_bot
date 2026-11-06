"""Handler for start, help, and navigation commands."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.bot.keyb import main_menu_keyboard
from fce_bot.bot.handlers.admin import is_admin
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
Quando utilizzi il bot, vengono memorizzati `chat_id`, eventuale `@username`, nome e data di ultimo accesso (`last_active`) con *notifiche e AI disattivate di default*. Questo permette di gestire eventuali abilitazioni (notifiche o accesso AI) e di pulire automaticamente i profili inattivi dopo 60 giorni. Se non desideri più usare il bot, puoi eliminare istantaneamente e definitivamente il tuo record con il comando /cancella.

👨‍💻 *Sviluppatore & Progetto:*
Creato e sviluppato da *LeoCanta42*.
Progetto open-source disponibile su [GitHub](https://github.com/LeoCanta42/FCE_bot)."""


PRIVACY_TEXT = """🔒 *Informativa sulla Privacy & GDPR (Regolamento UE 2016/679)*

• *Finalità del servizio:* Questo bot fornisce informazioni su orari, linee e avvisi di servizio della Ferrovia Circumetnea e Metropolitana di Catania.
• *Registrazione Tecnica e Dati Trattati (Art. 5 e Art. 6):* Quando interagisci con il bot in chat privata, il sistema registra il tuo `chat_id` tecnico, l'eventuale `@username`, il nome (`first_name`) e il timestamp di ultimo utilizzo (`last_active`), impostando **notifiche disattivate** e **accesso AI disabilitato** per impostazione predefinita.
• *Perché vengono conservati questi dati:* Questi dati sono utilizzati esclusivamente per:
  1. Consentire all'amministratore o all'utente di gestire l'abilitazione all'Assistente AI o l'iscrizione volontaria agli avvisi di servizio;
  2. Effettuare la pulizia automatica (`auto-clean`) dei profili inattivi tramite la data di ultimo accesso.
• *Consenso alle Notifiche (Opt-in esplicito):* Nessun utente viene iscritto automaticamente agli avvisi broadcast. La ricezione delle notifiche avviene solo su esplicita attivazione tramite pulsante dedicato o comando /iscriviti (disattivabile in qualsiasi momento con /disiscriviti).
• *Nessuna profilazione o cessione a terzi:* Non effettuiamo tracciamento pubblicitario o profilazione commerciale e nessun dato viene ceduto o condiviso con terze parti.
• *Periodo di conservazione (Auto-Clean 60 giorni):* I record degli utenti che non interagiscono con il bot da oltre 60 giorni vengono rimossi automaticamente dal database.
• *Diritto alla Cancellazione / Oblio (Art. 17 GDPR):* Se non desideri più utilizzare il bot o vuoi rimuovere i tuoi dati, sei libero di farlo in qualsiasi momento inviando il comando /cancella (o /stop): il tuo record verrà eliminato immediatamente e definitivamente dal database."""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and 'menu_main' callback."""
    chat = update.effective_chat
    if chat and getattr(chat, "type", None) in ("channel", "group", "supergroup"):
        return

    user = update.effective_user
    if chat:
        users_repo.register_or_update(
            chat_id=chat.id,
            username=getattr(user, "username", None) if user else None,
            first_name=getattr(user, "first_name", None) if user else None,
        )

    # Clear wizard / admin session state
    context.user_data.clear()

    uid = getattr(user, "id", None) or (getattr(chat, "id", None) if chat else None)
    admin_flag = is_admin(uid) if isinstance(uid, int) else False

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                WELCOME_TEXT,
                reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Start command edit notice: %s", e)
    else:
        await update.effective_message.reply_text(
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
            parse_mode="Markdown"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command and 'help_info' callback."""
    user = update.effective_user
    chat = update.effective_chat
    uid = getattr(user, "id", None) or (getattr(chat, "id", None) if chat else None)
    admin_flag = is_admin(uid) if isinstance(uid, int) else False

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                HELP_TEXT,
                reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Help command edit notice: %s", e)
    else:
        await update.effective_message.reply_text(
            HELP_TEXT,
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
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
