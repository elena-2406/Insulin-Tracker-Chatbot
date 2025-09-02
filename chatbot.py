import os
from dotenv import load_dotenv
import telebot
import time
import firebase_admin
from firebase_admin import credentials, db

load_dotenv()

# Get values from .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
FIREBASE_KEY = os.getenv("FIREBASE_KEY_PATH")

bot = telebot.TeleBot(TOKEN)

#Setting up firebase
cred = credentials.Certificate(FIREBASE_KEY)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://insulin-shot-time-bot-default-rtdb.firebaseio.com/"
})
import time

# Save an injection log
def log_injection(user_id, units, hours):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    ref = db.reference(f"injections/{user_id}")
    ref.push({
        "time": now,
        "units": units,
        "gap_hours": hours
    })
    return now

# Retrieve all logs for a user
def get_user_logs(user_id):
    ref = db.reference(f"injections/{user_id}")
    return ref.get()  # returns dict or None

# Save user settings (optional, like default units or reminders)
def set_user_settings(user_id, settings: dict):
    ref = db.reference(f"settings/{user_id}")
    ref.update(settings)

# Get user settings
def get_user_settings(user_id):
    ref = db.reference(f"settings/{user_id}")
    return ref.get()