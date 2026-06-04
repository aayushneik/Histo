import time
import requests
from pymongo import MongoClient

# 🌐 1. MongoDB Connection Settings
# Agar local h, toh yahi rehne dein. Cloud Atlas ke liye apna connection string dalein.
MONGO_URI = "mongodb+srv://Romeo:pagal0@catch.tfjvhzk.mongodb.net/?appName=Catch"
DB_NAME = "wingo_database"
COLLECTION_NAME = "history_records"

# 🎮 2. Wingo API Configuration
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# Browser jaisa behavior dikhane ke liye fake headers (Taaki website block na kare)
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

def connect_to_mongodb():
    """MongoDB se connect karne ka function"""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME], client

def fetch_and_save_live_data():
    collection, client = connect_to_mongodb()
    
    try:
        # API se direct live data fetch karna
        response = requests.post(API_URL, json=PAYLOAD, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            # API response me se data list dhoondhna (jaise JS me kiya tha)
            records = []
            keys = ['data', 'Data', 'list', 'List', 'result', 'Result']
            for key in keys:
                if key in result:
                    records = result[key] if isinstance(result[key], list) else result[key].get('list', [])
                    break
            
            if not records and isinstance(result, list):
                records = result

            if not records:
                print("⚠️ API se connect hua par koi records nahi mile.")
                return

            inserted_count = 0
            
            # Puraane data se naye ki taraf check karna (Reversed list)
            for item in reversed(records):
                # Alag-alag tarike ke key names handle karna
                period_id = item.get("issueNumber") or item.get("IssueNumber") or item.get("period") or item.get("Period")
                num_raw = item.get("number") if item.get("number") is not None else (item.get("Number") if item.get("Number") is not None else item.get("drawNumber"))
                color_raw = item.get("color") or item.get("Color") or item.get("colour")

                if period_id is None or num_raw is None:
                    continue

                period_str = str(period_id).strip()
                
                # Number parsing aur Size/Color calculation (Exact JavaScript Logic)
                try:
                    num = int(num_raw)
                except ValueError:
                    continue

                size = "big" if num >= 5 else "small"
                
                # Color logic
                if color_raw:
                    color = str(color_raw).lower().replace(" ", "")
                else:
                    if num in [1, 3, 7, 9]:
                        color = "green"
                    elif num in [2, 4, 6, 8]:
                        color = "red"
                    elif num == 0:
                        color = "red,violet"
                    elif num == 5:
                        color = "green,violet"
                    else:
                        color = "unknown"

                # MongoDB ke liye document taiyar karna
                formatted_document = {
                    "period": period_str,
                    "number": num,
                    "color": color,
                    "size": size
                }

                # 🚫 DUPLICATE PREVENTION (Upsert)
                # Agar period database me pehle se h toh kuch nahi karega, nahi h toh naya insert karega
                res = collection.update_one(
                    {"period": period_str},
                    {"$setOnInsert": formatted_document}, # Sirf tab insert hoga jab data naya ho
                    upsert=True
                )
                
                if res.upserted_id is not None:
                    inserted_count += 1
                    print(f"🆕 Saved New Period: {period_str} | Number: {num} | Color: {color} | Size: {size}")

            if inserted_count > 0:
                print(f"📊 Live Status: {inserted_count} naye periods database me jode gaye.")
            else:
                print("😴 Live Status: Koi naya period nahi mila (Waiting for next draw...)")

        else:
            print(f"❌ API Error: Server ne response code {response.status_code} diya.")

    except Exception as e:
        print(f"❌ Fetching ya Database Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Wingo Fully Automated Python Tracker Start Ho Gaya Hai...")
    print("📦 Data direct API se uthakar MongoDB me save ho raha hai. Rokne ke liye Ctrl+C dabayein.\n")
    
    # Infinite loop jo har 10 second me background me chalta rahega
    while True:
        fetch_and_save_live_data()
        time.sleep(10)  # Har 10 second me naya data check karega
