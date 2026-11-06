"""Tests for Telegram bot handlers, keyboards, and wizard flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, CallbackQuery
from fce_bot.core.models import TransportType, FilterType, Stop
from fce_bot.bot.keyb import (
    main_menu_keyboard,
    transport_select_keyboard,
    stop_letters_keyboard,
    stops_pagination_keyboard,
    filter_type_keyboard,
    hours_keyboard,
    trip_results_keyboard,
    subscription_manage_keyboard,
)
from fce_bot.bot.handlers.start import start_command, help_command, HELP_TEXT
from fce_bot.bot.handlers.timetable import wizard_callback
from fce_bot.bot.handlers.news import (
    news_sub_menu_callback,
    sub_enable_callback,
    sub_disable_callback,
)
from fce_bot.data.users_repo import UsersRepository


def test_help_text_markdown_syntax():
    """Verify HELP_TEXT has balanced markdown formatting and developer attribution."""
    assert "`chat_id`" in HELP_TEXT
    assert "chat_id " not in HELP_TEXT
    # Check developer and repository references
    assert "LeoCanta42" in HELP_TEXT
    assert "https://github.com/LeoCanta42/FCE_bot" in HELP_TEXT
    # Check that italic/bold markers don't leave hanging tags
    assert HELP_TEXT.count("*") % 2 == 0


def test_stop_letters_keyboard():
    """Verify alphabetical stop letter keyboard extraction and layout."""
    mock_stops = [
        Stop(stop_id="1", stop_name="Acireale", normalized_name="acireale"),
        Stop(stop_id="2", stop_name="Borgo", normalized_name="borgo"),
        Stop(stop_id="3", stop_name="Catania", normalized_name="catania"),
        Stop(stop_id="4", stop_name="Paterno'", normalized_name="paterno"),
        Stop(stop_id="5", stop_name="Randazzo", normalized_name="randazzo"),
    ]
    markup = stop_letters_keyboard(mock_stops, is_departure=True)
    buttons = [btn for row in markup.inline_keyboard for btn in row]
    cb_data = [btn.callback_data for btn in buttons]

    assert "let_dep:A" in cb_data
    assert "let_dep:B" in cb_data
    assert "let_dep:C" in cb_data
    assert "let_dep:P" in cb_data
    assert "let_dep:R" in cb_data
    assert "all_dep" in cb_data
    assert "wizard_start" in cb_data


def test_stops_pagination_keyboard_with_letter_filter():
    """Verify filtering stops by initial letter."""
    mock_stops = [
        Stop(stop_id="1", stop_name="Paterno'", normalized_name="paterno"),
        Stop(stop_id="2", stop_name="Piano Tavola", normalized_name="piano tavola"),
        Stop(stop_id="3", stop_name="Pozzillo", normalized_name="pozzillo"),
        Stop(stop_id="4", stop_name="Randazzo", normalized_name="randazzo"),
    ]
    # Filter with letter P
    markup = stops_pagination_keyboard(mock_stops, page=0, is_departure=True, letter="P")
    buttons = [btn for row in markup.inline_keyboard for btn in row]
    btn_texts = [btn.text for btn in buttons]

    assert "Paterno'" in btn_texts
    assert "Piano Tavola" in btn_texts
    assert "Pozzillo" in btn_texts
    assert "Randazzo" not in btn_texts


@pytest.mark.anyio
async def test_help_command_callback_query():
    """Verify help_command edits message in-place without spawning duplicates."""
    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    query.data = "help_info"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    context = MagicMock()

    await help_command(update, context)
    query.answer.assert_awaited_once()
    query.edit_message_text.assert_awaited_once()
    args, kwargs = query.edit_message_text.call_args
    assert "Guida all'uso" in args[0]
    assert kwargs.get("parse_mode") == "Markdown"


@pytest.mark.anyio
async def test_start_command_callback_query():
    """Verify start_command edits message in-place on menu_main callback."""
    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    query.data = "menu_main"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    context = MagicMock()
    context.user_data = {}

    await start_command(update, context)
    query.answer.assert_awaited_once()
    query.edit_message_text.assert_awaited_once()
    args, kwargs = query.edit_message_text.call_args
    assert "Benvenuto su FCE Circumetnea Bot" in args[0]


@pytest.mark.anyio
async def test_wizard_full_flow():
    """Verify complete end-to-end interactive timetable wizard navigation."""
    context = MagicMock()
    context.user_data = {}

    # 1. Start wizard
    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    query.data = "wizard_start"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query

    await wizard_callback(update, context)
    assert "Step 1/4" in query.edit_message_text.call_args[0][0]

    # 2. Select Train mode
    query.data = "tt_train"
    await wizard_callback(update, context)
    assert context.user_data["transport_type"] == TransportType.TRENO
    assert len(context.user_data["available_stops"]) > 0

    # 3. Filter departure by letter P
    query.data = "let_dep:P"
    await wizard_callback(update, context)
    assert context.user_data["dep_letter"] == "P"

    # 4. Pick departure stop
    p_stops = [s for s in context.user_data["available_stops"] if s.stop_name.upper().startswith("P")]
    paterno_stop = next(s for s in p_stops if "PATERNO" in s.stop_name.upper())
    query.data = f"dep_stop:{paterno_stop.stop_id}"
    await wizard_callback(update, context)
    assert context.user_data["dep_stop"].stop_id == paterno_stop.stop_id

    # 5. Filter arrival by letter R
    query.data = "let_arr:R"
    await wizard_callback(update, context)
    assert context.user_data["arr_letter"] == "R"

    # 6. Pick arrival stop
    r_stops = [s for s in context.user_data["available_stops"] if s.stop_name.upper().startswith("R")]
    randazzo_stop = next(s for s in r_stops if "RANDAZZO" in s.stop_name.upper())
    query.data = f"arr_stop:{randazzo_stop.stop_id}"
    await wizard_callback(update, context)
    assert context.user_data["arr_stop"].stop_id == randazzo_stop.stop_id

    # 7. Test back_to_arrival navigation
    query.data = "back_to_arrival"
    await wizard_callback(update, context)
    assert "Fermata di ARRIVO" in query.edit_message_text.call_args[0][0]

    # Re-select arrival
    query.data = f"arr_stop:{randazzo_stop.stop_id}"
    await wizard_callback(update, context)

    # 8. Select filter criterion
    query.data = f"filt:{FilterType.DEPARTURE_AFTER.value}"
    await wizard_callback(update, context)
    assert "Scegli l'orario" in query.edit_message_text.call_args[0][0]

    # 9. Test back_to_filters navigation
    query.data = "back_to_filters"
    await wizard_callback(update, context)
    assert "Criterio di Ricerca" in query.edit_message_text.call_args[0][0]

    # Re-select filter
    query.data = f"filt:{FilterType.DEPARTURE_AFTER.value}"
    await wizard_callback(update, context)

    # 10. Select hour
    query.data = "hour:08:00"
    await wizard_callback(update, context)
    assert "Itinerari FCE trovati" in query.edit_message_text.call_args[0][0]


@pytest.mark.anyio
async def test_manual_news_subscription_flow():
    """Verify manual opt-in and opt-out buttons for news broadcast alerts."""
    repo = UsersRepository()
    test_cid = 888777666
    repo.delete_user(test_cid)

    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    chat = MagicMock()
    chat.id = test_cid
    update.effective_chat = chat
    context = MagicMock()

    # 1. Open subscription preferences menu
    query.data = "news_sub_menu"
    await news_sub_menu_callback(update, context)
    assert repo.is_user_subscribed(test_cid) is False
    assert "Non iscritto" in query.edit_message_text.call_args[0][0]

    # 2. Click button to manually subscribe
    query.data = "sub_enable"
    await sub_enable_callback(update, context)
    assert repo.is_user_subscribed(test_cid) is True
    assert "Iscrizione completata con successo" in query.edit_message_text.call_args[0][0]

    # 3. Click button to manually unsubscribe
    query.data = "sub_disable"
    await sub_disable_callback(update, context)
    assert repo.is_user_subscribed(test_cid) is False
    assert "Notifiche disattivate" in query.edit_message_text.call_args[0][0]

    # Clean up
    repo.delete_user(test_cid)


@pytest.mark.anyio
async def test_bot_post_init_and_commands():
    """Verify bot application factory, public commands list, and post_init registration."""
    from fce_bot.bot.bot_app import create_bot_application, post_init, PUBLIC_BOT_COMMANDS

    app = create_bot_application()
    assert app is not None

    # Check commands list
    cmd_names = [c.command for c in PUBLIC_BOT_COMMANDS]
    assert "start" in cmd_names
    assert "viaggio" in cmd_names
    assert "fermate" in cmd_names
    assert "news" in cmd_names
    assert "iscriviti" in cmd_names
    assert "disiscriviti" in cmd_names
    assert "documenti" in cmd_names
    assert "help" in cmd_names
    assert "privacy" in cmd_names
    assert "cancella" in cmd_names
    assert "chat_id" in cmd_names

    # Admin commands should not be in public autocomplete
    assert "stats" not in cmd_names
    assert "broadcast" not in cmd_names

    # Mock app for post_init with real-like token
    mock_app = MagicMock()
    mock_app.bot.token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    mock_app.bot.set_my_commands = AsyncMock()

    await post_init(mock_app)
    mock_app.bot.set_my_commands.assert_awaited_once_with(PUBLIC_BOT_COMMANDS)

    # Post init with dummy token should safely return without network call
    mock_dummy_app = MagicMock()
    mock_dummy_app.bot.token = "0000000000:DUMMY"
    mock_dummy_app.bot.set_my_commands = AsyncMock()
    await post_init(mock_dummy_app)
    mock_dummy_app.bot.set_my_commands.assert_not_called()

