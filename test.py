import os
import telebot
import requests
import string

token = open('/home/leo/fcebot_token.txt','r')
BOT_TOKEN = str(token.read())

bot = telebot.TeleBot(BOT_TOKEN.strip())

def get_news(message):
    #news_page=requests.get(url='https://www.circumetnea.it/category/news/')
    #bot.reply_to(message,news_page.text)
    bot.reply_to(message,'ciao')

@bot.message_handler(commands=['news']) 
def handle_news(message):
    get_news(message)

bot.infinity_polling()