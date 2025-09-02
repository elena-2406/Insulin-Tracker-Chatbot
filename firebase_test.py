from firebase_admin import db
import firebase_init  # this imports and initializes firebase

root = db.reference("/")
root.child("sanity_test").set({"hello": "world"})
print("Read:", root.child("sanity_test").get())