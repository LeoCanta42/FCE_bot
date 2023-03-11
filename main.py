from handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder

def main():
    token = str(open('fcebot_token.txt','r').read()).strip()
    bot= ApplicationBuilder().token(token).build()
    
    bot.add_handlers(add_handlers())
    
    #aggiungere download orari ogni tot aggiornati, una volta in modo che si possono usare o inviare direttamente quelli

    bot.run_polling()

if __name__ == '__main__':
    main()