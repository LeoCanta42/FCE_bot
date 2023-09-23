# FCE_bot
Before starting the bot, you will also have to install all the modules for python so "pip install -r requirements.txt".

To start the bot you will have to create a folder into "module" called "private" with these files:
- api_token_cloudconvert.txt (cloudconvert token to converte pdftables to excel)
- channel_id.txt (the telegram id of the channel for news)
- fcebot_token.txt (the telegram token of the primary bot)
- news_fcebot_token.txt (the telegram token of the news bot)
- my_userid.txt (your telegram id)

You have to start "create_users_db.py" and now you can use "scheduler.sh" to start your bots.

To stop your bots or restart them you can use "restarter.sh" passing parameters restart | stop | pause (this one is just for starting the pause bot, that sends a message alerting that the bot is in manteinance).
