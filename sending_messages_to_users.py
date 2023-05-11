from telegram import Bot
import asyncio
import sqlite3 as sql

# import os
# os.chdir("/home/pi/FCE_bot")

token=str(open("./module/private/fcebot_token.txt","r").read()).strip()
bot=Bot(token=token)
tosend='''

'''

with sql.connect("users.db") as connection:
    cursor=connection.cursor()
    chat_ids=cursor.execute("select chatid from Users").fetchall()

for chat in chat_ids:
    asyncio.run(bot.send_message(chat_id=chat[0],text=tosend,parse_mode='Markdown')) 