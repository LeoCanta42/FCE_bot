import tabula

def define_locations(s:str): 
    table=tabula.read_pdf(s, pages='all', lattice=True)[0] #prima tabella #pandas_options={'header':None}
    first_col=table.iloc[1:,:1] #iloc[row:row,col:col]
    for i in first_col.values:
        print(i)
    
    print("SECONDA \n")
    table=tabula.read_pdf(s, pages='all', lattice=True)[1] #seconda tabella #pandas_options={'header':None}
    first_col=table.iloc[1:,:1] #iloc[row:row,col:col]
    for i in first_col.values:
        print(i)

define_locations("./bus_orario0.pdf")