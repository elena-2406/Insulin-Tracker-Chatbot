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

#REMINDER LOOP

def reminder_loop():
    while True:
        try:
            all_users = db.reference("settings").get()
            if all_users:
                for user_id, settings in all_users.items():
                    next_due = settings.get("next_due")
                    if next_due:
                        next_due_dt = datetime.strptime(next_due, "%Y-%m-%d %H:%M:%S")
                        if datetime.now() >= next_due_dt:
                            bot.send_message(user_id, "⏰ Time to inject your insulin! Reply with /inject <units> <hours> or just type 'Injected X units'.")
                            # postpone next reminder until user confirms
                            new_next = (datetime.now() + timedelta(hours=settings.get("gap_hours", DEFAULT_GAP))).strftime("%Y-%m-%d %H:%M:%S")
                            set_user_settings(user_id, {"next_due": new_next})
        except Exception as e:
            print("Reminder loop error:", e)
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

#BASIC MESSAGES

@bot.message_handler(func=lambda m: True)
def natural_message_handler(message):
    user_id = str(message.chat.id)
    text = message.text.lower()

    # Match "Injected X units"
    match = re.match(r'injected (\d+) units?', text)
    if match:
        units = int(match.group(1))
        settings = get_user_settings(user_id)
        gap_hours = settings.get("gap_hours", DEFAULT_GAP)
        now = log_injection(user_id, units, gap_hours)
        bot.reply_to(message, f"✅ Logged {units} units at {now}. Next reminder in {gap_hours}h.")
        return

    # Match "skipped"
    if 'skipped' in text:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ref = db.reference(f"injections/{user_id}")
        ref.push({"time": now, "units": 0, "gap_hours": 0, "skipped": True})
        bot.reply_to(message, f"⚠️ Logged as skipped at {now}.")
        return
    
#ALL OTHER COMMANDS

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    bot.reply_to(message, "👋 Hey! I'm your insulin reminder bot.\nUse /inject <units> <hours> to log injections.\nCheck /history to see past logs.\nSet defaults with /setunits and /setgap.")

@bot.message_handler(commands=['inject'])
def inject(message):
    user_id = str(message.chat.id)
    parts = message.text.split()
    try:
        if len(parts) >= 3:
            units = int(parts[1])
            gap_hours = int(parts[2])
        else:
            settings = get_user_settings(user_id)
            units = settings.get("default_units", DEFAULT_UNITS)
            gap_hours = settings.get("gap_hours", DEFAULT_GAP)
        now = log_injection(user_id, units, gap_hours)
        bot.reply_to(message, f"✅ Logged {units} units at {now}. Next reminder in {gap_hours}h.")
    except Exception as e:
        bot.reply_to(message, "⚠️ Usage: /inject <units> <hours>\nExample: /inject 6 8")
        print("Error in /inject:", e)

@bot.message_handler(commands=['history'])
def history(message):
    user_id = str(message.chat.id)
    logs = get_user_logs(user_id)
    if not logs:
        bot.reply_to(message, "No injections logged yet.")
        return
    reply = "📝 Injection history:\n"
    for k, v in logs.items():
        if v.get("skipped"):
            reply += f"{v['time']} → Skipped\n"
        else:
            reply += f"{v['time']} → {v['units']} units\n"
    bot.reply_to(message, reply)

@bot.message_handler(commands=['setgap'])
def setgap(message):
    user_id = str(message.chat.id)
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /setgap <hours>\nExample: /setgap 4")
        return
    try:
        gap = int(parts[1])
        set_user_settings(user_id, {"gap_hours": gap})
        bot.reply_to(message, f"✅ Default gap set to {gap} hours.")
    except:
        bot.reply_to(message, "⚠️ Please provide a number for hours.")

@bot.message_handler(commands=['setunits'])
def setunits(message):
    user_id = str(message.chat.id)
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /setunits <units>\nExample: /setunits 6")
        return
    try:
        units = int(parts[1])
        set_user_settings(user_id, {"default_units": units})
        bot.reply_to(message, f"✅ Default units set to {units}.")
    except:
        bot.reply_to(message, "⚠️ Please provide a number for units.")

@bot.message_handler(commands=['next'])
def next_due(message):
    user_id = str(message.chat.id)
    next_time = get_next_due(user_id)
    if not next_time:
        bot.reply_to(message, "No injections logged yet.")
        return
    delta = next_time - datetime.now()
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes = remainder // 60
    bot.reply_to(message, f"⏳ Next injection due in {hours}h {minutes}m at {next_time.strftime('%Y-%m-%d %H:%M:%S')}")