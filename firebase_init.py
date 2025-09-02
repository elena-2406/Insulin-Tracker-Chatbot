from firebase_admin import credentials, initialize_app, db

cred = credentials.Certificate("firebase key.json")
initialize_app(cred, {
    "databaseURL": "https://insulin-shot-time-bot-default-rtdb.firebaseio.com/"
})