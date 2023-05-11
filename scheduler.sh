#!/bin/bash
#source .venv/bin/activate
h=true

while true; do
        if $h; then
                kill $PID1
                python3.10 mainbot.py & #bot principale
                PID1=$!
                python3.10 bot_news_sender.py & #bot notizie
                PID2=$!
                h=false #se e' gia partito non deve ripartire
        fi
        if [ "$(date '+%H:%M')" = "01:00" ]; then #all'1:00 effettuo check di n>
                kill $PID1
                kill $PID2
                python3.10 bot_pause_messages.py & #bot quando bot in pausa
                PID1=$!
                python3.10 autocheck.py
                h=true #faccio ripartire il bot
        fi
        if [ "$(date '+%H:%M')" = "02:00" ]; then #alle 2 riavvio
                sudo reboot
        fi
        sleep 58 #<1 min in modo da beccare sempre
done

