import telebot
import time
import firebase_admin
from firebase_admin import credentials, db
#Inserting telegram token
TOKEN = "8368529325:AAGNA8gpzkXwSdJyajxWKKC04p_lq-66rxk"
bot = telebot.TeleBot(TOKEN)