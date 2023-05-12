#!/bin/bash
PIDs=( $(pgrep python) )
for i in "${PIDs[@]}"
do :
    kill ${i}    
done

PIDs=( $(pgrep scheduler) )
for i in "${PIDs[@]}"
do :
    kill ${i}    
done

if [ $1 = 'restart' ]; then
    /bin/bash scheduler.sh &
    #nohup solo quando in ssh
fi

if [ $1 = 'pause' ]; then
    python3.9 bot_pause_messages.py &
fi