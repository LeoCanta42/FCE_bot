from telegram import Bot
from module.news_check.news import check_news,indexes
import requests
import schedule
import time
import asyncio

# import os
# os.chdir("/home/pi/FCE_bot")

token=str(open("./module/private/news_fcebot_token.txt","r").read()).strip()
bot=Bot(token=token)

#per ottenere chat id
#https://api.telegram.org/bot'bottoken'/sendMessage?chat_id=@'channel_name_public'&text=123
#nella risposta e' contenuto il chat id del canale, una volta preso si puo' reimpostare il canale a privato

channel_chat_id=str(open("./module/private/channel_id.txt","r").read()).strip()

async def sender(bot:Bot,chat:str) -> None:
    inviare=check_news()
    try:
        if inviare:
            for news in inviare:
                await bot.send_message(chat_id=chat,text=news,parse_mode='Markdown')
            
            new_page=requests.get("https://www.circumetnea.it/category/news/")
            ind=indexes(new_page)
            new_page=new_page.text[ind[0]:ind[1]]
            with open("./module/news_check/updated_news.html","w") as f: #aggiorno la pagina con le nuove notizie
                f.write(new_page)
        else:
            return
    except Exception as e:
        print("Errore durante l'esecuzione della query: {}".format(e))
        return

def run_sender(bot:Bot,chat:str) -> None:
    asyncio.run(sender(bot,chat))

if __name__=="__main__":
    schedule.every().hour.do(run_sender,bot,channel_chat_id)
    while True:
       schedule.run_pending()
       time.sleep(300) #5 min
    
