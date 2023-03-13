import tabula

file="./module/timetables_operations/locations.txt"
pdf="./module/timetables_operations/bus_orario0.pdf"


def extract_locations_onTXT(s:str):
    with open(file,"w") as f:
        f.write("")
    table=tabula.read_pdf(s, pages='all', stream=True)[0] #prima tabella #pandas_options={'header':None}    
    rows=table.shape[0]  
    #cols=table.shape[1]
    with open(file,"a") as f:
        for i in range(rows):
            row=table.iloc[i:i+1,:].values #prendo la prima riga della tabella
            for j in row[0][:]: #[0] perche' vede anche una riga come una matrice di una sola riga
                f.write(str(j)+" | ") # scrivo ogni elemento della riga (scorrendo le colonne) e mettendo il separatore |
            f.write(" \n")
    
#extract_locations_onTXT(pdf)


def find_lines(s:str,a:str,b:str):
    