#!/bin/bash
#source .venv/bin/activate
h=true
t=true
while true; do
	if $h; then
		kill $PID
		python3.10 mainbot.py &
		PID=$!
		h=false #se e' gia partito non deve ripartire
	fi
	if [ "$(date '+%H:%M')" = "01:00" ]; then #all'1:00 effettuo check di nuovi orari	
		kill $PID
		python3.10 bot_pause_messages.py &
		PID=$!
		python3.10 autocheck.py
		h=true #faccio ripartire il bot
	fi
	sleep 58 #<1 min in modo da beccare sempre
done
