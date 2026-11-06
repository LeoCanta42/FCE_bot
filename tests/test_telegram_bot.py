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

    # Verify MessageHandler only matches private 1-to-1 chats and rejects channels/groups
    from telegram.ext import MessageHandler
    from telegram import Message as TgMessage, Chat as TgChat
    msg_handlers = [h for h in app.handlers[0] if isinstance(h, MessageHandler)]
    assert len(msg_handlers) == 1
    u_channel = Update(999, channel_post=TgMessage(999, None, TgChat(-100123, "channel"), text="prova"))
    assert msg_handlers[0].filters.check_update(u_channel) is False
    u_group = Update(999, message=TgMessage(999, None, TgChat(-100456, "supergroup"), text="prova"))
    assert msg_handlers[0].filters.check_update(u_group) is False
    u_priv = Update(999, message=TgMessage(999, None, TgChat(12345, "private"), text="prova"))
    assert msg_handlers[0].filters.check_update(u_priv) is True

    # Post init with dummy token should safely return without network call
    mock_dummy_app = MagicMock()
    mock_dummy_app.bot.token = "0000000000:DUMMY"
    mock_dummy_app.bot.set_my_commands = AsyncMock()
    await post_init(mock_dummy_app)
    mock_dummy_app.bot.set_my_commands.assert_not_called()


@pytest.mark.anyio
async def test_channel_and_group_messages_are_strictly_ignored():
    """Verify bot never responds to messages from channels, groups, or channel posts."""
    from fce_bot.bot.handlers.ai_chat import ai_message_handler
    from fce_bot.bot.handlers.start import start_command

    # 1. Channel post update
    channel_update = MagicMock(spec=Update)
    channel_update.channel_post = MagicMock()
    channel_update.callback_query = None
    channel_chat = MagicMock()
    channel_chat.type = "channel"
    channel_update.effective_chat = channel_chat
    channel_msg = MagicMock()
    channel_msg.text = "A che ora passa la metro?"
    channel_msg.reply_text = AsyncMock()
    channel_update.effective_message = channel_msg
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()

    await ai_message_handler(channel_update, context)
    channel_msg.reply_text.assert_not_called()
    context.bot.send_chat_action.assert_not_called()

    # 2. Supergroup / Group chat message
    group_update = MagicMock(spec=Update)
    group_update.channel_post = None
    group_chat = MagicMock()
    group_chat.type = "supergroup"
    group_update.effective_chat = group_chat
    group_msg = MagicMock()
    group_msg.text = "C'è un treno per Randazzo?"
    group_msg.reply_text = AsyncMock()
    group_update.effective_message = group_msg

    await ai_message_handler(group_update, context)
    group_msg.reply_text.assert_not_called()
    context.bot.send_chat_action.assert_not_called()

    # 3. Start command on channel
    await start_command(channel_update, context)
    channel_msg.reply_text.assert_not_called()


@pytest.mark.anyio
async def test_ai_permission_flow_and_admin_commands():
    """Verify AI permission checking, unauthorized message blocking, and admin allow/disallow."""
    from fce_bot.data.users_repo import UsersRepository
    from fce_bot.bot.handlers.ai_chat import ai_message_handler
    from fce_bot.bot.handlers.admin import allow_ai_command, disallow_ai_command, list_ai_command
    from fce_bot.config import settings

    repo = UsersRepository()
    test_user_id = 777666555
    repo.delete_user(test_user_id)

    # Initially unauthorized
    assert repo.is_ai_allowed(test_user_id) is False

    # Unauthorized user sending question gets restricted notice and is not processed
    update = MagicMock(spec=Update)
    update.channel_post = None
    chat = MagicMock()
    chat.type = "private"
    chat.id = test_user_id
    update.effective_chat = chat
    msg = MagicMock()
    msg.text = "A che ora c'è la metro?"
    msg.reply_text = AsyncMock()
    update.effective_message = msg
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()

    await ai_message_handler(update, context)
    msg.reply_text.assert_awaited_once()
    assert "ad accesso limitato" in msg.reply_text.call_args[0][0]
    assert str(test_user_id) in msg.reply_text.call_args[0][0]

    # Non-admin trying to allow AI is denied
    admin_update = MagicMock(spec=Update)
    admin_user = MagicMock()
    admin_user.id = 999999999
    admin_update.effective_user = admin_user
    admin_msg = MagicMock()
    admin_msg.reply_text = AsyncMock()
    admin_update.effective_message = admin_msg
    admin_context = MagicMock()
    admin_context.args = [str(test_user_id)]

    await allow_ai_command(admin_update, admin_context)
    admin_msg.reply_text.assert_awaited_once_with("⛔ Comando riservato agli amministratori.")

    # Mock admin in settings.admin_user_ids
    original_admins = settings.ADMIN_USER_IDS_RAW
    try:
        settings.ADMIN_USER_IDS_RAW = str(admin_user.id)
        assert admin_user.id in settings.admin_user_ids
        # Admin is automatically allowed AI
        assert repo.is_ai_allowed(admin_user.id) is True

        # Admin executes /allow_ai <chat_id>
        admin_msg.reply_text.reset_mock()
        await allow_ai_command(admin_update, admin_context)
        assert repo.is_ai_allowed(test_user_id) is True
        assert str(test_user_id) in repo.get_ai_allowed_chat_ids()
        assert "Accesso AI *abilitato*" in admin_msg.reply_text.call_args[0][0]

        # Admin checks /list_ai
        admin_msg.reply_text.reset_mock()
        await list_ai_command(admin_update, admin_context)
        assert str(test_user_id) in admin_msg.reply_text.call_args[0][0]

        # Now test_user sends message again -> passes permission check and typing action is triggered
        msg.reply_text.reset_mock()
        with pytest.MonkeyPatch().context() as mp:
            from fce_bot.core.models import AIQueryResponse
            from fce_bot.services.ai_service import ai_service
            mp.setattr(ai_service, "answer_query", lambda q: AIQueryResponse(answer="Ecco la risposta AI", itineraries_count=1))
            await ai_message_handler(update, context)
            context.bot.send_chat_action.assert_awaited_once_with(chat_id=test_user_id, action="typing")
            assert "Ecco la risposta AI" in msg.reply_text.call_args[0][0]

        # Admin executes /disallow_ai <chat_id>
        admin_msg.reply_text.reset_mock()
        await disallow_ai_command(admin_update, admin_context)
        assert repo.is_ai_allowed(test_user_id) is False
        assert "Accesso AI *revocato*" in admin_msg.reply_text.call_args[0][0]
    finally:
        settings.ADMIN_USER_IDS_RAW = original_admins
        repo.delete_user(test_user_id)


