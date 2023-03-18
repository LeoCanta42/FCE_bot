#from retrieve_webdata import getdownload_urls
from telegram import InlineKeyboardButton,InlineKeyboardMarkup


def general_markup():
    keyboard = [
        [InlineKeyboardButton("Orario bus", callback_data="1"),
        InlineKeyboardButton("Orario treni", callback_data="2")],
        [InlineKeyboardButton("Orario metro", callback_data="3"),
        InlineKeyboardButton("Controlla orario vicino", callback_data="choose_T")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def times_markup():
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
        [InlineKeyboardButton("<-- Back   ",callback_data="general")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def transport_markup():
    keyboard = [
        [InlineKeyboardButton("BUS", callback_data="bus"),
        InlineKeyboardButton("LITTORINA", callback_data="littorina")],
        [InlineKeyboardButton("<-- Back   ",callback_data="choose_T")]
    ]
    markup=InlineKeyboardMarkup(keyboard)
    return markup

def index_t_b():
    index_train=0
    c=0
    for stop in open("./module/timetables_operations/locations.txt"): 
        if stop=="TR\n":
            index_train=c
        c+=1
    
    arr=[index_train,c] 
    return arr

def bus_markup():
    
    index=index_t_b()    
    count_loc=index[0]-1 #numero di fermate bus (indice TR-1)

    keyboard = [[] for i in range(count_loc+1)]
    step=1
    i=0
    stop_counter=0
    c=0
    for stop in open("./module/timetables_operations/locations.txt","r"): 
        if c<=count_loc:
            if(stop_counter>=step): 
                stop_counter=0
                i+=1
            stop=stop.replace('\n','')
            keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
            stop_counter+=1
        if c>count_loc:
            break
        c+=1
    keyboard[i].append(InlineKeyboardButton("<-- Back   ",callback_data="choose_T"))

    markup = InlineKeyboardMarkup(keyboard)
    return markup

def tr_markup():
    
    index=index_t_b()    
    count_loc=index[1]-1 #da tr a totale

    keyboard = [[] for i in range(count_loc-index[0]+1)]
    step=1
    i=0
    stop_counter=0
    c=0
    for stop in open("./module/timetables_operations/locations.txt","r"): 
        if c>index[0] and c<=count_loc:
            if(stop_counter>=step): 
                stop_counter=0
                i+=1
            stop=stop.replace('\n','')
            keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
            stop_counter+=1
        if c>count_loc:
            break
        c+=1
    keyboard[i].append(InlineKeyboardButton("<-- Back   ",callback_data="choose_T"))
    markup = InlineKeyboardMarkup(keyboard)
    return markup
