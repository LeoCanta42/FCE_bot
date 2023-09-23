from module.handlers_basic_commands import add_handlers
from telegram.ext import ApplicationBuilder

from time import sleep

#from module.timetables_operations.calculate_times import find_lines2 #see all lines| just for debug#

import os
# os.chdir("/home/pi/FCE_bot")

token = str(open('~/FCE_bot/module/private/fcebot_token.txt','r').read()).strip()
app= ApplicationBuilder().token(token).build()
app.add_handlers(add_handlers()) 

def mainbot() -> None : 
    try:
        app.run_polling()
    except Exception as e:
        print(e)
        sleep(30)
        os.system('bash ~/FCE_bot/restarter.sh restart &')

if __name__ == '__main__':
    mainbot()
