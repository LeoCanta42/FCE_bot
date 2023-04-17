#!/bin/bash
rm users.db
rm module/news_check/updated_news.html
echo "" > module/urls1.txt
echo "" > module/urls2.txt
rm -r module/timetables_operations/bus
rm -r module/timetables_operations/littorina
mkdir module/timetables_operations/bus
mkdir module/timetables_operations/littorina
python3.10 create_users_db.py
python3.10 autocheck.py
