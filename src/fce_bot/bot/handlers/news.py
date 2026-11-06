"""News commands and announcement broadcast handlers."""

import logging
from telegram import Update, Bot
from telegram.ext import ContextTypes
from fce_bot.config import settings
from fce_bot.services.news_service import news_service
from fce_bot.data.users_repo import UsersRepository
from fce_bot.bot.keyb import main_menu_keyboard

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /news command."""
    articles = news_service.fetch_news(limit=3)
    if not articles:
        await update.effective_message.reply_text(
            "Al momento non ci sono notizie o avvisi recenti.",
            reply_markup=main_menu_keyboard()
        )
        return

    for item in articles:
        await update.effective_message.reply_text(
            item.format_telegram(),
            parse_mode="Markdown",
            disable_web_page_preview=False
        )


async def news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'news_latest' button press."""
    query = update.callback_query
    await query.answer()

    articles = news_service.fetch_news(limit=3)
    if not articles:
        await query.edit_message_text(
            "Al momento non ci sono notizie o avvisi recenti.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Send first article by editing the message, subsequent ones as new messages
    first = articles[0]
    await query.edit_message_text(
        first.format_telegram(),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True
    )

    for item in articles[1:]:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=item.format_telegram(),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )


async def check_and_broadcast_news(bot: Bot) -> int:
    """Check for new articles and broadcast them to channel and users."""
    new_items = news_service.check_for_new_articles()
    if not new_items:
        return 0

    sent_count = 0
    channel_id = settings.TELEGRAM_CHANNEL_ID

    for item in new_items:
        msg_text = "🚨 *NUOVO AVVISO CIRCUMETNEA:*\n\n" + item.format_telegram()

        # Send to broadcast channel if configured
        if channel_id:
            try:
                await bot.send_message(
                    chat_id=channel_id,
                    text=msg_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                sent_count += 1
            except Exception as e:
                logger.error("Failed to broadcast news to channel %s: %s", channel_id, e)

    return sent_count
