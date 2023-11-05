#!/bin/bash
startpy=$(head -n 1 ~/FCE_bot/pyvers.txt)

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
    /bin/bash ~/FCE_bot/scheduler.sh check &
fi

if [ $1 = 'pause' ]; then
    source ~/FCE_bot/.venv/bin/activate
    eval "$startpy ~/FCE_bot/bot_pause_messages.py &"
fi
