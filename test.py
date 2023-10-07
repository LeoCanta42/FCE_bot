import sqlite3 as sql

with sql.connect("fce_lines.db") as connection:
    cursor=connection.cursor()
    result=cursor.execute("SELECT T.id, T.orario, F.Mezzo from TratteFermate T, Tratte F where T.idTratta=F.idTratta").fetchall()
    for i in result:
        print(str(i[0])+" "+str(i[1])+" "+str(i[2])+"\n")