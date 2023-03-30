from datetime import datetime

async def isTimeFormat(input:str):
    try:
        datetime.strptime(input, "%H.%M")
        return True
    except:
        return False
async def isTimeFormatH(input:str):
    try:
        datetime.strptime(input, "%H")
        return True
    except:
        return False

async def format_time(t:str):
    if len(t)==3: #es: 8.5 viene interpretato come 08.05 quindi aggiungo 0 per fare 8.50
        t=t+'0'
    if await isTimeFormat(t):
        tmp=datetime.strptime(t,"%H.%M")
    elif await isTimeFormatH(t):
        tmp=datetime.strptime(t,"%H")
    
    return str(tmp.strftime("%H.%M"))