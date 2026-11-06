"""Admin maintenance and broadcast handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.config import settings
from fce_bot.data.users_repo import UsersRepository
from fce_bot.data.gtfs_loader import download_and_sync_gtfs
from fce_bot.data.db import get_db

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


def is_admin(user_id: int) -> bool:
    """Check if given Telegram user is configured as an admin.
    
    Secure by default: if no admins are explicitly configured in ADMIN_USER_IDS,
    access to privileged administrative commands is denied.
    """
    if not settings.admin_user_ids:
        logger.warning("Admin command attempted but no ADMIN_USER_IDS configured. Denying access for user %s", user_id)
        return False
    return user_id in settings.admin_user_ids


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display user and database statistics (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    stats = users_repo.get_stats()
    with get_db() as conn:
        cur = conn.cursor()
        stops_cnt = cur.execute("SELECT count(*) as cnt FROM stops").fetchone()["cnt"]
        trips_cnt = cur.execute("SELECT count(*) as cnt FROM trips").fetchone()["cnt"]
        routes_cnt = cur.execute("SELECT count(*) as cnt FROM routes").fetchone()["cnt"]
        times_cnt = cur.execute("SELECT count(*) as cnt FROM stop_times").fetchone()["cnt"]
        news_cnt = cur.execute("SELECT count(*) as cnt FROM news_cache").fetchone()["cnt"]

    msg = (
        "📊 *Statistiche Sistema FCE Bot*\n\n"
        f"👥 *Utenti Totali:* `{stats['total_users']}`\n"
        f"🔔 *Iscritti attivi:* `{stats['subscribed_users']}`\n"
        f"⚡ *Attivi ultimi 30gg:* `{stats['active_last_30_days']}`\n\n"
        "🗄 *Database GTFS:*\n"
        f"• Fermate censite: `{stops_cnt}`\n"
        f"• Linee/Percorsi: `{routes_cnt}`\n"
        f"• Corse giornaliere: `{trips_cnt}`\n"
        f"• Orari di passaggio: `{times_cnt}`\n"
        f"• Notizie memorizzate: `{news_cnt}`\n"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


async def sync_gtfs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger manual GTFS database re-sync from circumetnea.it (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    status_msg = await update.effective_message.reply_text("⏳ Download e sincronizzazione GTFS in corso...")
    try:
        stops, trips, st = download_and_sync_gtfs()
        await status_msg.edit_text(
            f"✅ *Sincronizzazione completata con successo!*\n"
            f"• Fermate: `{stops}`\n"
            f"• Corse: `{trips}`\n"
            f"• Passaggi orari: `{st}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("GTFS sync failed: %s", e)
        await status_msg.edit_text(f"❌ Errore durante la sincronizzazione: `{e}`", parse_mode="Markdown")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send broadcast message to all subscribed users (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    broadcast_text = " ".join(context.args) if context.args else ""
    if not broadcast_text:
        await update.effective_message.reply_text(
            "ℹ️ Inserisci il messaggio da inviare.\nEsempio: `/broadcast Avviso sciopero domani`",
            parse_mode="Markdown"
        )
        return

    user_ids = users_repo.get_subscribed_chat_ids()
    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *Avviso FCE Bot:*\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1

    await update.effective_message.reply_text(
        f"📤 Broadcast inviato:\n• Consegnati: `{sent}`\n• Falliti: `{failed}`",
        parse_mode="Markdown"
    )
