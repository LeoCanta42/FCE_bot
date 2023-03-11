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

def transport_markup():
    keyboard = [
        [InlineKeyboardButton("Bus", callback_data="bus"),
        InlineKeyboardButton("Littorina", callback_data="lit")],
        [InlineKeyboardButton("<-- Back   ",callback_data="choose_T")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def am_pm_markup():
    keyboard = [
        [InlineKeyboardButton("AM", callback_data="am"),
        InlineKeyboardButton("PM", callback_data="pm")],
        [InlineKeyboardButton("<-- Back   ",callback_data="general")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def am_times_markup():
    keyboard = [
        [InlineKeyboardButton("5:00", callback_data="5:00"),
        InlineKeyboardButton("5:30", callback_data="5:30")],
        [InlineKeyboardButton("6:00", callback_data="6:00"),
        InlineKeyboardButton("6:30", callback_data="6:30")],
        [InlineKeyboardButton("7:00", callback_data="7:00"),
        InlineKeyboardButton("7:30", callback_data="7:30")],
        [InlineKeyboardButton("8:00", callback_data="8:00"),
        InlineKeyboardButton("8:30", callback_data="8:30")],
        [InlineKeyboardButton("9:00", callback_data="9:00"),
        InlineKeyboardButton("9:30", callback_data="9:30")],
        [InlineKeyboardButton("10:00", callback_data="10:00"),
        InlineKeyboardButton("10:30", callback_data="10:30")],
        [InlineKeyboardButton("11:00", callback_data="11:00"),
        InlineKeyboardButton("11:30", callback_data="11:30")],
        [InlineKeyboardButton("<-- Back   ",callback_data="choose_T")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def pm_times_markup():
    keyboard = [
        [InlineKeyboardButton("12:00", callback_data="12:00"),
        InlineKeyboardButton("12:30", callback_data="12:30")],
        [InlineKeyboardButton("13:00", callback_data="13:00"),
        InlineKeyboardButton("13:30", callback_data="13:30")],
        [InlineKeyboardButton("14:00", callback_data="14:00"),
        InlineKeyboardButton("14:30", callback_data="14:30")],
        [InlineKeyboardButton("15:00", callback_data="15:00"),
        InlineKeyboardButton("15:30", callback_data="15:30")],
        [InlineKeyboardButton("16:00", callback_data="16:00"),
        InlineKeyboardButton("16:30", callback_data="16:30")],
        [InlineKeyboardButton("17:00", callback_data="17:00"),
        InlineKeyboardButton("17:30", callback_data="17:30")],
        [InlineKeyboardButton("18:00", callback_data="18:00"),
        InlineKeyboardButton("18:30", callback_data="18:30")],
        [InlineKeyboardButton("19:00", callback_data="19:00"),
        InlineKeyboardButton("19:30", callback_data="19:30")],
        [InlineKeyboardButton("20:00", callback_data="20:00")],
        [InlineKeyboardButton("<-- Back   ",callback_data="choose_T")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

