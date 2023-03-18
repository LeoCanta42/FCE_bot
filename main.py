from handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder
from module.retrieve_webdata import download_package

def main():
    token = str(open('fcebot_token.txt','r').read()).strip()
    bot= ApplicationBuilder().token(token).build()
    
    bot.add_handlers(add_handlers())
    
    #aggiungere download orari ogni tot aggiornati, una volta in modo che si possono usare quelli
    '''
    download_package(2,"./module/timetables_operations/bus_orario")
    download_package(1,"./module/timetables_operations/littorina_orario")
    '''
    bot.run_polling()

if __name__ == '__main__':
    main()