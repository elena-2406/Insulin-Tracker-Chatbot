import os
from dotenv import load_dotenv
import telebot

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

print("Token loaded:", TOKEN)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Bot is alive ✅")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    print("Received:", message.text)
    bot.reply_to(message, "Echo: " + message.text)

print("Bot polling now...")
bot.infinity_polling()