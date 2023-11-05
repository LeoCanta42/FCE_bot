from module.timetables_operations.db import set_db_users
import sqlite3 as sql

with sql.connect("users.db") as connection:
    set_db_users(connection)
