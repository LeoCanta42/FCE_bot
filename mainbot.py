from module.handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder
#from module.timetables_operations.extract_excel import load #NO DB#

#token = str(open('fcebot_token.txt','r').read()).strip()
token = str(open('news_fcebot_token.txt','r').read()).strip()
app= ApplicationBuilder().token(token).build()
app.add_handlers(add_handlers()) 

def mainbot():    
    #togliere commenti con #NO DB# per usare old find lines (no DB), anche da handlers_basic_commands
    #load("bus") #NO DB#
    #load("littorina") #NO DB#
    app.run_polling()

if __name__ == '__main__':
    mainbot()
