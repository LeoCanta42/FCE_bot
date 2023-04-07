import sqlite3 as sql

with sql.connect("users.db") as connection:
	cursor=connection.cursor()
	res=cursor.execute("select * from Users").fetchall()
	print(res)
