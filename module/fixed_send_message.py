from telegram import constants

max_len=int(constants.MessageLimit.MAX_TEXT_LENGTH)

def fix_message(string) -> list:
    to_send=[]
    #if len(string)>int(constants.MessageLimit.MAX_TEXT_LENGTH): 
     
    #dato che alcuni messaggi potrebbero sforare la lungezza massima creiamo una lista di stringhe
    while len(string)>0:
        if len(string)>max_len:
            tosend_string=string[:max_len]
            final_newline=tosend_string.rfind('\n')
            tosend_string=tosend_string[:final_newline]
            to_send.append(tosend_string)
            string=string[final_newline+1:]
        else:
            to_send.append(string)
            string=""    
    
    return to_send
