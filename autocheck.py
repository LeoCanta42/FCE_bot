import telegram
from mainbot import token as tt
import sqlite3 as sql
import module.timetables_operations.db as db
from module.timetables_operations.extract_excel import load,locations_to_file
from module.check_new_urls import download_after_check

bot=telegram.Bot(token=tt)

def job() -> bool:
    try:
        return download_after_check()
    except Exception as e:
        print("Errore durante esecuzione job:\n"+str(e))
        return False


if __name__ == '__main__':
    if job():
        load("bus")
        load("littorina")
        locations_to_file("bus")
        locations_to_file("littorina")
        with sql.connect("fce_lines.db") as connection:
            db.reset(connection)
            db.set_db(connection)
            db.insert_fermate(connection)
            db.insert_tratte(connection)
    with sql.connect("users.db") as connection:
        db.check_dbuser(connection)