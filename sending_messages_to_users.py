from telegram import Bot
import asyncio
import sqlite3 as sql

from module.timetables_operations import db
from module.timetables_operations.extract_excel import load, locations_to_file
# import os
# os.chdir("/home/pi/FCE_bot")

token=str(open("~/FCE_bot/module/private/fcebot_token.txt","r").read()).strip()
bot=Bot(token=token)
tosend='''

'''
def send():
    with sql.connect("users.db") as connection:
        cursor=connection.cursor()
        chat_ids=cursor.execute("select chatid from Users").fetchall()

    for chat in chat_ids:
        asyncio.run(bot.send_message(chat_id=chat[0],text=tosend,parse_mode='Markdown')) 

if __name__ == "__main__":
    send()