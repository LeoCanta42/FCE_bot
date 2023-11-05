#!/bin/bash
source ~/FCE_bot/.venv/bin/activate
h=true
startpy=$(head -n 1 ~/FCE_bot/pyvers.txt)

if [ $1 = 'check' ]; then
    eval "$startpy ~/FCE_bot/autocheck.py"
fi

while true; do
	if $h; then
		kill $PID1
		eval "$startpy ~/FCE_bot/mainbot.py &" #bot principale
		PID1=$!
		eval "$startpy ~/FCE_bot/bot_news_sender.py &" #bot notizie
		PID2=$!
		h=false #se e' gia partito non deve ripartire
	fi
	sleep 58 #<1 min in modo da beccare sempre
	if [ "$(date '+%H:%M')" = "01:00" ]; then #all'1:00 effettuo check di nuovi orari	
		kill $PID1
		kill $PID2
		eval "$startpy ~/FCE_bot/FCE_bot/bot_pause_messages.py &" #bot quando bot in pausa
		PID1=$!
		eval "$startpy ~/FCE_bot/autocheck.py"
		h=true #faccio ripartire il bot
	fi
done
