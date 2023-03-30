from module.retrieve_webdata import getdownload_urls
from module.timetables_operations.convert_excel import download_converted
from module.timetables_operations.extract_excel import locations_to_file
import shutil,os
import asyncio

def check(type:int): #1 littorina 2 bus
    h=True
    for oldurl in open("./module/urls"+str(type)+".txt","r"):
        if oldurl not in asyncio.run(getdownload_urls(type)):
            h=False
    if type==1: t="littorina"
    elif type==2: t="bus"
    if not h: print("Nessuna modifica "+t+" !")
    
    return h

def clean_folders(type:int):
    if type==1:
        shutil.rmtree("./module/timetables_operations/littorina")
        os.mkdir("./module/timetables_operations/littorina")
    elif type==2:
        shutil.rmtree("./module/timetables_operations/bus")
        os.mkdir("./module/timetables_operations/bus")


def download_after_check():
    for type in range(1,3):
        if(check(type)):
            clean_folders(type)
            i=0
            with open("./module/urls"+str(type)+".txt","w") as f:
                for url in  asyncio.run(getdownload_urls(type)):
                    if type==1:
                        t="littorina"
                    elif type==2:
                        t="bus"
                    download_converted(url,"./module/timetables_operations/"+t+"/orario"+str(i)+".xlsx")
                    f.write(str(url)+"\n")
                    i+=1
            locations_to_file(t)
                