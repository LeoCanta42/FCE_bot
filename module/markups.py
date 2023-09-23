from telegram import InlineKeyboardButton,InlineKeyboardMarkup
import sqlite3 as sql
path="~/FCE_bot/module/"

async def general_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Documento Bus", callback_data="1"),
        InlineKeyboardButton("Documento Treni", callback_data="2")],
        [InlineKeyboardButton("Documento Metro", callback_data="3"),
        InlineKeyboardButton("Controlla Linea", callback_data="default")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

async def near_time_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Linee con PARTENZA vicino l'ora scelta", callback_data="near_partenza")],
        [InlineKeyboardButton("Linee con ARRIVO vicino l'ora scelta", callback_data="near_arrivo")],
        [InlineKeyboardButton("Tutte le linee dall'ora di PARTENZA scelta in poi", callback_data="near_partenza2")],
        [InlineKeyboardButton("Tutte le linee da prima all'ora di ARRIVO scelta", callback_data="near_arrivo2")],
        [InlineKeyboardButton("<-- Back   ",callback_data="default")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

async def times_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("5.00", callback_data="5.00"),
        InlineKeyboardButton("6.00", callback_data="6.00")],
        [InlineKeyboardButton("7.00", callback_data="7.00"),
        InlineKeyboardButton("8.00", callback_data="8.00")],
        [InlineKeyboardButton("9.00", callback_data="9.00"),
        InlineKeyboardButton("10.00", callback_data="10.00")],
        [InlineKeyboardButton("11.00", callback_data="11.00"),
        InlineKeyboardButton("12.00", callback_data="12.00")],
        [InlineKeyboardButton("13.00", callback_data="13.00"),
        InlineKeyboardButton("14.00", callback_data="14.00")],
        [InlineKeyboardButton("15.00", callback_data="15.00"),
        InlineKeyboardButton("16.00", callback_data="16.00")],
        [InlineKeyboardButton("17.00", callback_data="17.00"),
        InlineKeyboardButton("18.00", callback_data="18.00")],
        [InlineKeyboardButton("19.00", callback_data="19.00"),
        InlineKeyboardButton("20.00", callback_data="20.00")],
        [InlineKeyboardButton("21.00", callback_data="21.00")],
        [InlineKeyboardButton("<-- Back   ",callback_data="default")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

async def transport_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("BUS", callback_data="bus"),
        InlineKeyboardButton("LITTORINA", callback_data="littorina")],
        [InlineKeyboardButton("QUALSIASI", callback_data="qualsiasi")],
        [InlineKeyboardButton("<-- Back   ",callback_data="general")]
    ]
    markup=InlineKeyboardMarkup(keyboard)
    return markup

async def bus_markup() -> InlineKeyboardMarkup:
    
    step=2 #numero di colonne
    keyboard = []
  
    i=0
    stop_counter=0
    keyboard.append([])
    with sql.connect("fce_lines.db") as connection:
        cursor=connection.cursor()
        stops=cursor.execute("select distinct Nome from Fermate where bus=1 order by Nome").fetchall()
    for curstop in stops:
        stop=curstop[0]
        if(stop_counter>=step): 
            keyboard.append([])
            stop_counter=0
            i+=1
        stop=stop.replace('\n','')
        if len(stop)>20: #questa condizione mi permette di mettere un solo pulsante (e non step colonne) se questo ha un testo lungo
            keyboard.append([])
            i+=1
            stop_counter=step
        keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
        stop_counter+=1
    
    keyboard.append([])
    keyboard[i+1].append(InlineKeyboardButton("<-- Back   ",callback_data="default"))
    markup = InlineKeyboardMarkup(keyboard)
    return markup

async def tr_markup() -> InlineKeyboardMarkup:
    
    step=2 #numero di colonne
    keyboard = []
    
    i=0
    stop_counter=0
    keyboard.append([])
    with sql.connect("fce_lines.db") as connection:
        cursor=connection.cursor()
        stops=cursor.execute("select distinct Nome from Fermate where littorina=1 order by Nome").fetchall()
    for curstop in stops:
        stop=curstop[0]
        if(stop_counter>=step): 
            keyboard.append([])
            stop_counter=0
            i+=1
        stop=stop.replace('\n','')
        if len(stop)>20: #questa condizione mi permette di mettere un solo pulsante (e non step colonne) se questo ha un testo lungo
            keyboard.append([])
            i+=1
            stop_counter=step
        keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
        stop_counter+=1

    keyboard.append([])
    keyboard[i+1].append(InlineKeyboardButton("<-- Back   ",callback_data="default"))
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def extract_cities(stops):
    cities = []
    for stop in stops:
        stop=stop.replace('(','').replace(')','')
        stop_words = stop.split()
        city = ""
        if len(stop_words) == 1:
            city = stop_words[0]
        else:
            old_count=0
            for i in range(len(stop_words)):
                if len(stop_words)==1: #se solo una parola
                    city = " ".join(stop_words)
                    break
                elif " ".join(stop_words[:i+1]) in cities:
                    break # abbiamo già trovato questa città in un'altra fermata
                else:
                    cur_count=0
                    for s in stops:
                        s_words=s.split()
                        if i<len(s_words) and " ".join(stop_words[:i+1]) == " ".join(s_words[:i+1]):
                            cur_count+=1 #di quante e' sotto stringa
                    if cur_count>old_count:
                        old_count=cur_count
                    elif cur_count<old_count: #se prima maggiore e poi minore allora diminuendo vuol dire che non trovo l'associazione massima
                        city = " ".join(stop_words[:i])
                        break
                    elif cur_count==old_count: #se uguale allora e' una fermata unica
                        city = " ".join(stop_words)
                        break
        if city:
            cities.append(city)
    return cities


async def any_markup() -> InlineKeyboardMarkup:
    
    to_put=set()
    with sql.connect("fce_lines.db") as connection:
        cursor=connection.cursor()
        stops=cursor.execute("select distinct Nome from Fermate").fetchall()
    for i in range(len(stops)):
        stops[i]=stops[i][0]

    cities=extract_cities(stops)    
    for city in cities:
        to_put.add(city)

    to_put=sorted(to_put)
    step=2 #numero di colonne
    keyboard = []
    
    i=0
    stop_counter=0
    keyboard.append([])
    for stop in to_put:
        if(stop_counter>=step): 
            keyboard.append([])
            stop_counter=0
            i+=1
        if len(stop)>20: #questa condizione mi permette di mettere un solo pulsante (e non step colonne) se questo ha un testo lungo
            keyboard.append([])
            i+=1
            stop_counter=step

        keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=stop)))
        stop_counter+=1

    keyboard.append([])
    keyboard[i+1].append(InlineKeyboardButton("<-- Back   ",callback_data="default"))
    markup = InlineKeyboardMarkup(keyboard)

    return markup

