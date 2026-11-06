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
        f"🤖 *Utenti con accesso AI:* `{stats['ai_allowed_users']}`\n"
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


async def allow_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Authorize a Telegram chat ID to use the AI trip assistant (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    if not context.args:
        await update.effective_message.reply_text(
            "ℹ️ Inserisci il `chat_id` dell'utente da abilitare all'AI.\n"
            "Esempio: `/allow_ai 123456789`",
            parse_mode="Markdown"
        )
        return

    target_chat_id = context.args[0].strip()
    users_repo.set_ai_allowed(target_chat_id, True)

    # Attempt to notify the user if possible
    notified = False
    try:
        await context.bot.send_message(
            chat_id=target_chat_id,
            text=(
                "🎉 *Accesso AI Abilitato!*\n\n"
                "L'amministratore ha autorizzato il tuo account all'uso dell'Assistente AI FCE.\n"
                "Da adesso puoi scrivergli liberamente in chat per chiedere orari, coincidenze e percorsi!"
            ),
            parse_mode="Markdown"
        )
        notified = True
    except Exception as exc:
        logger.debug("Could not notify user %s of AI activation: %s", target_chat_id, exc)

    msg = f"✅ Accesso AI *abilitato* per la chat ID: `{target_chat_id}`"
    if notified:
        msg += "\n🔔 L'utente è stato notificato con successo in chat."
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


async def disallow_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Revoke AI trip assistant access for a Telegram chat ID (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    if not context.args:
        await update.effective_message.reply_text(
            "ℹ️ Inserisci il `chat_id` dell'utente a cui revocare l'accesso AI.\n"
            "Esempio: `/disallow_ai 123456789`",
            parse_mode="Markdown"
        )
        return

    target_chat_id = context.args[0].strip()
    users_repo.set_ai_allowed(target_chat_id, False)

    await update.effective_message.reply_text(
        f"🚫 Accesso AI *revocato* per la chat ID: `{target_chat_id}`",
        parse_mode="Markdown"
    )


async def list_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all chat IDs authorized to use the AI assistant (Admin only)."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.effective_message.reply_text("⛔ Comando riservato agli amministratori.")
        return

    allowed_ids = users_repo.get_ai_allowed_chat_ids()
    admin_ids = [str(aid) for aid in settings.admin_user_ids]

    lines = ["🤖 *Utenti con Accesso AI Abilitato:*", ""]
    if admin_ids:
        lines.append("👑 *Amministratori (abilitati automaticamente):*")
        for aid in admin_ids:
            lines.append(f"• `{aid}`")
        lines.append("")

    lines.append(f"👥 *Utenti whitelisted:* `{len(allowed_ids)}`")
    if allowed_ids:
        for cid in allowed_ids:
            lines.append(f"• `{cid}`")
    else:
        lines.append("_(Nessun utente esterno attualmente abilitato)_")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")

