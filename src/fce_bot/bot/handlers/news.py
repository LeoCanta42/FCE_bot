"""News commands and announcement broadcast handlers."""

import logging
from telegram import Update, Bot
from telegram.ext import ContextTypes
from fce_bot.config import settings
from fce_bot.services.news_service import news_service
from fce_bot.data.users_repo import UsersRepository
from fce_bot.bot.keyb import main_menu_keyboard, subscription_manage_keyboard

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


def format_news_digest(articles) -> str:
    """Format a list of news items into a single neat Telegram digest with the newest on top."""
    if not articles:
        return "Al momento non ci sono notizie o avvisi recenti pubblicati da Circumetnea."

    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    lines = ["📢 *Ultime Notizie & Avvisi Ufficiali FCE*\n"]

    for idx, item in enumerate(articles):
        num = number_emojis[idx] if idx < len(number_emojis) else f"{idx + 1}."
        date_str = item.format_date_italian()
        summary = item.get_clean_summary(max_length=200)

        lines.append(f"{num} *{item.title.strip()}*")
        if date_str:
            lines.append(f"📅 _{date_str}_")
        if summary:
            lines.append(f"{summary}")
        lines.append(f"🔗 [Leggi notizia completa]({item.link})\n")

    return "\n".join(lines)


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /news command."""
    articles = news_service.fetch_news(limit=4)
    chat_id = update.effective_chat.id if update.effective_chat else None
    is_sub = users_repo.is_user_subscribed(chat_id) if chat_id else False

    digest = format_news_digest(articles)
    try:
        await update.effective_message.reply_text(
            digest,
            parse_mode="Markdown",
            reply_markup=subscription_manage_keyboard(is_sub),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.warning("Markdown parse error on news digest: %s. Sending plain fallback.", e)
        plain = digest.replace("*", "").replace("_", "")
        await update.effective_message.reply_text(
            plain,
            reply_markup=subscription_manage_keyboard(is_sub),
            disable_web_page_preview=True
        )


async def news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'news_latest' button press."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id if update.effective_chat else None
    is_sub = users_repo.is_user_subscribed(chat_id) if chat_id else False

    articles = news_service.fetch_news(limit=4)
    digest = format_news_digest(articles)

    try:
        await query.edit_message_text(
            digest,
            parse_mode="Markdown",
            reply_markup=subscription_manage_keyboard(is_sub),
            disable_web_page_preview=True
        )
    except Exception as e:
        if "Message is not modified" in str(e):
            return
        logger.warning("Markdown error rendering news digest: %s. Falling back to plain text.", e)
        plain = digest.replace("*", "").replace("_", "")
        await query.edit_message_text(
            plain,
            reply_markup=subscription_manage_keyboard(is_sub),
            disable_web_page_preview=True
        )


# ==========================================
# Manual News Broadcast Subscription (Opt-in)
# ==========================================

async def news_sub_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display news subscription preferences and manual toggle."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    is_sub = users_repo.is_user_subscribed(chat_id)

    status_str = "🟢 *Iscritto (ricevi gli avvisi di servizio)*" if is_sub else "🔴 *Non iscritto (nessun avviso inviato)*"

    text = (
        "🔔 *Gestione Notifiche & Avvisi FCE*\n\n"
        "Desideri ricevere automaticamente su Telegram gli avvisi in tempo reale su scioperi, modifiche orari e deviazioni delle linee Circumetnea e Metro?\n\n"
        f"📌 *Stato attuale:* {status_str}\n\n"
        "L'iscrizione è libera e richiede il tuo consenso esplicito (GDPR). Nessuna notifica viene inviata senza la tua richiesta manuale."
    )
    try:
        await query.edit_message_text(
            text,
            reply_markup=subscription_manage_keyboard(is_sub),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.debug("Notice on sub menu edit: %s", e)


async def sub_enable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually register user to receive news broadcasts."""
    query = update.callback_query
    await query.answer("✅ Iscrizione alle notifiche completata!")

    chat = update.effective_chat
    user = update.effective_user
    if chat:
        users_repo.subscribe_user(
            chat_id=chat.id,
            username=user.username if user else None,
            first_name=user.first_name if user else None
        )

    text = (
        "✅ *Iscrizione completata con successo!*\n\n"
        "Il tuo account è ora registrato per ricevere gli avvisi ufficiali di servizio della Ferrovia Circumetnea e Metro.\n\n"
        "Non appena l'azienda comunicherà avvisi urgenti, scioperi o variazioni di percorso, riceverai una notifica qui su Telegram.\n\n"
        "Puoi disattivare le notifiche in qualunque momento premendo *Disattiva Notifiche* o inviando /disiscriviti."
    )
    try:
        await query.edit_message_text(
            text,
            reply_markup=subscription_manage_keyboard(is_subscribed=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.debug("Notice on sub enable edit: %s", e)


async def sub_disable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually unregister user from receiving news broadcasts."""
    query = update.callback_query
    await query.answer("🔕 Notifiche disattivate.")

    chat = update.effective_chat
    if chat:
        users_repo.unsubscribe_user(chat_id=chat.id)

    text = (
        "🔕 *Notifiche disattivate*\n\n"
        "Il tuo identificativo è stato rimosso dalla lista di trasmissione degli avvisi.\n"
        "Non riceverai più messaggi automatici di notifica.\n\n"
        "Potrai comunque continuare a usare tutte le funzioni del bot (orari, calcolo percorsi, assistente AI) o riattivare le notifiche quando preferisci."
    )
    try:
        await query.edit_message_text(
            text,
            reply_markup=subscription_manage_keyboard(is_subscribed=False),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.debug("Notice on sub disable edit: %s", e)


async def iscriviti_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /iscriviti to manually opt-in to service alerts."""
    chat = update.effective_chat
    user = update.effective_user
    if chat:
        users_repo.subscribe_user(
            chat_id=chat.id,
            username=user.username if user else None,
            first_name=user.first_name if user else None
        )
    await update.effective_message.reply_text(
        "✅ *Iscrizione agli avvisi completata!*\n\n"
        "Riceverai notifiche su scioperi e variazioni orari FCE.\n"
        "Per disattivare in futuro: /disiscriviti",
        reply_markup=subscription_manage_keyboard(is_subscribed=True),
        parse_mode="Markdown"
    )


async def disiscriviti_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /disiscriviti to manually opt-out of service alerts."""
    chat = update.effective_chat
    if chat:
        users_repo.unsubscribe_user(chat_id=chat.id)
    await update.effective_message.reply_text(
        "🔕 *Notifiche disattivate con successo.*\n\n"
        "Non riceverai più avvisi automatici.\n"
        "Per iscriverti di nuovo: /iscriviti",
        reply_markup=subscription_manage_keyboard(is_subscribed=False),
        parse_mode="Markdown"
    )


async def check_and_broadcast_news(bot: Bot) -> int:
    """Check for new articles and broadcast them to channel and subscribed users."""
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

        # Send strictly to users who manually subscribed
        subscribed_ids = users_repo.get_subscribed_chat_ids()
        for cid in subscribed_ids:
            try:
                await bot.send_message(
                    chat_id=cid,
                    text=msg_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send news to subscribed user %s: %s", cid, e)

    return sent_count
