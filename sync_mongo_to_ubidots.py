import pymongo
from streamlit import secrets
import requests
import time
from bson.objectid import ObjectId

# === Config MongoDB ===
MONGO_URI = pymongo.MongoClient(secrets["mongo"]["uri"])  # URI from secrets
client = pymongo.MongoClient(MONGO_URI)
collection = client["braille_db"]["user_data"]

# === Config Ubidots ===
UBIDOTS_TOKEN = (secrets["ubidots"]["token"])  # URI from secrets
DEVICE_LABEL = (secrets["ubidots"]["label"])  # URI from secrets
HEADERS = {
    "X-Auth-Token": UBIDOTS_TOKEN,
    "Content-Type": "application/json"
}
UBIDOTS_URL = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/"

# === Fungsi kirim ke Ubidots ===
def send_to_ubidots(data_id, text, summary):
    payload = {
        "jumlah_kata": len(text.split()),
        "jumlah_kata_ringkasan": len(summary.split()) if summary else 0
    }
    response = requests.post(UBIDOTS_URL, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 201]:
        print(f"✅ Data {data_id} terkirim ke Ubidots")
        # Update data supaya tidak dikirim ulang
        collection.update_one({"_id": ObjectId(data_id)}, {"$set": {"sent_to_ubidots": True}})
    else:
        print(f"❌ Gagal kirim: {response.status_code} {response.text}")

# === Loop terus cek setiap 30 detik ===
print("🔄 Mulai sync MongoDB ➝ Ubidots...")
while True:
    # Ambil data yang belum dikirim
    new_data = collection.find({"sent_to_ubidots": {"$ne": True}})
    
    for doc in new_data:
        send_to_ubidots(str(doc["_id"]), doc.get("text", ""), doc.get("summary", ""))
    
    time.sleep(30)  # cek tiap 30 detik