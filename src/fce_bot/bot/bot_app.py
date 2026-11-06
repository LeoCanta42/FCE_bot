"""Telegram Application factory and handler configuration."""

import logging
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    TypeHandler,
    ContextTypes,
    filters,
)
from fce_bot.config import settings
from fce_bot.data.users_repo import UsersRepository
from fce_bot.bot.handlers.start import (
    start_command,
    help_command,
    chat_id_command,
    privacy_command,
    cancella_command,
)
from fce_bot.bot.handlers.timetable import (
    viaggio_command,
    fermate_command,
    wizard_callback,
)
from fce_bot.bot.handlers.news import (
    news_command,
    news_callback,
    news_sub_menu_callback,
    sub_enable_callback,
    sub_disable_callback,
    iscriviti_command,
    disiscriviti_command,
)
from fce_bot.bot.handlers.documents import documents_command, documents_callback
from fce_bot.bot.handlers.ai_chat import ai_message_handler, ai_help_callback
from fce_bot.bot.handlers.admin import (
    admin_command,
    admin_callback,
    stats_command,
    sync_gtfs_command,
    broadcast_command,
    user_command,
    users_command,
    allow_ai_command,
    disallow_ai_command,
    sub_user_command,
    unsub_user_command,
    delete_user_command,
    list_ai_command,
)

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


