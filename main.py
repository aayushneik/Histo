import os
import time
import requests
import threading
from flask import Flask
from pymongo import MongoClient

# 🌐 1. MongoDB Connection Settings
# IMPORTANT: Render par 'localhost' kaam nahi karega. Niche apna asli MongoDB Atlas ka link dalein.
# Aap chahein toh Render ke Dashboard par Environment Variables me 'MONGO_URI' naam se bhi ise set kar sakte hain.
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Romeo:pagal0@cluster.mongodb.net/wingo_database?retryWrites=true&w=majority")
DB_NAME = "wingo_database"
COLLECTION_NAME = "history_records"

# 🎮 2. Wingo API Configuration
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://win-go-track.vercel.app"
}

PAYLOAD = {
    "pageIndex": 1,
    "pageSize": 20,
    "type": 1
}

# 🌐 Render ke Port Binding ko pass karne ke liye dummy Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return {
        "status": "Active ✅",
        "message": "Wingo Live Tracker is running smoothly in the background!",
        "platform": "Render Web Service"
    }

def fetch_and_save_live_data():
    """Yeh function background thread me hamesha chalta rahega"""
    print("🚀 Background Tracking Thread Start Ho Gaya Hai...")
    
    while True:
        try:
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            
            response = requests.post(API_URL, json=PAYLOAD, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                records = []
                keys = ['data', 'Data', 'list', 'List', 'result', 'Result']
                for key in keys:
                    if key in result:
                        records = result[key] if isinstance(result[key], list) else result[key].get('list', [])
                        break
                
                if not records and isinstance(result, list):
                    records = result

                if records:
                    inserted_count = 0
                    for item in reversed(records):
                        period_id = item.get("issueNumber") or item.get("IssueNumber") or item.get("period") or item.get("Period")
                        num_raw = item.get("number") if item.get("number") is not None else (item.get("Number") if item.get("Number") is not None else item.get("drawNumber"))
                        color_raw = item.get("color") or item.get("Color") or item.get("colour")

                        if period_id is None or num_raw is None:
                            continue

                        period_str = str(period_id).strip()
                        try:
                            num = int(num_raw)
                        except ValueError:
                            continue

                        size = "big" if num >= 5 else "small"
                        
                        if color_raw:
                            color = str(color_raw).lower().replace(" ", "")
                        else:
                            if num in [1, 3, 7, 9]: color = "green"
                            elif num in [2, 4, 6, 8]: color = "red"
                            elif num == 0: color = "red,violet"
                            elif num == 5: color = "green,violet"
                            else: color = "unknown"

                        formatted_document = {
                            "period": period_str,
                            "number": num,
                            "color": color,
                            "size": size
                        }

                        # Duplicate prevention
                        res = collection.update_one(
                            {"period": period_str},
                            {"$setOnInsert": formatted_document},
                            upsert=True
                        )
                        
                        if res.upserted_id is not None:
                            inserted_count += 1
                            print(f"🆕 Saved: {period_str} | Number: {num}")

                    if inserted_count > 0:
                        print(f"📊 Live Status: {inserted_count} naye periods database me jode gaye.")
                else:
                    print("😴 Live Status: Waiting for next draw...")
            else:
                print(f"❌ API Error: Status code {response.status_code}")
                
            client.close()
        except Exception as e:
            print(f"❌ Error in background thread: {e}")
            
        time.sleep(10) # Har 10 second me check karega

if __name__ == "__main__":
    # 1. Background Tracker Thread ko chalu karna
    tracker_thread = threading.Thread(target=fetch_and_save_live_data, daemon=True)
    tracker_thread.start()
    
    # 2. Render ke diye huye PORT par Flask Web Server ko run karna
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting Flask Web Server on port {port}...")
    app.run(host="0.0.0.0", port=port)
