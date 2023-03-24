from module.handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder

token = str(open('fcebot_token.txt','r').read()).strip()
bot= ApplicationBuilder().token(token).build()
bot.add_handlers(add_handlers()) 

def mainbot():
    bot.run_polling()

if __name__ == '__main__':
    mainbot()