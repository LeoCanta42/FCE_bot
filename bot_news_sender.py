from telegram import Bot
from module.news_check.news import check_news
import schedule
import time
import asyncio

token=str(open("./module/private/news_fcebot_token.txt","r").read()).strip()
bot=Bot(token=token)

#per ottenere chat id
#https://api.telegram.org/bot'bottoken'/sendMessage?chat_id=@'channel_name_public'&text=123
#nella risposta e' contenuto il chat id del canale, una volta preso si puo' reimpostare il canale a privato

channel_chat_id=str(open("./module/private/channel_id.txt","r").read()).strip()

async def sender(bot:Bot,chat:str) -> None:
    inviare=check_news()
    if inviare:
        for news in inviare:
            await bot.send_message(chat_id=chat,text=news,parse_mode='Markdown')
    else:
        return

def run_sender(bot:Bot,chat:str) -> None:
    asyncio.run(sender(bot,chat))

if __name__=="__main__":
    schedule.every().hour.do(run_sender,bot,channel_chat_id)
    while True:
       schedule.run_pending()
       time.sleep(300) #5minuti
    
