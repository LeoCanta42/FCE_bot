import tabula

file="./module/timetables_operations/locations.txt"
pdf="./module/timetables_operations/bus_orario0.pdf"


def extract_pdftable_tomatrix(s:str):
    with open(file,"w") as f:
        f.write("")
    table=tabula.read_pdf(s, pages='all', stream=True)[0] #prima tabella #pandas_options={'header':None} , per seconda uso[1]  
    rows=table.shape[0] 
    matrix=[]
    matrix=[[] for i in range(rows)] #inizializzo matrice
    #cols=table.shape[1]
    for i in range(rows):
        row=table.iloc[i:i+1,:].values #prendo la prima riga della tabella
        for j in row[0][:]: #[0] perche' vede anche una riga come una matrice di una sola riga                
            matrix[i].append(j) # scrivo ogni elemento della riga (scorrendo le colonne)            
    return matrix

#extract_pdftable_tomatrix(pdf)


def find_lines(a:str,b:str,time:str):
    route=False
    matrix=extract_pdftable_tomatrix(pdf)
    rows=len(matrix)
    cols=len(matrix[1][:])
    partenza=0
    line=0
    for i in range(rows):
        if(str(matrix[i][0])==a):
            for j in range(cols):
                if(matrix[i][j]==time):
                    line=j
                    partenza=i
                    route=True
                    break
    if partenza!=0:
        partenza+=1
        for partenza in range(rows):
            if(str(matrix[partenza][0])==b):
                if(matrix[i][line]=="nan"):
                    route=False
    if route:
        print("Linea esistente")
    else:
        print("Linea non esistente")
                

find_lines("CIBALI","VALCORRENTE","16.27")