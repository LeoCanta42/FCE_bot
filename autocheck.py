import telegram
from mainbot import token as tt
import sqlite3 as sql
import module.timetables_operations.db as db
from module.timetables_operations.extract_excel import load
from module.check_new_urls import download_after_check

bot=telegram.Bot(token=tt)

def job():
    try:
        return download_after_check()
    except Exception as e:
        print("Errore durante esecuzione job:\n"+str(e))
        return False


if __name__ == '__main__':
    if job():
        load("bus")
        load("littorina")
        with sql.connect("fce_lines.db") as connection:
            db.reset(connection)
            db.set_db(connection)
            db.insert_fermate(connection)
            db.insert_tratte(connection)
