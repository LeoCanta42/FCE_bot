#!/bin/bash
startpy=$(head -n 1 ~/FCE_bot/pyvers.txt)

rm ~/FCE_bot/users.db
rm ~/FCE_bot/module/news_check/updated_news.html
echo "" > ~/FCE_bot/module/urls1.txt
echo "" > ~/FCE_bot/module/urls2.txt
echo "" > ~/FCE_bot/module/news_check/updated_news.html
rm -r ~/FCE_bot/module/timetables_operations/bus
rm -r ~/FCE_bot/module/timetables_operations/littorina
mkdir ~/FCE_bot/module/timetables_operations/bus
mkdir ~/FCE_bot/module/timetables_operations/littorina
eval "$startpy ~/FCE_bot/create_users_db.py"
eval "$startpy ~/FCE_bot/autocheck.py"
