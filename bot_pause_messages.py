from telegram.ext import ApplicationBuilder,MessageHandler,ContextTypes
from telegram import Update
from mainbot import token as tt

def add_handlers() -> list: #defining handlers
    handlers = [
        MessageHandler(filters=None,callback=pause)
        
    ]
    return handlers

async def pause(message:Update,context:ContextTypes.DEFAULT_TYPE) -> None:
    if 'count' not in context.chat_data:
        context.chat_data['count']=0
    else:
        context.chat_data['count']+=1
    await context.bot.delete_message(chat_id=message.effective_chat.id,message_id=message.effective_message.id)
    if context.chat_data['count']<2: #considero fino a 2 messaggi inviati
        await context.bot.send_message(chat_id=message.effective_chat.id,text="Bot in pausa ...\ncontrollo nuovi orari/manutenzione")
    elif context.chat_data['count']>10:
        context.chat_data['count']=0


app = ApplicationBuilder().token(tt).build()
app.add_handlers(add_handlers())

def sec_bot() -> None:
    app.run_polling()

if __name__ == '__main__':
    sec_bot()