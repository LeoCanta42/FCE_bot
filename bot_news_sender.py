from telegram import Bot
from module.news_check.news import check_news
import schedule
import time
import asyncio

token=str(open("news_fcebot_token.txt","r").read()).strip()
bot=Bot(token=token)

#per ottenere chat id
#https://api.telegram.org/bot'bottoken'/sendMessage?chat_id=@'channel_name_public'&text=123
#nella risposta e' contenuto il chat id del canale, una volta preso si puo' reimpostare il canale a privato

channel_chat_id=str(open("./module/news_check/channel_id.txt","r").read()).strip()

def sender(bot:Bot,chat):
    inviare=check_news()
    if inviare:
        for news in inviare:
            asyncio.run(bot.send_message(chat_id=chat,text=news))
    else:
        return

if __name__=="__main__":
    schedule.every().hour.do(sender,bot,channel_chat_id)
    while True:
       schedule.run_pending()
       time.sleep(300) #5minuti
    