@pytest.mark.anyio
async def test_admin_username_management_and_panel_flow():
    """Verify admin can search/view user by username, toggle AI & notifications, delete record, and use admin panel."""
    from fce_bot.data.users_repo import UsersRepository
    from fce_bot.bot.handlers.admin import (
        admin_command,
        admin_callback,
        user_command,
        users_command,
        allow_ai_command,
        disallow_ai_command,
        sub_user_command,
        unsub_user_command,
        delete_user_command,
    )
    from fce_bot.bot.handlers.start import start_command
    from fce_bot.bot.handlers.ai_chat import ai_message_handler
    from fce_bot.config import settings

    repo = UsersRepository()
    target_id = 666555444
    target_username = "mario_fce_test"
    admin_id = 111222333
    repo.delete_user(target_id)

    # Register target user with username
    repo.register_or_update(chat_id=target_id, username=target_username, first_name="Mario", is_subscribed=False)

    original_admins = settings.ADMIN_USER_IDS_RAW
    try:
        settings.ADMIN_USER_IDS_RAW = str(admin_id)

        # 1. Verify /start shows 'Pannello Admin' button ONLY for admin
        admin_start_upd = MagicMock(spec=Update)
        admin_start_upd.callback_query = None
        admin_chat = MagicMock()
        admin_chat.type = "private"
        admin_chat.id = admin_id
        admin_start_upd.effective_chat = admin_chat
        admin_usr = MagicMock()
        admin_usr.id = admin_id
        admin_usr.username = "admin_boss"
        admin_usr.first_name = "Admin"
        admin_start_upd.effective_user = admin_usr
        admin_msg = MagicMock()
        admin_msg.reply_text = AsyncMock()
        admin_start_upd.effective_message = admin_msg
        ctx = MagicMock()
        ctx.user_data = {}
        ctx.bot.send_message = AsyncMock()

        await start_command(admin_start_upd, ctx)
        admin_kb = admin_msg.reply_text.call_args.kwargs["reply_markup"]
        admin_cb_data = [btn.callback_data for row in admin_kb.inline_keyboard for btn in row]
        assert "adm_menu" in admin_cb_data

        # Regular user should NOT see 'adm_menu'
        user_start_upd = MagicMock(spec=Update)
        user_start_upd.callback_query = None
        u_chat = MagicMock()
        u_chat.type = "private"
        u_chat.id = target_id
        user_start_upd.effective_chat = u_chat
        u_usr = MagicMock()
        u_usr.id = target_id
        u_usr.username = target_username
        u_usr.first_name = "Mario"
        user_start_upd.effective_user = u_usr
        u_msg = MagicMock()
        u_msg.reply_text = AsyncMock()
        user_start_upd.effective_message = u_msg
        await start_command(user_start_upd, ctx)
        u_kb = u_msg.reply_text.call_args.kwargs["reply_markup"]
        u_cb_data = [btn.callback_data for row in u_kb.inline_keyboard for btn in row]
        assert "adm_menu" not in u_cb_data

        # 2. Admin looks up user by @username via /user @mario_fce_test
        admin_msg.reply_text.reset_mock()
        ctx.args = [f"@{target_username}"]
        await user_command(admin_start_upd, ctx)
        card_text = admin_msg.reply_text.call_args[0][0]
        assert str(target_id) in card_text
        assert f"@{target_username}" in card_text

        # 3. Admin enables & disables AI by @username
        admin_msg.reply_text.reset_mock()
        ctx.args = [f"@{target_username}"]
        await allow_ai_command(admin_start_upd, ctx)
        assert repo.is_ai_allowed(target_id) is True

        ctx.args = [target_username]  # without @ also works
        await disallow_ai_command(admin_start_upd, ctx)
        assert repo.is_ai_allowed(target_id) is False

        # 4. Admin enables & disables notification subscription by @username
        ctx.args = [f"@{target_username}"]
        await sub_user_command(admin_start_upd, ctx)
        assert repo.is_user_subscribed(target_id) is True

        await unsub_user_command(admin_start_upd, ctx)
        assert repo.is_user_subscribed(target_id) is False

        # 5. Interactive Admin Panel callbacks (toggle AI, toggle sub, search prompt, delete user)
        cb_update = MagicMock(spec=Update)
        cb_query = MagicMock(spec=CallbackQuery)
        cb_query.answer = AsyncMock()
        cb_query.edit_message_text = AsyncMock()
        cb_update.callback_query = cb_query
        cb_update.effective_user = admin_usr
        cb_update.effective_chat = admin_chat

        # Open admin menu
        cb_query.data = "adm_menu"
        await admin_callback(cb_update, ctx)
        assert "Pannello di Controllo Amministratore" in cb_query.edit_message_text.call_args[0][0]

        # Open users list
        cb_query.data = "adm_users:all:0"
        await admin_callback(cb_update, ctx)
        assert "Gestione Utenti" in cb_query.edit_message_text.call_args[0][0]

        # Toggle AI ON via inline button
        cb_query.data = f"adm_u_ai:{target_id}:1:all:0"
        await admin_callback(cb_update, ctx)
        assert repo.is_ai_allowed(target_id) is True

        # Toggle Notifications ON via inline button
        cb_query.data = f"adm_u_sub:{target_id}:1:all:0"
        await admin_callback(cb_update, ctx)
        assert repo.is_user_subscribed(target_id) is True

        # Interactive search prompt -> admin sends username in chat
        cb_query.data = "adm_search_prompt"
        await admin_callback(cb_update, ctx)
        assert ctx.user_data.get("admin_state") == "awaiting_user_search"

        admin_msg.reply_text.reset_mock()
        admin_msg.text = f"@{target_username}"
        admin_start_upd.channel_post = None
        await ai_message_handler(admin_start_upd, ctx)
        assert ctx.user_data.get("admin_state") is None
        assert "Scheda Utente FCE Bot" in admin_msg.reply_text.call_args[0][0]

        # Interactive Broadcast prompt -> admin sends message in chat
        cb_query.data = "adm_broadcast_prompt"
        await admin_callback(cb_update, ctx)
        assert ctx.user_data.get("admin_state") == "awaiting_broadcast"

        admin_msg.reply_text.reset_mock()
        admin_msg.text = "Comunicazione di test agli iscritti"
        await ai_message_handler(admin_start_upd, ctx)
        assert "Broadcast Inviato con Successo" in admin_msg.reply_text.call_args[0][0]

        # Delete user record via inline button confirmation
        cb_query.data = f"adm_u_del_ask:{target_id}:all:0"
        await admin_callback(cb_update, ctx)
        assert "Conferma Eliminazione Utente" in cb_query.edit_message_text.call_args[0][0]

        cb_query.data = f"adm_u_del_ok:{target_id}:all:0"
        await admin_callback(cb_update, ctx)
        assert repo.get_user(target_id) is None

        # Re-register and test /delete_user @username command
        repo.register_or_update(chat_id=target_id, username=target_username, first_name="Mario")
        assert repo.get_user(target_username) is not None
        ctx.args = [f"@{target_username}"]
        await delete_user_command(admin_start_upd, ctx)
        assert repo.get_user(target_id) is None

        # 6. Verify track_user_interaction saves any incoming private user with is_subscribed=0 and ai_allowed=0
        from fce_bot.bot.bot_app import track_user_interaction
        new_uid = 555444333
        repo.delete_user(new_uid)
        auto_upd = MagicMock(spec=Update)
        auto_upd.channel_post = None
        auto_chat = MagicMock()
        auto_chat.type = "private"
        auto_chat.id = new_uid
        auto_upd.effective_chat = auto_chat
        auto_user = MagicMock()
        auto_user.id = new_uid
        auto_user.username = "nuovo_utente_fce"
        auto_user.first_name = "Luca"
        auto_upd.effective_user = auto_user
        auto_msg = MagicMock()
        auto_msg.text = "/viaggio Catania Bronte"
        auto_upd.effective_message = auto_msg

        await track_user_interaction(auto_upd, ctx)
        saved_u = repo.get_user("nuovo_utente_fce")
        assert saved_u is not None
        assert saved_u["chat_id"] == str(new_uid)
        assert saved_u["username"] == "nuovo_utente_fce"
        assert saved_u["first_name"] == "Luca"
        assert saved_u["is_subscribed"] == 0
        assert saved_u["ai_allowed"] == 0
        repo.delete_user(new_uid)
    finally:
        settings.ADMIN_USER_IDS_RAW = original_admins
        repo.delete_user(target_id)
        repo.delete_user(admin_id)




