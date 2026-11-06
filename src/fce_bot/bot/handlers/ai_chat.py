"""AI assistant natural language chat message handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.services.ai_service import ai_service
from fce_bot.data.users_repo import UsersRepository
from fce_bot.bot.keyb import main_menu_keyboard
from fce_bot.bot.handlers.admin import is_admin, handle_admin_text_input

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle freeform natural language text messages using AI service (private chat only)."""
    # Strictly ignore channel posts, groups, or non-private updates
    if getattr(update, "channel_post", None):
        return
    chat = update.effective_chat
    if not chat or getattr(chat, "type", None) in ("channel", "group", "supergroup"):
        return

    message = update.effective_message
    if not message or not message.text:
        return

    text = message.text.strip()
    # Ignore commands
    if text.startswith("/"):
        return

    user = update.effective_user
    chat = update.effective_chat
    if user and chat:
        users_repo.register_or_update(
            chat_id=chat.id,
            username=getattr(user, "username", None),
            first_name=getattr(user, "first_name", None)
        )

    uid = getattr(user, "id", None) or getattr(chat, "id", None)
    admin_flag = is_admin(uid) if isinstance(uid, int) else False

    # If admin is currently in an interactive admin prompt (user search / broadcast), handle it here
    user_data = getattr(context, "user_data", None)
    if admin_flag and isinstance(user_data, dict) and user_data.get("admin_state"):
        handled = await handle_admin_text_input(update, context)
        if handled:
            return

    # Permission check: AI is restricted to admin and authorized users only
    if not users_repo.is_ai_allowed(chat.id):
        logger.info("Unauthorized AI access attempt from chat_id %s", chat.id)
        restricted_msg = (
            "🔒 *Assistente AI ad accesso limitato*\n\n"
            "L'assistente conversazionale AI è attualmente riservato agli utenti abilitati dall'amministratore.\n\n"
            f"🆔 Il tuo ID chat è: `{chat.id}`\n\n"
            "Puoi comunicare questo ID all'amministratore per richiedere l'abilitazione (es. con `/allow_ai {chat.id}`).\n\n"
            "Nel frattempo, puoi cercare tutte le corse e gli orari con il tasto *Cerca Linea / Orari* oppure usando i comandi /viaggio e /fermate."
        ).format(chat=chat)
        await message.reply_text(
            restricted_msg,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag)
        )
        return

    # Let the user know the bot is thinking
    await context.bot.send_chat_action(chat_id=chat.id, action="typing")

    response = ai_service.answer_query(text)
    try:
        await message.reply_text(
            response.answer,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.warning("Markdown parse error on AI response: %s. Sending plain text fallback.", e)
        await message.reply_text(
            response.answer,
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
            disable_web_page_preview=True
        )


async def ai_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain how to use the AI assistant."""
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user
    chat_id = chat.id if chat else None
    uid = getattr(user, "id", None) or chat_id
    admin_flag = is_admin(uid) if isinstance(uid, int) else False

    # If user is not authorized for AI, display restriction notice and instructions
    if chat_id and not users_repo.is_ai_allowed(chat_id):
        restricted_msg = (
            "🔒 *Assistente AI ad accesso limitato*\n\n"
            "L'assistente conversazionale AI è attualmente riservato agli utenti abilitati dall'amministratore.\n\n"
            f"🆔 Il tuo ID chat è: `{chat_id}`\n\n"
            "Puoi comunicare questo identificativo all'amministratore per richiedere l'abilitazione.\n\n"
            "Puoi comunque cercare tutte le corse e gli orari con il tasto *Cerca Linea / Orari* oppure usando i comandi /viaggio e /fermate."
        )
        try:
            await query.edit_message_text(
                restricted_msg,
                reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("AI help restricted edit notice: %s", e)
        return

    help_msg = (
        "🤖 *Assistente AI per la Mobilità FCE*\n\n"
        "Non serve cliccare decine di pulsanti! Puoi scrivermi qualsiasi domanda come se parlassi con una persona reale.\n\n"
        "💬 *Esempi di domande che puoi fare:*\n"
        "• _\"Come vado da Catania a Bronte alle 14:00?\"_\n"
        "• _\"Orari della littorina da Paternò a Randazzo verso le 16\"_\n"
        "• _\"A che ora c'è la metro da Monte Po a Borgo stasera alle 20?\"_\n"
        "• _\"Dove posso scaricare i pdf degli orari?\"_\n\n"
        "👉 Scrivi adesso la tua richiesta qui sotto!"
    )
    try:
        await query.edit_message_text(
            help_msg,
            reply_markup=main_menu_keyboard(is_admin_user=admin_flag),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.debug("AI help edit notice: %s", e)
