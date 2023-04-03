from module.timetables_operations.extract_excel import bus_workbooks,train_workbooks,extract,dimensions,all_replacing
from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH,format_time
import asyncio

def set_db(connection):
    cursor=connection.cursor()
    cursor.execute("create table Tratte(idTratta INTEGER PRIMARY KEY AUTOINCREMENT,CodiceTratta TEXT, Mezzo TEXT)")
    cursor.execute("create table Fermate(idFermata INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT,nomereplace TEXT,bus BOOL, littorina BOOL)")
    cursor.execute("create table TratteFermate(id INTEGER PRIMARY KEY AUTOINCREMENT, orario TIME, idFermata INTEGER, idTratta INTEGER, foreign key (idFermata) references Fermate(idFermata),foreign key (idTratta) references Tratte(idTratta))")

def reset(connection):
    cursor=connection.cursor()
    cursor.execute("drop table Tratte")
    cursor.execute("drop table Fermate")
    cursor.execute("drop table TratteFermate")

def insert_fermate(connection):
    cursor=connection.cursor()
    file=open("./module/timetables_operations/bus/locations.txt","r")
    bus_loc=file.readlines()
    file=open("./module/timetables_operations/littorina/locations.txt","r")
    train_loc=file.readlines()
    
    for i in range(len(bus_loc)):
        bus_loc[i]=bus_loc[i].replace('\n','')
        cursor.execute("insert into Fermate(Nome,bus,littorina,nomereplace) values(?,1,0,?)",(bus_loc[i],str(all_replacing(str(bus_loc[i]))),))
        bus_loc[i]=all_replacing(bus_loc[i])
    
    for i in range(len(train_loc)):
        train_loc[i]=train_loc[i].replace('\n','')
        if all_replacing(train_loc[i]) in bus_loc:
            cursor.execute("update Fermate set littorina=1 where Nome=?",(train_loc[i],))
        else:
            cursor.execute("insert into Fermate(Nome,littorina,bus,nomereplace) values(?,1,0,?)",(train_loc[i],str(all_replacing(str(train_loc[i]))),))


def insert_tratte(connection): #tratte e collegamento fermata-tratta
    cursor=connection.cursor()
    tipologia=["bus","littorina"]
    for tipo in tipologia:
        if tipo=="bus": 
            cur_workbooks=bus_workbooks
            r_tipo="BUS"
        elif tipo=="littorina": 
            cur_workbooks=train_workbooks
            r_tipo="TR"
        for work_index in range(len(cur_workbooks)):
                m_table=asyncio.run(extract(tipo,work_index))
                for table in range(len(m_table)):
                    matrix=m_table[table]
                    d=dimensions(matrix)
                    start=d[0]
                    rows=d[1]
                    cols=len(matrix[start])

                    locs=[]
                    tmp=cursor.execute("select nomereplace from Fermate").fetchall()
                    for i in tmp:
                        locs.append(i[0])

                    for j in range(2,cols): #da 2 perche' i primi due sono occupati da cella STAZIONI/FERMATE
                        #matrix[start-2][j] #-2 mi da bus e treni, -1 mi torna i codici delle tratte
                        if (cursor.execute("select * from Tratte where CodiceTratta=? and Mezzo=?",(str(matrix[start-1][j]),r_tipo)))!=None and str(matrix[start-2][j]).replace('.','')==r_tipo: # questo ultimo controllo serve per ora che abbiamo un file unico
                            cursor.execute("insert into Tratte (CodiceTratta,Mezzo) values (?,?)",(str(matrix[start-1][j]),r_tipo,))
                            idt=cursor.execute("select idTratta from Tratte where CodiceTratta=? and Mezzo=? ",(str(matrix[start-1][j]),r_tipo,)).fetchone()
                            for i in range(start,rows):
                                
                                if (isTimeFormat(str(matrix[i][j])) or isTimeFormatH(str(matrix[i][j]))) and str(matrix[i][j])!="None" and (all_replacing(str(matrix[i][0])) in locs):
                                    '''controllo che la localita' 
                                    sia una esistente per evitare di sforare nel foglio e 
                                    prendere LEGENDA o altro'''
                                    idf=cursor.execute("select idFermata from Fermate where nomereplace=? ",(str(all_replacing(str(matrix[i][0]))),)).fetchone()
                                    print("idTratta:"+str(idt[0]) +"\nidFermata:"+str(idf[0])+"\n")
                                    cursor.execute("insert into TratteFermate(orario,idTratta,idFermata) values(?,?,?)",(str(format_time(str(matrix[i][j]))),int(idt[0]),int(idf[0]),))
                                    print("Inserito "+str(matrix[i][0])+" "+str(matrix[start-1][j])+" "+str(matrix[start-2][j])+" "+str(matrix[i][j])+"\n\n")
