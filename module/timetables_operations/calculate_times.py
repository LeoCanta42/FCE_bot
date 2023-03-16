#import tabula
import glob
from datetime import datetime,timedelta
from extract_excel import extract

file="./module/timetables_operations/locations.txt"
pdf="./module/timetables_operations/bus_orario0.pdf"

def isTimeFormat(input:str):
    try:
        datetime.strptime(input, "%H.%M")
        return True
    except:
        return False
def isTimeFormatH(input:str):
    try:
        datetime.strptime(input, "%H")
        return True
    except:
        return False
'''
def find_files():
    list_files=glob.glob("./module/timetables_operations/matrice_orari*.txt")
    return list_files

def extract_pdftable_tomatrix_txt(s:str):
    table=tabula.read_pdf(s, pages='all', stream=True) #prima tabella , per seconda uso[1]  
    
    #cols=table.shape[1]
    ntable=0
    for t in table:
        rows=t.shape[0] 
        with open("./module/timetables_operations/matrice_orari"+str(ntable)+".txt","w") as f:
            for i in range(rows):
                row=t.iloc[i:i+1,:].values #prendo la prima riga della tabella
                for j in row[0]: #[0] perche' vede anche una riga come una matrice di una sola riga                
                    f.write(str(j)+",")  
                f.write("\n")
        ntable+=1
    #DA SISTEMARE IL FATTO CHE ALCUNI ORARI VENGONO MESSI DOPO \n ANCHE SE DEVONO ESSERE DI UNA SOLA RIGA
'''    

def find_lines(a:str,b:str,time:str): #a punto di partenza, b punto di arrivo
    '''
    list_files=find_files()
    count=0 #mi indica il file che sto considerando
    

    for file in list_files:
        
        matrix=[]
        rows=0

    #lettura da file per costruire matrice
        with open(str(file),"r") as f: #conto le righe
            for i in f.readlines():
                rows+=1
    
        matrix=[[] for i in range(rows)] #inizializzo matrice
        with open(str(file),"r") as f:
            #leggo riga per riga con separatore, fisso i e scorro j
            for i in range(rows):
                line=f.readline()
                #extract element j
                splitted=line.split(",")
                for j in splitted:
                    matrix[i].append(j)
        
        cols=len(matrix[1][:])
    '''
    dep_time=datetime.strptime(time,"%H.%M")
    line_string=[]
    matrix=extract()
    for table in range(2): #2 perche' ci sono 2 tabelle nel file excel
        count_table=0
        start=0
        rows=0
        h=True
        for i in range(len(matrix)):
            if str(matrix[i][0])=="CATANIA (S.Sofia)":
                count_table+=1
            if count_table==1 and table==0 and h:
                start=i
                h=False
            elif count_table==2 and table==0 and h==False:
                rows=i+1
                h=True
            elif count_table==3 and table==1 and h:
                start=i 
                h=False
            elif count_table==4 and table==1 and h==False:
                rows=i+1
        cols=len(matrix[start])

    #operazioni per trovare indici partenza e destinazione
        partenza=0
        destinazione=0
        for i,j in zip(range(start,rows),range(start,rows)): 
            if(str(matrix[i][0])==a):
                partenza=i
            elif(j>partenza and partenza!=0 and str(matrix[j][0])==b):
                destinazione=j        
    #operazioni per trovare linee valide nel tempo entro mezzora da quello indicato
        line=[]
        if partenza!=0 and destinazione>partenza:
            for i in range(1,cols):
                type_time=0 #perche' posso avere ore.minuti o solo ore
                if(isTimeFormat(str(matrix[partenza][i]))): type_time=1
                elif (isTimeFormatH(str(matrix[partenza][i]))): type_time=2
                if(type_time!=0):
                    if(type_time==1):
                        cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H.%M")
                    else:
                        cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H")
                    interval=30 #minuti
        
                    if cur_time_considered>=(dep_time-timedelta(minutes=interval)) and cur_time_considered<=(dep_time+timedelta(minutes=interval)):
                        if isTimeFormat(str(matrix[destinazione][i])) or isTimeFormatH(str(matrix[destinazione][i])) :
                            line.append(i)
        #salvo le stringhe delle linee valide per quel file                            
        
        line_string.append(table)
        line_string[table]=[]
        for l in line:
            if isinstance(l,int): # mi assicuro che sia un indice e quindi intero
                line_string[table].append(str(matrix[2][l])+"\n"+str(matrix[partenza][0])+": "+str(matrix[partenza][l])+"\n"+str(matrix[destinazione][0])+": "+str(matrix[destinazione][l]))
    
        
    
    h=False
    for c in range(2): #stesso motivo di prima di table (2 tabelle)
        if len(line_string[c])!=0:
            for line in line_string[c]:            
                if h==False:
                    print("Linea esistente")
                print("\n"+line)
                h=True
    
    if h==False:
        print("Linea non esistente")

    #'''
    

find_lines("BIANCAVILLA","PATERNO' Staz. FCE","20.00")
#extract_pdftable_tomatrix_txt(pdf)
#find_files()
