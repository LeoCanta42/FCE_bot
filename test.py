import logging
from telegram import InlineKeyboardButton,InlineKeyboardMarkup,Update
from telegram.ext import ApplicationBuilder,ContextTypes,CommandHandler,CallbackQueryHandler
import retrieve_webdata

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def general_markup():
    keyboard = [
        [
            InlineKeyboardButton("Orario bus", callback_data="1"),
            InlineKeyboardButton("Orario treni", callback_data="2"),
        ],
        [
            InlineKeyboardButton("Orario metro", callback_data="3"),
            InlineKeyboardButton("Controlla orario vicino", callback_data="4")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def add_handlers():
    handlers = [
        CommandHandler('start',welcome),
        CommandHandler('help',help),
        CallbackQueryHandler(button)
        
    ]
    return handlers

async def button(message: Update, context: ContextTypes.DEFAULT_TYPE):
    query = message.callback_query

    await query.answer()
    if(query.data == "1"): 
        await context.bot.send_message(chat_id=message.effective_chat.id, text=retrieve_webdata.filter_urls(1))
    elif(query.data == "2"):
        await context.bot.send_message(chat_id=message.effective_chat.id, text="Funziona2")
    elif(query.data == "3"):
        await context.bot.send_message(chat_id=message.effective_chat.id, text="Funziona3")
    elif(query.data == "4"):
        await context.bot.send_message(chat_id=message.effective_chat.id, text="Funziona4")

async def welcome(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text="Benvenuto nel bot per info sulla Ferrovia Circumetnea",reply_markup=general_markup())

async def help(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text=
"""Orario bus: scarica pdf orario bus
Orario treni: scarica pdf orario treni
Orario metro: scarica pdf orario metro 
Controlla orario vicino: calcola l'orario piu' vicino a quello desiderato per andare da/a """)

def main():
    token = str(open('fcebot_token.txt','r').read()).strip()
    bot= ApplicationBuilder().token(token).build()

    bot.add_handlers(add_handlers())
    
    bot.run_polling()

if __name__ == '__main__':
    main()