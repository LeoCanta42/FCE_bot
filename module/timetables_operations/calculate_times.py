from datetime import datetime,timedelta
from module.timetables_operations.extract_excel import extract,dimensions,all_replacing
from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH,format_time
from telegram import Update
from telegram.ext import ContextTypes
from module.timetables_operations.extract_excel import bus_workbooks,train_workbooks
path="./module/timetables_operations/"

    
async def find_lines(context:ContextTypes.DEFAULT_TYPE,message:Update): #a punto di partenza, b punto di arrivo
    a=str(context.chat_data['partenza'])
    b=str(context.chat_data['arrivo'])
    time=str(context.chat_data['ora'])
    tipo=str(context.chat_data['tipo_trasporto'])
    dep_time=datetime.strptime(time,"%H.%M")
    line_string=[]
    if tipo=="bus":
        for work_index in range(len(bus_workbooks)):
            m_table=await extract(tipo,work_index)
            ll=await real_elaboration(m_table,dep_time,a,b,context,message)
            for s in ll:
                line_string.append(s)
    elif tipo=="littorina":
        for work_index in range(len(train_workbooks)):
            m_table=await extract(tipo,work_index)
            ll=await real_elaboration(m_table,dep_time,a,b,context,message)
            for s in ll:
                line_string.append(s)
    
    final=""
    h=False
    for line in line_string:
        if h==False:
            final+="Linea esistente"
        final+=str("\n\n"+line)
        h=True
    
    if h==False:
        final="Linea non esistente"

    await context.bot.send_message(chat_id=message.effective_chat.id, text=final)
            
async def real_elaboration(m_table,dep_time,a,b,context:ContextTypes.DEFAULT_TYPE,message:Update):
    ll=[]
    for table in range(len(m_table)):
        matrix=m_table[table]
        d=await dimensions(matrix)
        start=d[0]
        rows=d[1]
        cols=len(matrix[start])

    #operazioni per trovare indici partenza e destinazione
        partenza=0
        destinazione=0
        for i,j in zip(range(start,rows),range(start,rows)): 
            #dato che ci sono anche stesse fermate con piccole differenze, metto maiuscole e tolgo spazi
            if partenza!=0 and destinazione!=0 and destinazione>partenza: break
            if(await all_replacing(str(matrix[i][0]))==await all_replacing(a)): 
                partenza=i
            elif(j>partenza and partenza!=0 and await all_replacing(str(matrix[j][0]))==await all_replacing(b)):
                destinazione=j        
    #operazioni per trovare linee valide nel tempo entro mezzora da quello indicato
        line=[]
        if partenza!=0 and destinazione>partenza:
            for i in range(1,cols):
                #if str(matrix[start-2][i]).upper().replace('.','').replace('TR','LITTORINA')==tipo.upper(): #se voglio che faccia questa cosa solo se sono bus, non treni
                    type_time=0 #perche' posso avere ore.minuti o solo ore
                    if(await isTimeFormat(str(matrix[partenza][i]))): type_time=1
                    elif (await isTimeFormatH(str(matrix[partenza][i]))): type_time=2
                    if(type_time!=0):
                        if(type_time==1):
                            cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H.%M")
                        else:
                            cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H")
                        interval=59 #minuti
            
                        #if cur_time_considered>=(dep_time-timedelta(minutes=interval)) and cur_time_considered<=(dep_time+timedelta(minutes=interval)): #intervallo prima di 30 min e dopo 30 min
                        if cur_time_considered>=(dep_time) and cur_time_considered<=(dep_time+timedelta(minutes=interval)): #intervallo con orario x fino alle x.59
                            if await isTimeFormat(str(matrix[destinazione][i])) or await isTimeFormatH(str(matrix[destinazione][i])) :
                                line.append(i)
                        elif cur_time_considered>(dep_time+timedelta(minutes=interval)): #i successivi saranno tutti > posso fermarmi
                            break
        #salvo le stringhe delle linee valide per quel file                            
        
        for l in line:
            if isinstance(l,int): # mi assicuro che sia un indice e quindi intero
                s_to_append=matrix[start-2][l]+"\n"+matrix[partenza][0]+": "+await format_time(str(matrix[partenza][l]))+"\n"+matrix[destinazione][0]+": "+await format_time(str(matrix[destinazione][l]))
                ll.append(str(s_to_append))
    return ll
