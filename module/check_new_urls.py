from module.retrieve_webdata import getdownload_urls
from module.timetables_operations.convert_excel import download_converted
from module.timetables_operations.extract_excel import locations_to_file
import shutil,os
import asyncio

def check(type:int) -> bool: #1 littorina 2 bus
    h=False
    for urls in asyncio.run(getdownload_urls(type)):
        if urls not in open("~/FCE_bot/module/urls"+str(type)+".txt","r").read().strip():
            h=True
    if type==1: t="littorina"
    elif type==2: t="bus"
    if not h: print("Nessuna modifica "+t+" !")
    
    return h

def clean_folders(type:int) -> None:
    if type==1:
        shutil.rmtree("~/FCE_bot/module/timetables_operations/littorina")
        os.mkdir("~/FCE_bot/module/timetables_operations/littorina")
    elif type==2:
        shutil.rmtree("~/FCE_bot/module/timetables_operations/bus")
        os.mkdir("~/FCE_bot/module/timetables_operations/bus")


def download_after_check() -> bool:
    changed=False
    for type in range(1,3):
        if(check(type)):
            clean_folders(type)
            i=0
            with open("~/FCE_bot/module/urls"+str(type)+".txt","w") as f:
                for url in  asyncio.run(getdownload_urls(type)):
                    if type==1:
                        t="littorina"
                    elif type==2:
                        t="bus"
                    download_converted(url,"~/FCE_bot/module/timetables_operations/"+t+"/orario"+str(i)+".xlsx")
                    f.write(str(url)+"\n")
                    i+=1
            locations_to_file(t)
            changed=True
        else:
            break
    return changed
                