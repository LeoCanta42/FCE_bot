from module.handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder
from module.timetables_operations.extract_excel import locations_to_file,load

token = str(open('fcebot_token.txt','r').read()).strip()
app= ApplicationBuilder().token(token).build()
app.add_handlers(add_handlers()) 

def mainbot():    
    app.run_polling()

if __name__ == '__main__':
    mainbot()
