from module.check_new_urls import download_after_check,check
from module.timetables_operations.extract_excel import locations_to_file
#import schedule
#import time

def job():
    try:
        download_after_check()
        if check(2):
            locations_to_file("bus")
        else:
            print("Nessuna modifica bus !")
        if check(1):
            locations_to_file("littorina")
        else:
            print("Nessuna modifica littorina !")
    except Exception as e:
        print("Errore durante esecuzione job:\n"+str(e))
        

#def checker():
#    schedule.every(2).days.at("01:00").do(job)

#    while True:
#        schedule.run_pending()
#        time.sleep(3000) #circa un'ora


if __name__ == '__main__':
    #checker()
    job()
