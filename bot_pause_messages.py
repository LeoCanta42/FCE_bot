from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,ContextTypes
from telegram import Update
from mainbot import token as tt

def add_handlers(): #defining handlers
    handlers = [
        CommandHandler('start',pause),
        CommandHandler('help',pause),
        CommandHandler('contributors',pause),
        CallbackQueryHandler(pause)
        
    ]
    return handlers

async def pause(message:Update,context:ContextTypes.DEFAULT_TYPE,):
    await context.bot.send_message(chat_id=message.effective_chat.id,text="Bot in pausa ...\ncontrollo nuovi orari/manutenzione")

app = ApplicationBuilder().token(tt).build()
app.add_handlers(add_handlers())

def sec_bot():
    app.run_polling()

if __name__ == '__main__':
    sec_bot()