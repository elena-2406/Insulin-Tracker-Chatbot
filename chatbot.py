import os
from dotenv import load_dotenv
import telebot
import time
import firebase_admin
from firebase_admin import credentials, db
import threading
import re
from datetime import datetime, timedelta
import json
import io
load_dotenv()

# Get values from .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")
DB_URL = "https://insulin-shot-time-bot-default-rtdb.firebaseio.com/"

bot = telebot.TeleBot(TOKEN)

# Setting up firebase
# The credentials.Certificate() method expects a file path string
cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred, {
    "databaseURL": DB_URL
})
import time

DEFAULT_GAP = 4      # default hours between injections
DEFAULT_UNITS = 6    # default insulin units

# Save an injection log
def log_injection(user_id, units, gap_hours):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ref = db.reference(f"injections/{user_id}")
    ref.push({
        "time": now,
        "units": units,
        "gap_hours": gap_hours
    })
    # update next_due
    next_due = (datetime.now() + timedelta(hours=gap_hours)).strftime("%Y-%m-%d %H:%M:%S")
    set_user_settings(user_id, {"next_due": next_due})
    return now

def get_user_logs(user_id):
    ref = db.reference(f"injections/{user_id}")
    return ref.get()

def set_user_settings(user_id, settings: dict):
    ref = db.reference(f"settings/{user_id}")
    ref.update(settings)

def get_user_settings(user_id):
    ref = db.reference(f"settings/{user_id}")
    return ref.get() or {}

def get_next_due(user_id):
    settings = get_user_settings(user_id)
    next_due = settings.get("next_due")
    if next_due:
        return datetime.strptime(next_due, "%Y-%m-%d %H:%M:%S")
    return None

