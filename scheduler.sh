#!/bin/bash
time=86400 #24h

while true; do
	python3.9 mainbot.py &
	PID=$!
	sleep $time
	kill $PID
	python3.9 autocheck.py
done