async def track_user_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically register/update private chat users on any message, command, or button click.
    
    New users are stored with notifications disabled (is_subscribed=0) and AI disabled (ai_allowed=0)
    unless they explicitly opt-in or an admin enables them.
    """
    if getattr(update, "channel_post", None):
        return
    chat = update.effective_chat
    if not chat or getattr(chat, "type", None) != "private":
        return

    # Do not re-create record when user is executing /cancella or /stop (GDPR Right to Erasure)
    msg = update.effective_message
    if msg and msg.text:
        cmd = msg.text.strip().split()[0].lower().split("@")[0]
        if cmd in ("/cancella", "/stop"):
            return

    user = update.effective_user
    users_repo.register_or_update(
        chat_id=chat.id,
        username=getattr(user, "username", None) if user else None,
        first_name=getattr(user, "first_name", None) if user else None,
        is_subscribed=False,
    )

# List of public slash commands registered with Telegram for autocomplete menu
PUBLIC_BOT_COMMANDS = [
    BotCommand("start", "Menu principale e calcolo viaggio"),
    BotCommand("viaggio", "Cerca corsa (es. /viaggio Catania - Bronte)"),
    BotCommand("fermate", "Cerca stazioni e fermate FCE"),
    BotCommand("news", "Ultime notizie e avvisi di servizio"),
    BotCommand("iscriviti", "Ricevi notifiche su scioperi e variazioni"),
    BotCommand("disiscriviti", "Disattiva la ricezione delle notifiche"),
    BotCommand("documenti", "Scarica le tabelle orarie PDF ufficiali"),
    BotCommand("help", "Guida dettagliata all'uso del bot"),
    BotCommand("privacy", "Informativa GDPR e privacy"),
    BotCommand("cancella", "Cancella tutti i tuoi dati dal bot"),
    BotCommand("chat_id", "Mostra l'identificativo di questa chat"),
]


async def post_init(application: Application) -> None:
    """Register public bot commands with Telegram for '/' autocomplete."""
    token = application.bot.token
    if not token or token.startswith("0000000000"):
        return

    try:
        await application.bot.set_my_commands(PUBLIC_BOT_COMMANDS)
        logger.info("Bot commands successfully registered with Telegram for autocomplete.")
    except Exception as exc:
        logger.warning("Could not set bot commands: %s", exc)


async def error_handler(update: object, context) -> None:
    """Log unhandled exceptions during Telegram update processing without crashing."""
    err = getattr(context, "error", None)
    if err and "Message is not modified" in str(err):
        return
    logger.error("Unhandled exception while processing Telegram update: %s", err, exc_info=err)


def create_bot_application() -> Application:
    """Instantiate and configure the python-telegram-bot Application."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot will run in unconfigured mode.")
        token = "0000000000:DUMMY_TOKEN_FOR_INITIALIZATION"

    builder = ApplicationBuilder().token(token).post_init(post_init)
    app = builder.build()
    app.add_error_handler(error_handler)

    # Pre-processor (group -1): automatically save/update private user with is_subscribed=0, ai_allowed=0
    app.add_handler(TypeHandler(Update, track_user_interaction), group=-1)

    private_chat = filters.ChatType.PRIVATE

    # Commands - strictly restricted to direct private 1-to-1 chats
    app.add_handler(CommandHandler("start", start_command, filters=private_chat))
    app.add_handler(CommandHandler("help", help_command, filters=private_chat))
    app.add_handler(CommandHandler("viaggio", viaggio_command, filters=private_chat))
    app.add_handler(CommandHandler("fermate", fermate_command, filters=private_chat))
    app.add_handler(CommandHandler("news", news_command, filters=private_chat))
    app.add_handler(CommandHandler("iscriviti", iscriviti_command, filters=private_chat))
    app.add_handler(CommandHandler("disiscriviti", disiscriviti_command, filters=private_chat))
    app.add_handler(CommandHandler("documenti", documents_command, filters=private_chat))
    app.add_handler(CommandHandler("chat_id", chat_id_command, filters=private_chat))
    app.add_handler(CommandHandler("privacy", privacy_command, filters=private_chat))
    app.add_handler(CommandHandler("cancella", cancella_command, filters=private_chat))
    app.add_handler(CommandHandler("stop", cancella_command, filters=private_chat))

    # Admin commands (strictly private chat only)
    app.add_handler(CommandHandler("admin", admin_command, filters=private_chat))
    app.add_handler(CommandHandler("stats", stats_command, filters=private_chat))
    app.add_handler(CommandHandler("sync_gtfs", sync_gtfs_command, filters=private_chat))
    app.add_handler(CommandHandler("broadcast", broadcast_command, filters=private_chat))
    app.add_handler(CommandHandler("user", user_command, filters=private_chat))
    app.add_handler(CommandHandler("users", users_command, filters=private_chat))
    app.add_handler(CommandHandler("allow_ai", allow_ai_command, filters=private_chat))
    app.add_handler(CommandHandler("disallow_ai", disallow_ai_command, filters=private_chat))
    app.add_handler(CommandHandler("revoke_ai", disallow_ai_command, filters=private_chat))
    app.add_handler(CommandHandler("sub_user", sub_user_command, filters=private_chat))
    app.add_handler(CommandHandler("unsub_user", unsub_user_command, filters=private_chat))
    app.add_handler(CommandHandler("delete_user", delete_user_command, filters=private_chat))
    app.add_handler(CommandHandler("del_user", delete_user_command, filters=private_chat))
    app.add_handler(CommandHandler("list_ai", list_ai_command, filters=private_chat))

    # Callback queries
    app.add_handler(CallbackQueryHandler(start_command, pattern="^menu_main$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help_info$"))
    app.add_handler(CallbackQueryHandler(ai_help_callback, pattern="^ai_help$"))
    app.add_handler(CallbackQueryHandler(news_callback, pattern="^news_latest$"))
    app.add_handler(CallbackQueryHandler(news_sub_menu_callback, pattern="^news_sub_menu$"))
    app.add_handler(CallbackQueryHandler(sub_enable_callback, pattern="^sub_enable$"))
    app.add_handler(CallbackQueryHandler(sub_disable_callback, pattern="^sub_disable$"))
    app.add_handler(CallbackQueryHandler(documents_callback, pattern="^doc_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))
    app.add_handler(CallbackQueryHandler(wizard_callback))

    # Natural language AI chat fallback - strictly private 1-to-1 chat only
    app.add_handler(MessageHandler(private_chat & filters.TEXT & ~filters.COMMAND, ai_message_handler))

    return app
