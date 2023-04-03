from datetime import datetime,timedelta
from module.timetables_operations.extract_excel import all_replacing
#from module.timetables_operations.extract_excel import extract,dimensions
#from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH,format_time
from module.timetables_operations.times_op import format_time
from telegram import Update
from telegram.ext import ContextTypes
from module.timetables_operations.extract_excel import bus_workbooks,train_workbooks
import sqlite3 as sql
import threading
path="./module/timetables_operations/"

#___________________________________--- work with DB

#desiderata ora di partenza
query_findpartenza='''select t1.orario, t2.orario
                from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace=? 
                and t2.idFermata=f2.idFermata and f2.nomereplace=? and f1.nomereplace!=f2.nomereplace and
                tr.idTratta=t1.idTratta and tr.Mezzo=? and t2.orario>t1.orario and (strftime('%H.%M',?)-t1.orario)<=0 and (strftime('%H.%M',?)-t1.orario)>=0  '''
#desiderata ora di arrivo
query_finddestinazione='''select t1.orario, t2.orario
                from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace=? 
                and t2.idFermata=f2.idFermata and f2.nomereplace=? and f1.nomereplace!=f2.nomereplace and
                tr.idTratta=t1.idTratta and tr.Mezzo=? and t2.orario>t1.orario and (strftime('%H.%M',?)-t2.orario)<=0 and (strftime('%H.%M',?)-t2.orario)>=0  '''
#da ora desiderata in poi partenza
query_findpartenza2='''select t1.orario, t2.orario
                from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace=? 
                and t2.idFermata=f2.idFermata and f2.nomereplace=? and f1.nomereplace!=f2.nomereplace and
                tr.idTratta=t1.idTratta and tr.Mezzo=? and t2.orario>t1.orario and (strftime('%H.%M',?)-t1.orario)<=0 '''
#da ora desiderata arrivo o prima
query_finddestinazione2='''select t1.orario, t2.orario
                from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace=? 
                and t2.idFermata=f2.idFermata and f2.nomereplace=? and f1.nomereplace!=f2.nomereplace and
                tr.idTratta=t1.idTratta and tr.Mezzo=? and t2.orario>t1.orario and (strftime('%H.%M',?)-t2.orario)>=0 '''

async def find_lines(context:ContextTypes.DEFAULT_TYPE,message:Update,query:str): 
    a=str(context.chat_data['partenza'])
    b=str(context.chat_data['arrivo'])
    
    tipo=str(context.chat_data['tipo_trasporto'])
    if tipo=="bus": tipo="BUS"
    elif tipo=="littorina": tipo="TR"

    time=str(context.chat_data['ora'])
    dep_time=datetime.strptime(time,"%H.%M")
    interval=59

    with sql.connect("fce_lines.db") as connection:
        cursor = connection.cursor()
        
        if query==query_finddestinazione2:
            result=cursor.execute(query,(all_replacing(a),all_replacing(b),tipo,str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
        elif query==query_findpartenza2:
            result=cursor.execute(query,(all_replacing(a),all_replacing(b),tipo,str(dep_time.time()),)).fetchall()
        else:
            result=cursor.execute(query,(all_replacing(a),all_replacing(b),tipo,str(dep_time.time()),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
    
    string="Linea esistente"
    h=False
    for i in result:
        string+="\n\n"+str(tipo)+"\n"+str(a)+": "+format_time(str(i[0]))+"\n"+str(b)+": "+format_time(str(i[1]))
        h=True
    if not h:
        string="Linea non esistente"
    
    threading.Thread(target=await context.bot.send_message(chat_id=message.effective_chat.id,text=string))
    


#work without DB ---- uses matrix
'''
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
        d=dimensions(matrix)
        start=d[0]
        rows=d[1]
        cols=len(matrix[start])

    #operazioni per trovare indici partenza e destinazione
        partenza=0
        destinazione=0
        for i,j in zip(range(start,rows),range(start,rows)): 
            #dato che ci sono anche stesse fermate con piccole differenze, metto maiuscole e tolgo spazi
            if partenza!=0 and destinazione!=0 and destinazione>partenza: break
            if(all_replacing(str(matrix[i][0]))==all_replacing(a)): 
                partenza=i
            elif(j>partenza and partenza!=0 and all_replacing(str(matrix[j][0]))==all_replacing(b)):
                destinazione=j        
    #operazioni per trovare linee valide nel tempo entro mezzora da quello indicato
        line=[]
        if partenza!=0 and destinazione>partenza:
            for i in range(1,cols):
                #if str(matrix[start-2][i]).upper().replace('.','').replace('TR','LITTORINA')==tipo.upper(): #se voglio che faccia questa cosa solo se sono bus, non treni
                    type_time=0 #perche' posso avere ore.minuti o solo ore
                    if(isTimeFormat(str(matrix[partenza][i]))): type_time=1
                    elif (isTimeFormatH(str(matrix[partenza][i]))): type_time=2
                    if(type_time!=0):
                        if(type_time==1):
                            cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H.%M")
                        else:
                            cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H")
                        interval=59 #minuti
            
                        #if cur_time_considered>=(dep_time-timedelta(minutes=interval)) and cur_time_considered<=(dep_time+timedelta(minutes=interval)): #intervallo prima di 30 min e dopo 30 min
                        if cur_time_considered>=(dep_time) and cur_time_considered<=(dep_time+timedelta(minutes=interval)): #intervallo con orario x fino alle x.59
                            if  isTimeFormat(str(matrix[destinazione][i])) or  isTimeFormatH(str(matrix[destinazione][i])) :
                                line.append(i)
                        elif cur_time_considered>(dep_time+timedelta(minutes=interval)): #i successivi saranno tutti > posso fermarmi
                            break
        #salvo le stringhe delle linee valide per quel file                            
        
        for l in line:
            if isinstance(l,int): # mi assicuro che sia un indice e quindi intero
                s_to_append=matrix[start-2][l]+"\n"+matrix[partenza][0]+": "+ format_time(str(matrix[partenza][l]))+"\n"+matrix[destinazione][0]+": "+ format_time(str(matrix[destinazione][l]))
                ll.append(str(s_to_append))
    return ll
'''    
