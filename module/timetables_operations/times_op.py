from datetime import datetime

def isTimeFormat(input:str):
    try:
        datetime.strptime(input, "%H.%M")
        return True
    except:
        return False
def isTimeFormatH(input:str):
    try:
        datetime.strptime(input, "%H")
        return True
    except:
        return False

def format_time(t:str):
    splitted_time=t.split('.')
    #es: 8.5 viene interpretato come 08.05 quindi  mi separo in [8,5]
    # se il secondo e' di lunghezza 1 aggiungo 0 per fare 50 e poi unisco
    if len(splitted_time)==2 and len(splitted_time[1])==1: #lo faccio solo se ho H.M, se ho solo H non mi serve
        splitted_time[1]+='0'
        t=splitted_time[0]+'.'+splitted_time[1]
    if isTimeFormat(t):
        tmp=datetime.strptime(t,"%H.%M")
    elif isTimeFormatH(t):
        tmp=datetime.strptime(t,"%H")
    
    return str(tmp.strftime("%H.%M"))
