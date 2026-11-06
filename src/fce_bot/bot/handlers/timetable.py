"""Interactive timetable wizard and transit query handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from fce_bot.core.models import TransportType, FilterType
from fce_bot.services.transit_service import transit_service
from fce_bot.bot.keyb import (
    main_menu_keyboard,
    transport_select_keyboard,
    stop_letters_keyboard,
    stops_pagination_keyboard,
    filter_type_keyboard,
    hours_keyboard,
    trip_results_keyboard,
)

logger = logging.getLogger(__name__)


async def viaggio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shortcut command: /viaggio <partenza> - <arrivo> [ora]."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.effective_message.reply_text(
            "ℹ️ *Uso del comando /viaggio:*\n"
            "`/viaggio Catania - Bronte 14:00`\n"
            "`/viaggio Randazzo Paternò`\n"
            "Oppure usa il pulsante *Cerca Linea / Orari* per la procedura guidata.",
            parse_mode="Markdown"
        )
        return

    # Call AI service entity extraction for robust parsing
    from fce_bot.services.ai_service import ai_service
    resp = ai_service.answer_query(text)
    await update.effective_message.reply_text(resp.answer, parse_mode="Markdown")


async def fermate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /fermate <query> to search stations."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.effective_message.reply_text(
            "ℹ️ Inserisci il nome della stazione da cercare:\n"
            "Esempio: `/fermate Milo` oppure `/fermate Randazzo`",
            parse_mode="Markdown"
        )
        return

    stops = transit_service.search_stops(query, limit=12)
    if not stops:
        await update.effective_message.reply_text(
            f"❌ Nessuna fermata trovata per '{query}'.",
            parse_mode="Markdown"
        )
        return

    lines = [f"🔍 *Fermate trovate per '{query}':*\n"]
    for s in stops:
        icons = []
        if s.has_metro:
            icons.append("🚇 Metro")
        if s.has_train:
            icons.append("🚆 Treno")
        if s.has_bus:
            icons.append("🚌 Bus")
        types_str = " | ".join(icons) or "Bus"
        lines.append(f"• *{s.stop_name}* ({types_str})")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


# ==========================================
# Wizard Callback Query Handlers
# ==========================================

async def wizard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle interactive timetable lookup button callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        return

    if data in ("wizard_start", "back_to_transport"):
        context.user_data.clear()
        await query.edit_message_text(
            "🧭 *Step 1/4 - Tipologia Trasporto*\n\n"
            "Scegli con quale mezzo desideri viaggiare:",
            reply_markup=transport_select_keyboard(),
            parse_mode="Markdown"
        )
        return

    if data.startswith("tt_"):
        tt_key = data.split("_")[1]
        tt_map = {
            "bus": TransportType.BUS,
            "train": TransportType.TRENO,
            "metro": TransportType.METRO,
            "any": TransportType.QUALSIASI,
        }
        selected_tt = tt_map.get(tt_key, TransportType.QUALSIASI)
        context.user_data["transport_type"] = selected_tt

        # Load all stops for selected mode (deduplicated)
        stops = transit_service.get_stops_by_type(selected_tt)
        context.user_data["available_stops"] = stops
        context.user_data["dep_page"] = 0
        context.user_data["dep_letter"] = None

        if len(stops) <= 12:
            await query.edit_message_text(
                f"📍 *Step 2/4 - Fermata di PARTENZA* ({selected_tt.value})\n\n"
                "Seleziona la fermata da cui vuoi partire:",
                reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=True, letter=None),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"📍 *Step 2/4 - Fermata di PARTENZA* ({selected_tt.value})\n\n"
                "Scegli l'iniziale della fermata di partenza:",
                reply_markup=stop_letters_keyboard(stops, is_departure=True),
                parse_mode="Markdown"
            )
        return

    # User picked an initial letter for departure
    if data.startswith("let_dep:"):
        letter = data.split(":")[1]
        context.user_data["dep_letter"] = letter
        context.user_data["dep_page"] = 0
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops

        await query.edit_message_text(
            f"📍 *Step 2/4 - Fermata di PARTENZA* (Lettera {letter})\n\n"
            "Seleziona la fermata da cui vuoi partire:",
            reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=True, letter=letter),
            parse_mode="Markdown"
        )
        return

    # User chose to see all departure stops
    if data == "all_dep":
        context.user_data["dep_letter"] = None
        context.user_data["dep_page"] = 0
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops

        await query.edit_message_text(
            "📍 *Step 2/4 - Fermata di PARTENZA*\n\n"
            "Seleziona la fermata da cui vuoi partire:",
            reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=True, letter=None),
            parse_mode="Markdown"
        )
        return

    # Return to letters keyboard for departure
    if data == "alpha_dep":
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        tt_val = context.user_data.get("transport_type", TransportType.QUALSIASI).value

        await query.edit_message_text(
            f"📍 *Step 2/4 - Fermata di PARTENZA* ({tt_val})\n\n"
            "Scegli l'iniziale della fermata di partenza:",
            reply_markup=stop_letters_keyboard(stops, is_departure=True),
            parse_mode="Markdown"
        )
        return

    # Pagination for departure stops
    if data.startswith("page_dep:"):
        parts = data.split(":")
        if len(parts) == 3:
            let_str = parts[1]
            page = int(parts[2])
            letter = None if let_str == "ALL" else let_str
        else:
            page = int(parts[1])
            letter = context.user_data.get("dep_letter")

        context.user_data["dep_page"] = page
        context.user_data["dep_letter"] = letter
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops

        try:
            await query.edit_message_reply_markup(
                reply_markup=stops_pagination_keyboard(stops, page=page, is_departure=True, letter=letter)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Page edit error: %s", e)
        return

    # Departure stop chosen
    if data.startswith("dep_stop:"):
        stop_id = data.split(":")[1]
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        selected_stop = next((s for s in stops if str(s.stop_id) == str(stop_id)), None)
        context.user_data["dep_stop"] = selected_stop

        context.user_data["arr_page"] = 0
        context.user_data["arr_letter"] = None
        dep_name = selected_stop.stop_name if selected_stop else "Scelta"

        if len(stops) <= 12:
            await query.edit_message_text(
                f"📍 Partenza: *{dep_name}*\n\n"
                "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
                "Seleziona la fermata di destinazione:",
                reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=False, letter=None),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"📍 Partenza: *{dep_name}*\n\n"
                "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
                "Scegli l'iniziale della fermata di destinazione:",
                reply_markup=stop_letters_keyboard(stops, is_departure=False),
                parse_mode="Markdown"
            )
        return

    # User picked an initial letter for arrival
    if data.startswith("let_arr:"):
        letter = data.split(":")[1]
        context.user_data["arr_letter"] = letter
        context.user_data["arr_page"] = 0
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        dep_stop = context.user_data.get("dep_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"

        await query.edit_message_text(
            f"📍 Partenza: *{dep_name}*\n\n"
            f"🏁 *Step 3/4 - Fermata di ARRIVO* (Lettera {letter})\n"
            "Seleziona la fermata di destinazione:",
            reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=False, letter=letter),
            parse_mode="Markdown"
        )
        return

    # User chose to see all arrival stops
    if data == "all_arr":
        context.user_data["arr_letter"] = None
        context.user_data["arr_page"] = 0
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        dep_stop = context.user_data.get("dep_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"

        await query.edit_message_text(
            f"📍 Partenza: *{dep_name}*\n\n"
            "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
            "Seleziona la fermata di destinazione:",
            reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=False, letter=None),
            parse_mode="Markdown"
        )
        return

    # Return to letters keyboard for arrival
    if data == "alpha_arr":
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        dep_stop = context.user_data.get("dep_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"

        await query.edit_message_text(
            f"📍 Partenza: *{dep_name}*\n\n"
            "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
            "Scegli l'iniziale della fermata di destinazione:",
            reply_markup=stop_letters_keyboard(stops, is_departure=False),
            parse_mode="Markdown"
        )
        return

    # Pagination for arrival stops
    if data.startswith("page_arr:"):
        parts = data.split(":")
        if len(parts) == 3:
            let_str = parts[1]
            page = int(parts[2])
            letter = None if let_str == "ALL" else let_str
        else:
            page = int(parts[1])
            letter = context.user_data.get("arr_letter")

        context.user_data["arr_page"] = page
        context.user_data["arr_letter"] = letter
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops

        try:
            await query.edit_message_reply_markup(
                reply_markup=stops_pagination_keyboard(stops, page=page, is_departure=False, letter=letter)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.debug("Page edit error: %s", e)
        return

    # Back to departure from arrival
    if data == "back_to_departure":
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        dep_letter = context.user_data.get("dep_letter")
        dep_page = context.user_data.get("dep_page", 0)

        if len(stops) <= 12:
            await query.edit_message_text(
                "📍 *Step 2/4 - Fermata di PARTENZA*\n\nSeleziona la fermata da cui vuoi partire:",
                reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=True, letter=None),
                parse_mode="Markdown"
            )
        elif dep_letter:
            await query.edit_message_text(
                f"📍 *Step 2/4 - Fermata di PARTENZA* (Lettera {dep_letter})\n\nSeleziona la fermata da cui vuoi partire:",
                reply_markup=stops_pagination_keyboard(stops, page=dep_page, is_departure=True, letter=dep_letter),
                parse_mode="Markdown"
            )
        else:
            tt_val = context.user_data.get("transport_type", TransportType.QUALSIASI).value
            await query.edit_message_text(
                f"📍 *Step 2/4 - Fermata di PARTENZA* ({tt_val})\n\nScegli l'iniziale della fermata di partenza:",
                reply_markup=stop_letters_keyboard(stops, is_departure=True),
                parse_mode="Markdown"
            )
        return

    # Arrival stop chosen
    if data.startswith("arr_stop:"):
        stop_id = data.split(":")[1]
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        selected_stop = next((s for s in stops if str(s.stop_id) == str(stop_id)), None)
        context.user_data["arr_stop"] = selected_stop

        dep_stop = context.user_data.get("dep_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"
        arr_name = selected_stop.stop_name if selected_stop else "Arrivo"

        await query.edit_message_text(
            f"📍 Partenza: *{dep_name}*\n"
            f"🏁 Destinazione: *{arr_name}*\n\n"
            "⏱ *Step 4/4 - Criterio di Ricerca*\n"
            "Come desideri impostare la ricerca?",
            reply_markup=filter_type_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Back to arrival from filter selection
    if data == "back_to_arrival":
        stops = context.user_data.get("available_stops") or transit_service.get_stops_by_type(
            context.user_data.get("transport_type", TransportType.QUALSIASI)
        )
        context.user_data["available_stops"] = stops
        arr_letter = context.user_data.get("arr_letter")
        arr_page = context.user_data.get("arr_page", 0)
        dep_stop = context.user_data.get("dep_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"

        if len(stops) <= 12:
            await query.edit_message_text(
                f"📍 Partenza: *{dep_name}*\n\n"
                "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
                "Seleziona la fermata di destinazione:",
                reply_markup=stops_pagination_keyboard(stops, page=0, is_departure=False, letter=None),
                parse_mode="Markdown"
            )
        elif arr_letter:
            await query.edit_message_text(
                f"📍 Partenza: *{dep_name}*\n\n"
                f"🏁 *Step 3/4 - Fermata di ARRIVO* (Lettera {arr_letter})\n"
                "Seleziona la fermata di destinazione:",
                reply_markup=stops_pagination_keyboard(stops, page=arr_page, is_departure=False, letter=arr_letter),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"📍 Partenza: *{dep_name}*\n\n"
                "🏁 *Step 3/4 - Fermata di ARRIVO*\n"
                "Scegli l'iniziale della fermata di destinazione:",
                reply_markup=stop_letters_keyboard(stops, is_departure=False),
                parse_mode="Markdown"
            )
        return

    # Filter criterion chosen
    if data.startswith("filt:"):
        filt_val = data.split(":")[1]
        context.user_data["filter_type"] = FilterType(filt_val)
        await query.edit_message_text(
            "🕒 *Scegli l'orario desiderato:*",
            reply_markup=hours_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Back to filters from hours
    if data == "back_to_filters":
        dep_stop = context.user_data.get("dep_stop")
        arr_stop = context.user_data.get("arr_stop")
        dep_name = dep_stop.stop_name if dep_stop else "Partenza"
        arr_name = arr_stop.stop_name if arr_stop else "Arrivo"

        await query.edit_message_text(
            f"📍 Partenza: *{dep_name}*\n"
            f"🏁 Destinazione: *{arr_name}*\n\n"
            "⏱ *Step 4/4 - Criterio di Ricerca*\n"
            "Come desideri impostare la ricerca?",
            reply_markup=filter_type_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Hour chosen: execute lookup
    if data.startswith("hour:"):
        chosen_hour = data.split(":")[1]
        dep_stop = context.user_data.get("dep_stop")
        arr_stop = context.user_data.get("arr_stop")
        ttype = context.user_data.get("transport_type", TransportType.QUALSIASI)
        ftype = context.user_data.get("filter_type", FilterType.DEPARTURE_AFTER)

        if not dep_stop or not arr_stop:
            await query.edit_message_text(
                "⚠️ Sessione scaduta. Ricomincia la ricerca dal menu.",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            return

        # Execute query
        itineraries = transit_service.find_trips(
            origin=dep_stop.stop_name,
            destination=arr_stop.stop_name,
            target_time=chosen_hour,
            transport_type=ttype,
            filter_type=ftype,
            limit=6
        )

        dep_name = dep_stop.stop_name
        arr_name = arr_stop.stop_name

        if not itineraries:
            await query.edit_message_text(
                f"❌ Nessuna corsa trovata tra *{dep_name}* e *{arr_name}* all'orario selezionato ({chosen_hour}).\n\n"
                "💡 Prova a selezionare un'ora differente o consulta i documenti PDF ufficiali.",
                reply_markup=trip_results_keyboard(),
                parse_mode="Markdown"
            )
            return

        result_header = (
            f"🚉 *Itinerari FCE trovati*\n"
            f"Da: *{dep_name}*\n"
            f"A: *{arr_name}*\n"
            f"Filtro: `{chosen_hour}`\n\n"
        )
        it_texts = [it.format_telegram() for it in itineraries]
        full_text = result_header + "\n".join(it_texts)

        # Telegram message limit check
        if len(full_text) > 4000:
            full_text = full_text[:3990] + "\n..."

        await query.edit_message_text(
            full_text,
            reply_markup=trip_results_keyboard(),
            parse_mode="Markdown"
        )
        return
