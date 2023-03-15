import tabula
import glob
from datetime import datetime,timedelta

file="./module/timetables_operations/locations.txt"
pdf="./module/timetables_operations/bus_orario0.pdf"

def isTimeFormat(input:str):
    try:
        datetime.strptime(input, "%H.%M")
        return True
    except:
        return False

def find_files():
    list_files=glob.glob("./module/timetables_operations/matrice_orari*.txt")
    return list_files

def extract_pdftable_tomatrix_txt(s:str):
    table=tabula.read_pdf(s, pages='all', stream=True) #prima tabella #pandas_options={'header':None} , per seconda uso[1]  
    
    #cols=table.shape[1]
    ntable=0
    for t in table:
        rows=t.shape[0] 
        with open("./module/timetables_operations/matrice_orari"+str(ntable)+".txt","w") as f:
            for i in range(rows):
                row=t.iloc[i:i+1,:].values #prendo la prima riga della tabella
                for j in row[0][:]: #[0] perche' vede anche una riga come una matrice di una sola riga                
                    f.write(str(j)+",")  
                f.write("\n")
        ntable+=1
    

def find_lines(a:str,b:str,time:str): #a punto di partenza, b punto di arrivo
    list_files=find_files()
    count=0 #mi indica il file che sto considerando
    dep_time=datetime.strptime(time,"%H.%M")
    line_string=[]

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
    #operazioni per trovare indici partenza e destinazione
        partenza=0
        destinazione=0
        for i,j in zip(range(rows),range(rows)):
            if(str(matrix[i][0])==a):
                partenza=i
            elif(j>partenza and str(matrix[j][0])==b):
                destinazione=j        
    #operazioni per trovare linee valide nel tempo entro mezzora da quello indicato
        if partenza!=0 and destinazione>partenza:
            line=[]
            for i in range(1,cols):
                if(isTimeFormat(matrix[partenza][i])):
                    cur_time_considered=datetime.strptime(str(matrix[partenza][i]),"%H.%M")
                    interval=45 #minuti

                    if cur_time_considered>=(dep_time-timedelta(minutes=interval)) and cur_time_considered<=(dep_time+timedelta(minutes=interval)):
                        if isTimeFormat(matrix[destinazione][i]):
                            line.append(i)
        #salvo le stringhe delle linee valide per quel file                            
        line_string.append(count)
        line_string[count]=[]
        for l in line:
            if isinstance(l,int): # mi assicuro che sia un indice e quindi intero
                line_string[count].append(str(matrix[partenza][0])+":"+str(matrix[partenza][l])+"\n"+str(matrix[destinazione][0])+":"+str(matrix[destinazione][l]))
        
        count+=1
    
        
    
    h=False
    for c in range(count):
        if len(line_string[c])!=0:
            for line in line_string[c]:            
                print("Linea esistente \n"+line)
                h=True
    
    if h==False:
        print("Linea non esistente")
    


find_lines("PATERNO' Staz. FCE","CIBALI","8.00")
#extract_pdftable_tomatrix_txt(pdf)
#find_files()