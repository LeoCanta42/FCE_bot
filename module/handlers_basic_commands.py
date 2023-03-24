import logging
from telegram import Update
from telegram.ext import ContextTypes,CommandHandler,CallbackQueryHandler
from module.retrieve_webdata import getdownload_urls
from module.markups import general_markup,bus_markup,tr_markup,transport_markup,times_markup
from module.timetables_operations.calculate_times import find_lines

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
        context.chat_data['counter']=0
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
        context.chat_data['counter']=1
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli a che ora controllare", reply_markup=times_markup(),disable_web_page_preview=True)
   
    elif(context.chat_data['counter']==1):
        context.chat_data['counter']=2
        context.chat_data['ora']=query.data
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli tipologia trasporto",reply_markup=transport_markup(),disable_web_page_preview=True)
   
    elif(context.chat_data['counter']==2):
        context.chat_data['counter']=3
        context.chat_data['tipo_trasporto']=query.data
        if context.chat_data['tipo_trasporto']=="bus":
            await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di partenza",reply_markup=bus_markup(),disable_web_page_preview=True)
        elif context.chat_data['tipo_trasporto']=="littorina":
            await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di partenza",reply_markup=tr_markup(),disable_web_page_preview=True)

    elif (context.chat_data['counter']==3):
        context.chat_data['counter']=4
        context.chat_data['partenza']=query.data
        if context.chat_data['tipo_trasporto']=="bus":
            await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di arrivo",reply_markup=bus_markup(),disable_web_page_preview=True)
        elif context.chat_data['tipo_trasporto']=="littorina":
            await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di arrivo",reply_markup=tr_markup(),disable_web_page_preview=True)
    
    elif (context.chat_data['counter']==4):
        context.chat_data['counter']=5
        context.chat_data['arrivo']=query.data
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        await context.bot.send_message(chat_id=message.effective_chat.id, text=find_lines(str(context.chat_data['partenza']),str(context.chat_data['arrivo']),str(context.chat_data['ora']),str(context.chat_data['tipo_trasporto'])))


async def contributors(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id,text=
"""@B4catr0n42, @SuperBomber

https://github.com/Leonardo0101/FCE_bot.git""")

async def welcome(message: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['counter']=0
    await context.bot.send_message(chat_id=message.effective_chat.id, text="Benvenuto nel bot per info sulla Ferrovia Circumetnea",reply_markup=general_markup())

async def help(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text=
"""Orario bus: link pdf orario bus

Orario treni: link pdf orario treni

Orario metro: link pdf orario metro 

Controlla orario vicino: mostra le linee disponibili scegliendo la tipologia di mezzo(bus/littorina), le fermate di partenza e arrivo e l'ora. Verranno restituite tutte le linee corrispondenti nel range di quell'ora (ad esempio se si seleziona 8.00 fara' vedere, se esistono, tutte le linee nel range dalle 8.00 alle 8.59) """)
