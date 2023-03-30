import sqlite3 as sql

connection = sql.connect("fce_lines.db")

cursor = connection.cursor()

#cursor.execute("select * from prova").fetchall()
#cursor.execute("create table prova (nome TEXT,)")
#cursor.execute("delete from ... where ...= ?",(variabile_da_passare))
