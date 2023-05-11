from datetime import datetime,timedelta
from module.timetables_operations.extract_excel import all_replacing
#from module.timetables_operations.extract_excel import extract,dimensions
#from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH,format_time
from module.timetables_operations.times_op import format_time
from module.fixed_send_message import fix_message
from telegram import Update
from telegram.ext import ContextTypes
from module.timetables_operations.extract_excel import bus_workbooks,train_workbooks
import sqlite3 as sql
import threading
path="./module/timetables_operations/"

#___________________________________--- work with DB


#primo select trova tutte le destinazioni raggiungibili dalla partenza passata
#secondo select trova tutte le partenze che fanno raggiungere l'arrivo passato
#condizione veririfica che l'arrivo del primo è = partenza del secondo

async def find_lines(context:ContextTypes.DEFAULT_TYPE,message:Update,query_type:str) -> None: 
    #desiderata ora di partenza
    query_findpartenza='''select t1.orario, t2.orario,tr.Mezzo
                    from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                    where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace like ? || '%'
                    and t2.idFermata=f2.idFermata and f2.nomereplace like ? || '%' and f1.nomereplace!=f2.nomereplace and
                    tr.idTratta=t1.idTratta  and t2.orario>t1.orario and (strftime('%H.%M',?)-t1.orario)<=0 and (strftime('%H.%M',?)-t1.orario)>=0
    '''
    #desiderata ora di arrivo
    query_finddestinazione='''select t1.orario, t2.orario,tr.Mezzo
                    from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                    where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace like ? || '%' 
                    and t2.idFermata=f2.idFermata and f2.nomereplace like ? || '%' and f1.nomereplace!=f2.nomereplace and
                    tr.idTratta=t1.idTratta  and t2.orario>t1.orario and (strftime('%H.%M',?)-t2.orario)<=0 and (strftime('%H.%M',?)-t2.orario)>=0
    '''
    #da ora desiderata in poi partenza
    query_findpartenza2='''select t1.orario, t2.orario,tr.Mezzo
                    from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                    where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace like ? || '%' 
                    and t2.idFermata=f2.idFermata and f2.nomereplace like ? || '%' and f1.nomereplace!=f2.nomereplace and
                    tr.idTratta=t1.idTratta  and t2.orario>t1.orario and (strftime('%H.%M',?)-t1.orario)<=0
    '''
    #da ora desiderata arrivo o prima
    query_finddestinazione2='''select t1.orario, t2.orario,tr.Mezzo
                    from TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
                    where t1.idTratta=t2.idTratta and t1.idFermata=f1.idFermata and f1.nomereplace like ? || '%' 
                    and t2.idFermata=f2.idFermata and f2.nomereplace like ? || '%' and f1.nomereplace!=f2.nomereplace and
                    tr.idTratta=t1.idTratta  and t2.orario>t1.orario and (strftime('%H.%M',?)-t2.orario)>=0
    '''

    query_findincroci='''
    SELECT V1.fermPar AS FermataPartenza, V1.orpar AS OrarioPartenza, V1.fermArr AS FermataScambio, V1.orarr AS OrarioArrivoScambio,V1.Mezzo AS Mezzo, V2.orpar AS OrarioPartenzaScambio, V2.fermArr AS FermataArrivo, V2.orarr AS OrarioArrivo,V2.Mezzo as Mezzo
    FROM (
        SELECT t1.orario as orpar, f1.Nome as fermPar, t2.orario as orarr, f2.Nome as fermArr, tr.Mezzo as Mezzo
        FROM TratteFermate t1,TratteFermate t2, Fermate as f1,Fermate as f2, Tratte as tr
        WHERE t1.idTratta=t2.idTratta AND 
            t1.idFermata=f1.idFermata AND 
            f1.nomereplace like ? || '%' AND

            t2.idFermata=f2.idFermata AND  
            f1.nomereplace!=f2.nomereplace AND
            tr.idTratta=t1.idTratta AND 
            t2.orario>t1.orario
    ) AS V1, 
    (   SELECT t3.orario as orpar, f3.Nome as fermPar, t4.orario as orarr, f4.Nome as fermArr, tr2.mezzo as Mezzo
        FROM TratteFermate t3,TratteFermate t4, Fermate as f3,Fermate as f4, Tratte as tr2
        WHERE t3.idTratta=t4.idTratta AND 
            t3.idFermata=f3.idFermata AND 
            
            t4.idFermata=f4.idFermata AND 
            f4.nomereplace like ? || '%' AND 
            f3.nomereplace!=f4.nomereplace AND
            tr2.idTratta=t3.idTratta AND 
            t4.orario>t3.orario
    ) AS V2
    WHERE V1.fermArr = V2.fermPar AND V1.orarr <= V2.orpar and V1.fermPar!=V2.fermArr 
    '''

    
    a=str(context.chat_data['partenza'])
    b=str(context.chat_data['arrivo'])
    
    tipo=str(context.chat_data['tipo_trasporto'])
    if tipo=="bus": tipo="BUS"
    elif tipo=="littorina": tipo="TR"

    time=str(context.chat_data['ora'])
    dep_time=datetime.strptime(time,"%H.%M")
    interval=59
    if tipo!="qualsiasi":
        query_findpartenza+=" and tr.Mezzo='{}' order by t1.orario".format(tipo)
        query_findpartenza2+=" and tr.Mezzo='{}' order by t1.orario".format(tipo)
        query_finddestinazione+=" and tr.Mezzo='{}' order by t1.orario".format(tipo)
        query_finddestinazione2+=" and tr.Mezzo='{}' order by t1.orario".format(tipo)
    try:
        with sql.connect("fce_lines.db") as connection:
            cursor = connection.cursor()
            not_direct=False

            if query_type=="near_arrivo2":
                result=cursor.execute(query_finddestinazione2,(all_replacing(a),all_replacing(b),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
            elif query_type=="near_partenza2":
                result=cursor.execute(query_findpartenza2,(all_replacing(a),all_replacing(b),str(dep_time.time()),)).fetchall()
            elif query_type=="near_partenza":
                result=cursor.execute(query_findpartenza,(all_replacing(a),all_replacing(b),str(dep_time.time()),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
            elif query_type=="near_arrivo":
                result=cursor.execute(query_finddestinazione,(all_replacing(a),all_replacing(b),str(dep_time.time()),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()

            if len(result)==0: #quindi non esiste linea diretta, senno' l'avrebbe trovata con quelli prima
                not_direct=True
                query=query_findincroci
                if query_type=="near_arrivo2": #compongo la query con quello che serve da aggiungere per validare quelle condizioni
                    query+=''' AND (strftime('%H.%M',?)-V2.orarr)>=0'''
                elif query_type=="near_partenza2":
                    query+=''' AND (strftime('%H.%M',?)-V1.orpar)<=0'''
                elif query_type=="near_partenza":
                    query+=''' AND (strftime('%H.%M',?)-V1.orpar)<=0 AND (strftime('%H.%M',?)-V1.orpar)>=0'''
                elif query_type=="near_arrivo":
                    query+=''' AND (strftime('%H.%M',?)-V2.orarr)<=0 AND (strftime('%H.%M',?)-V2.orarr)>=0'''

                if tipo!="qualsiasi":
                    query+=" and V1.Mezzo='{}' and V2.Mezzo='{}'".format(tipo,tipo)

                query+='''
                ORDER BY OrarioPartenza'''#giusto per ordinare gli orari
                if query_type=="near_arrivo2":
                    result=cursor.execute(query,(all_replacing(a),all_replacing(b),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
                elif query_type=="near_partenza2":
                    result=cursor.execute(query,(all_replacing(a),all_replacing(b),str(dep_time.time()),)).fetchall()
                else:
                    result=cursor.execute(query,(all_replacing(a),all_replacing(b),str(dep_time.time()),str((dep_time+timedelta(minutes=interval)).time()),)).fetchall()
        
        if len(result)>0:
            string=""
            for i in result:
                if not_direct: #se deve fare la ricerca con incroci ha un formato diverso l'output
                    string+="_Linea non diretta_\n"+("*"+str(i[4])+"*")+"\n"+format_time(str(i[1]))+" - "+str(a)+"\n"+format_time(str(i[3]))+" - "+str(i[2])+"\n*"+str(i[8])+"*\n"+format_time(str(i[5]))+" - "+str(i[2])+"\n"+format_time(str(i[7]))+" - "+str(b)+"\n\n"
                else:
                    string+="_Linea diretta_\n"+("*"+str(i[2])+"*")+"\n"+format_time(str(i[0]))+" - "+str(a)+"\n"+format_time(str(i[1]))+" - "+str(b)+"\n\n"
        else:
            string="Linea non esistente"
        
        to_send=fix_message(string)
        
        for msg in to_send: #per ogni elemento nella stringa inviamo un messaggio
            threading.Thread(target=await context.bot.send_message(chat_id=message.effective_chat.id,text=msg,parse_mode='Markdown'))
    except Exception as e:
        print("Errore durante l'esecuzione della query: {}".format(e))
        threading.Thread(target=await context.bot.send_message(chat_id=message.effective_chat.id,text="Errore durante l'operazione.",parse_mode='Markdown'))
    

'''
query_testing=""" select f.Nome,tr.orario,t.CodiceTratta
                from Fermate f, Tratte t, TratteFermate tr
                where tr.idFermata=f.idFermata and tr.idTratta=t.idTratta and t.Mezzo='BUS'
                order by t.idTratta """

def find_lines2(): 
    with sql.connect("fce_lines.db") as connection:
        cursor = connection.cursor() 
        result=cursor.execute(query_testing).fetchall()   
    
    cur_tr=result[0][2]
    h=True
    for i in result:
        if i[2]!=cur_tr:
            cur_tr=i[2]
            print('\n')
        if i[2]=='1' and h:
            print("Da qui inizia seconda tabella")
            h=False
        print(str(i))
'''   #serve per vedere tutte le linee in ordine per colonne

#work without DB ---- uses matrix
'''
async def find_lines(context:ContextTypes.DEFAULT_TYPE,message:Update) -> None: #a punto di partenza, b punto di arrivo
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
            
async def real_elaboration(m_table,dep_time,a,b,context:ContextTypes.DEFAULT_TYPE,message:Update) -> list:
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
