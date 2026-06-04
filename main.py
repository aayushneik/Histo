import os
import time
import requests
import threading
from flask import Flask, render_template_string
from pymongo import MongoClient

# 🌐 1. MongoDB Connection Settings
# NOTE: 'abcde' ko mita kar apne MongoDB Atlas ka asli cluster ID daalna mat bhoolna!
MONGO_URI = "mongodb+srv://Romeo:pagal0123@cluster0.tfjvhzk.mongodb.net/wingo_database?retryWrites=true&w=majority"
DB_NAME = "wingo_database"
COLLECTION_NAME = "history_records"

# 🎮 2. Wingo API & Proxy Configuration
_PROXY_URL = "https://api.codetabs.com/v1/proxy?quest="
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# Dono URLs ko jodh kar final proxy URL banana
FINAL_REQUEST_URL = _PROXY_URL + API_URL

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

# Live status track karne ke liye global variable
live_status = {"status": "Starting...", "total_saved_db": 0, "last_check": "Never"}

app = Flask(__name__)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Wingo MongoDB Tracker Status</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; text-align: center; padding: 50px; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #334155; }
        h1 { color: #38bdf8; }
        .status { font-size: 1.5rem; font-weight: bold; color: #10b981; margin: 20px 0; }
        .info { color: #94a3b8; font-size: 1.1rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📊 Wingo To MongoDB Live Tracker</h1>
        <p class="status">Status: {{ data.status }}</p>
        <p class="info">Total Records in MongoDB: <strong>{{ data.total_saved_db }}</strong></p>
        <p class="info">Last Checked: {{ data.last_check }}</p>
        <p style="color: #64748b; font-size: 0.85rem; margin-top: 20px;">Proxy Mode: ON (Codetabs)</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        client = MongoClient(MONGO_URI)
        count = client[DB_NAME][COLLECTION_NAME].count_documents({})
        live_status["total_saved_db"] = count
        client.close()
    except Exception:
        pass
    return render_template_string(HTML_DASHBOARD, data=live_status)

def fetch_and_save_live_data():
    print("🚀 Background Tracking Started with Proxy...")
    while True:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        live_status["last_check"] = current_time
        
        try:
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            
            # 🔄 Proxy URL par POST request bhejna
            response = requests.post(FINAL_REQUEST_URL, json=PAYLOAD, headers=HEADERS, timeout=15)
            
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

                        res = collection.update_one(
                            {"period": period_str},
                            {"$setOnInsert": formatted_document},
                            upsert=True
                        )
                        
                        if res.upserted_id is not None:
                            inserted_count += 1

                    live_status["status"] = "Active ✅ (Running via Proxy)"
                else:
                    live_status["status"] = "Connected via Proxy ✅ (Waiting for next draw...)"
            else:
                live_status["status"] = f"Proxy/API Error ❌ (Status: {response.status_code})"
                
            client.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            live_status["status"] = f"DB Error ❌ (Check Cluster ID/IP Whitelist)"
            
        time.sleep(10)

if __name__ == "__main__":
    tracker_thread = threading.Thread(target=fetch_and_save_live_data, daemon=True)
    tracker_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
