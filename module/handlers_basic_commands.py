import logging
from telegram import Update
from telegram.ext import ContextTypes,CommandHandler,CallbackQueryHandler, MessageHandler
from module.retrieve_webdata import getdownload_urls
from module.markups import general_markup,bus_markup,tr_markup,transport_markup,times_markup
from module.timetables_operations.calculate_times import find_lines2 #,find_lines #NO DB#
import threading

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def add_handlers(): #defining handlers
    handlers = [
        #CommandHandler('start',welcome),
        CommandHandler('help',help),
        CommandHandler('contributors',contributors),
        CallbackQueryHandler(buttons),
        MessageHandler(filters=None,callback=scraping_messages)
        
    ]
    return handlers

async def reset(context:ContextTypes.DEFAULT_TYPE,message:Update):
    await context.bot.delete_message(chat_id=message.effective_chat.id,message_id=message.effective_message.id)
    context.chat_data['counter']=0
    await context.bot.send_message(chat_id=message.effective_chat.id,text="Errore durante l'operazione.\nProva di nuovo !",reply_markup=await general_markup())


async def buttons(message: Update, context: ContextTypes.DEFAULT_TYPE):
    query = message.callback_query
    await query.answer()    
    
    if(query.data == "general"):
        await context.bot.delete_message(chat_id=message.effective_chat.id,message_id=message.effective_message.id)
        await start(message,context)

    elif(query.data == "1"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id) #elimino vecchia lista opzioni
        for i in await getdownload_urls(2): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i) #invio orari
        await start(message,context) #rimetto lista opzioni
    
    elif(query.data == "2"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        for i in await getdownload_urls(1): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i)
        await start(message,context)
  
    elif(query.data == "3"):
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        for i in await getdownload_urls(0): 
            await context.bot.send_message(chat_id=message.effective_chat.id, text=i)
        await start(message,context)
   
    elif(query.data == "choose_T"):
        context.chat_data['counter']=1
        await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli a che ora controllare", reply_markup=await times_markup(),disable_web_page_preview=True)
   
    elif context.chat_data=={}: #da qui in poi mi serve questo controllo cosi' da verificare che se la chat_data e' vuota
        #causa riavvio bot o altro, resetto
        await reset(context,message)

    elif(query.data in ["5.00","6.00","7.00","8.00","9.00","10.00","11.00","12.00","13.00","14.00","15.00","16.00","17.00","18.00","19.00","20.00"]):
        if (context.chat_data['counter']==1):
            context.chat_data['counter']=2
            context.chat_data['ora']=query.data
            await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli tipologia trasporto",reply_markup=await transport_markup(),disable_web_page_preview=True)
        else:
            await reset(context,message)        
   
    elif(query.data in ["bus","littorina"]):
        if(context.chat_data['counter']==2):
            context.chat_data['counter']=3
            context.chat_data['tipo_trasporto']=query.data
            if context.chat_data['tipo_trasporto']=="bus":
                await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di _PARTENZA_",reply_markup=await bus_markup(),disable_web_page_preview=True,parse_mode='Markdown')
            elif context.chat_data['tipo_trasporto']=="littorina":
                await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di _PARTENZA_",reply_markup=await tr_markup(),disable_web_page_preview=True,parse_mode='Markdown')
        else:
            await reset(context,message)

    elif (context.chat_data['counter']==4): #controllo prima che non siamo gia' alla fine perche' l'if sotto verrebbe ripetuto 2 volte
        context.chat_data['counter']=5
        context.chat_data['arrivo']=query.data
        await context.bot.delete_message(chat_id=message.effective_chat.id, message_id=message.effective_message.id)
        #threading.Thread(target=await find_lines(context,message)).start() #NO DB# e commentare riga sotto
        threading.Thread(target=await find_lines2(context,message)).start() #ricerca linee
        #await start(message,context)

    elif(query.data in (open("./module/timetables_operations/"+str(context.chat_data['tipo_trasporto'])+"/locations.txt","r")).read()):
        if(context.chat_data['counter']==3):
            context.chat_data['counter']=4
            context.chat_data['partenza']=query.data
            if context.chat_data['tipo_trasporto']=="bus":
                await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di _ARRIVO_",reply_markup=await bus_markup(),disable_web_page_preview=True,parse_mode='Markdown')
            elif context.chat_data['tipo_trasporto']=="littorina":
                await context.bot.edit_message_text(chat_id=message.effective_chat.id,message_id=message.effective_message.id, text="Scegli fermata di _ARRIVO_",reply_markup=await tr_markup(),disable_web_page_preview=True,parse_mode='Markdown')
        else:
            await reset(context,message)

async def contributors(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id,text=
"""@B4catr0n42, @SuperBomber

https://github.com/Leonardo0101/FCE_bot.git""")

async def welcome(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text="Benvenuto nel bot per info sulla Ferrovia Circumetnea\nAltri comandi disponibili /help /contributors")
    await start(message,context)

async def start(message: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['counter']=0
    await context.bot.send_message(chat_id=message.effective_chat.id, text="Cosa posso fare per te ?",reply_markup=await general_markup())

async def help(message: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=message.effective_chat.id, text=
"""Info utili: si consiglia di non fare piu' operazioni in contemporanea con piu' liste opzioni (/start), perche' potreste incorrere in alcuni errori e dover ripetere le operazioni.
Una volta non piu' presenti le operazioni (nel caso di fine controllo linea) potete eseguire un nuovo /start.
In ogni caso per qualsiasi problema, se non sono presenti opzioni e facendo /start ottenete errori, eseguitelo per altre 2 volte e verranno inviate nuovamente le opzioni.

Cosa posso fare:
Orario bus: invio link pdf orario bus
Orario treni: invio link pdf orario littorine
Orario metro: invio link pdf orario metro 

Controlla orario vicino: mostra le linee disponibili scegliendo la tipologia di mezzo(bus/littorina), le fermate di partenza e arrivo e l'ora. Verranno restituite tutte le linee corrispondenti nel range di quell'ora (ad esempio se si seleziona 8.00 fara' vedere, se esistono, tutte le linee nel range dalle 8.00 alle 8.59) """)

async def scraping_messages(message: Update, context: ContextTypes.DEFAULT_TYPE):
    if message.message.text not in ["/start","/help","/contributors"]:
        await context.bot.delete_message(chat_id=message.effective_chat.id,message_id=message.effective_message.id)
    if message.message.text == "/start":
        
        if 'counter' in context.chat_data and context.chat_data['counter']>=0 and context.chat_data['counter']<=4 and context.chat_data['start_count']<2: 
            #verifico che ci sia solo uno start in esecuzione e per essere tale deve essere almeno 0 (chiamata a start)
            #e minore di 4 perche' quando termina la ricerca counter=5. nonostante non si debba poter fare, in caso di problemi
            #se viene chiamato 2 volte start, viene data una nuova istanza
            context.chat_data['start_count']+=1
            await context.bot.delete_message(chat_id=message.effective_chat.id,message_id=message.effective_message.id)
            await context.bot.send_message(chat_id=message.effective_chat.id,text="Le opzioni sono gia' presenti !\n")
        else :
            context.chat_data['start_count']=0
            await welcome(message,context)