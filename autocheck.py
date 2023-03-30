from module.check_new_urls import download_after_check
import telegram
from mainbot import token as tt
import asyncio

bot=telegram.Bot(token=tt)

def job():
    try:
        download_after_check()
    except Exception as e:
        print("Errore durante esecuzione job:\n"+str(e))

async def send():
    chat_ids=set()
    updates=await bot.get_updates()

    for update in updates:
        chat_id=update.message.chat.id
        chat_ids.add(chat_id)
    
    text="Bot in pausa, controllo nuovi orari ..."
    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id,text=text)

if __name__ == '__main__':
    asyncio.run(send())
    job()



'''
import schedule
import time

def checker():
   schedule.every(2).days.at("01:00").do(job)

   while True:
       schedule.run_pending()
       time.sleep(3000) #circa un'ora
'''