#!/bin/bash
time=86400 #24h

#source .venv/bin/activate
while true; do
	python3.10 autocheck.py
	python3.10 mainbot.py &
	PID=$!
	sleep $time
	kill $PID
done
