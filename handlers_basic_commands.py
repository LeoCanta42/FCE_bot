import logging
from telegram import Update
from telegram.ext import ContextTypes,CommandHandler,CallbackQueryHandler
from module.retrieve_webdata import getdownload_urls
from module.markups import general_markup,transport_markup,am_pm_markup,am_times_markup,pm_times_markup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def add_handlers(): #defining handlers
    handlers = [
        CommandHandler('start',welcome),
        CommandHandler('help',help),
        CommandHandler('contributors',contributors),
        CallbackQueryHandler(buttons)
        
    ]
    return handlers

async def buttons(message: Update, context: ContextTypes.DEFAULT_TYPE):
    query = message.callback_query

    await query.answer()
    if(query.data == "general"):
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Benvenuto nel bot per info sulla Ferrovia Circumetnea")
        await context.bot.edit_message_reply_markup(chat_id=message.effective_chat.id, message_id=message.effective_message.id, reply_markup=general_markup())

    elif(query.data == "1"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id) #elimino vecchia lista opzioni
        for i in getdownload_urls(2): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i) #invio orari
        await welcome(message,context) #rimetto lista opzioni
    elif(query.data == "2"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        for i in getdownload_urls(1): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i)
        await welcome(message,context)
    elif(query.data == "3"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        for i in getdownload_urls(0): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i)
        await welcome(message,context)
    elif(query.data == "choose_T"):
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli mattina/pomeriggio (AM/PM)")
        await context.bot.edit_message_reply_markup(chat_id=message.effective_chat.id, message_id=message.effective_message.id, reply_markup=am_pm_markup())
         
    elif(query.data == "am"):
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli per quale ora vuoi controllare")
        await context.bot.edit_message_reply_markup(chat_id=message.effective_chat.id, message_id=message.effective_message.id, reply_markup=am_times_markup())
    
    elif(query.data == "pm"):
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli per quale ora vuoi controllare")
        await context.bot.edit_message_reply_markup(chat_id=message.effective_chat.id, message_id=message.effective_message.id, reply_markup=pm_times_markup())

    elif (query.data in ["5:00","5:30","6:00","6:30","7:00","7:30","8:00","8:30","9:00","9:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00"]):
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli per quale mezzo vuoi controllare")
        await context.bot.edit_message_reply_markup(chat_id=message.effective_chat.id, message_id=message.effective_message.id, reply_markup=transport_markup())

async def contributors(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id,text=
"""@B4catr0n42, @SuperBomber

https://github.com/Leonardo0101/FCE_bot.git""")

async def welcome(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text="Benvenuto nel bot per info sulla Ferrovia Circumetnea",reply_markup=general_markup())

async def help(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text=
"""Orario bus: link pdf orario bus
Orario treni: link pdf orario treni
Orario metro: link pdf orario metro 
Controlla orario vicino: calcola l'orario piu' vicino a quello desiderato per andare da/a """)