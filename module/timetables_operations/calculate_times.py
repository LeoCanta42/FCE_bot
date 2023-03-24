from datetime import datetime,timedelta
from module.timetables_operations.extract_excel import extract,dimensions,all_replacing,find_files
from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH,format_time
path="./module/timetables_operations/"

    
def find_lines(a:str,b:str,time:str,tipo:str): #a punto di partenza, b punto di arrivo
    dep_time=datetime.strptime(time,"%H.%M")
    line_string=[]
    file_to_check=find_files(tipo)
    for file in file_to_check:
        m_table=extract(file,tipo)
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
                                if isTimeFormat(str(matrix[destinazione][i])) or isTimeFormatH(str(matrix[destinazione][i])) :
                                    line.append(i)
                            elif cur_time_considered>(dep_time+timedelta(minutes=interval)): #i successivi saranno tutti > posso fermarmi
                                break
            #salvo le stringhe delle linee valide per quel file                            
            
            for l in line:
                if isinstance(l,int): # mi assicuro che sia un indice e quindi intero
                    s_to_append=matrix[start-2][l]+"\n"+matrix[partenza][0]+": "+format_time(str(matrix[partenza][l]))+"\n"+matrix[destinazione][0]+": "+format_time(str(matrix[destinazione][l]))
                    line_string.append(str(s_to_append))
        
        final=""
        h=False
        for line in line_string:
            if h==False:
                final+="Linea esistente"
            final+=str("\n\n"+line)
            h=True
        
        if h==False:
            final="Linea non esistente"

        return final

