from handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder
from module.retrieve_webdata import getdownload_urls
from module.timetables_operations.convert_excel import download_converted

def main():
    token = str(open('fcebot_token.txt','r').read()).strip()
    bot= ApplicationBuilder().token(token).build()
    
    bot.add_handlers(add_handlers())
    
    #aggiungere download orari ogni tot aggiornati e/o controllare siano diversi
    '''
    i=0
    for url in getdownload_urls(1): #littorina
        download_converted(url,"./module/timetables_operations/littorina/orario"+str(i)+".xlsx")
        i+=1
    i=0
    for url in getdownload_urls(2): #bus
        download_converted(url,"./module/timetables_operations/bus/orario"+str(i)+".xlsx")
        i+=1
    '''

    bot.run_polling()

if __name__ == '__main__':
    main()