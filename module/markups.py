from telegram import InlineKeyboardButton,InlineKeyboardMarkup

path="./module/"

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

def bus_markup():
    
    step=2 #numero di colonne
    keyboard = []
  
    i=0
    stop_counter=0
    keyboard.append([])
    for stop in open(path+"timetables_operations/bus/locations.txt","r"): 
        if(stop_counter>=step): 
            keyboard.append([])
            stop_counter=0
            i+=1
        stop=stop.replace('\n','')
        keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
        stop_counter+=1

    keyboard[i].append(InlineKeyboardButton("<-- Back   ",callback_data="choose_T"))
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def tr_markup():
    
    step=2 #numero di colonne
    keyboard = []
    
    i=0
    stop_counter=0
    keyboard.append([])
    for stop in open(path+"timetables_operations/littorina/locations.txt","r"): 
        if(stop_counter>=step): 
            keyboard.append([])
            stop_counter=0
            i+=1
        stop=stop.replace('\n','')
        keyboard[i].append((InlineKeyboardButton(str(stop),callback_data=str(stop))))
        stop_counter+=1

    keyboard[i].append(InlineKeyboardButton("<-- Back   ",callback_data="choose_T"))
    markup = InlineKeyboardMarkup(keyboard)
    return markup

