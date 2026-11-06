"""AI assistant natural language chat message handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.services.ai_service import ai_service
from fce_bot.data.users_repo import UsersRepository
from fce_bot.bot.keyb import main_menu_keyboard

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle freeform natural language text messages using AI service."""
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
            username=user.username,
            first_name=user.first_name
        )

    # Let the user know the bot is thinking
    await context.bot.send_chat_action(chat_id=chat.id, action="typing")

    response = ai_service.answer_query(text)
    await message.reply_text(
        response.answer,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True
    )


async def ai_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain how to use the AI assistant."""
    query = update.callback_query
    await query.answer()

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
    await query.edit_message_text(
        help_msg,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
