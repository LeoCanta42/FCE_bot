from module.handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder
from module.timetables_operations.extract_excel import locations_to_file
from module.timetables_operations.extract_excel import load #NO DB#
from time import sleep

#from module.timetables_operations.calculate_times import find_lines2 #see all lines| just for debug#

import os
# os.chdir("/home/pi/FCE_bot")

token = str(open('./module/private/fcebot_token.txt','r').read()).strip()
app= ApplicationBuilder().token(token).build()
app.add_handlers(add_handlers()) 

def mainbot() -> None : 
    #togliere commenti con #NO DB# per usare old find lines (no DB), anche da handlers_basic_commands
    #load("bus") #NO DB#
    #load("littorina") #NO DB#
    try:
        app.run_polling()
    except Exception as e:
        print(e)
        sleep(60)
        os.system('bash /home/leo/Desktop/FCE_bot/restarter.sh restart')

if __name__ == '__main__':
    mainbot()
    #find_lines2()
