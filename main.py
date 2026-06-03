import requests
import time
import json
import os
from threading import Thread
from flask import Flask, send_file, jsonify

# ---- FLASK SERVER SETUP ----
app = Flask(__name__)

# '/' aur '/data' dono par strict_slashes=False lagaya hai taaki trailing slash se error na aaye
@app.route('/', strict_slashes=False)
def home():
    return "🚀 Wingo Live Tracker is Running Successfully!<br><br>👉 Apni JSON file dekhne ke liye URL ke aakhiri me <b>/data</b> lagayein."

@app.route('/data', strict_slashes=False)
def download_file():
    json_filename = "wingo_history.json"
    if os.path.exists(json_filename):
        return send_file(json_filename, mimetype='application/json')
    else:
        # Agar file abhi tak nahi bani hai, toh 404 ke bajaye khali list dikhayega
        return jsonify([])

# ---- WINGO LIVE TRACKER CODE ----
def get_wingo_live_data():
    url = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    payload = {
        "pageIndex": 1,
        "pageSize": 20,
        "type": 1
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        if response.status_code in [405, 400]:
            response = requests.get(url, headers=headers, timeout=8)
            
        if response.status_code == 200:
            data = response.json()
            for key in ['data', 'Data', 'list', 'List', 'result', 'Result']:
                if key in data:
                    if isinstance(data[key], list):
                        return data[key]
                    elif isinstance(data[key], dict) and 'list' in data[key]:
                        return data[key]['list']
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"📡 Network/API Error: {e}")
    return []

def start_json_monitoring():
    json_filename = "wingo_history.json"
    print("🚀 Wingo Live JSON Monitoring Background Me Shuru Ho Gaya Hai...")
    
    while True:
        saved_data = []
        saved_periods = set()
        
        if os.path.exists(json_filename) and os.path.getsize(json_filename) > 0:
            try:
                with open(json_filename, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    for entry in saved_data:
                        saved_periods.add(str(entry.get("period")))
            except Exception as e:
                saved_data = []

        records = get_wingo_live_data()
        has_new_data = False
        
        if records:
            for item in reversed(records):
                period = item.get('issueNumber') or item.get('IssueNumber') or item.get('period') or item.get('Period')
                num_raw = item.get('number') or item.get('Number') or item.get('drawNumber')
                color_raw = item.get('color') or item.get('Color') or item.get('colour')
                
                if period is None or num_raw is None:
                    continue
                
                period_str = str(period).strip()
                
                if period_str not in saved_periods:
                    num = int(num_raw)
                    size = "big" if num >= 5 else "small"
                    
                    if color_raw:
                        color = str(color_raw).lower().replace(" ", "")
                    else:
                        if num in [1, 3, 7, 9]: color = "green"
                        elif num in [2, 4, 6, 8]: color = "red"
                        elif num == 0: color = "red,violet"
                        elif num == 5: color = "green,violet"
                        else: color = "unknown"
                    
                    new_entry = {
                        "period": period_str,
                        "number": num,
                        "color": color,
                        "size": size
                    }
                    
                    saved_data.append(new_entry)
                    saved_periods.add(period_str)
                    has_new_data = True
                    print(f"🆕 Saved -> {period_str}")
            
            if has_new_data:
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(saved_data, f, indent=4, ensure_ascii=False)
                    
        time.sleep(5)

# 🚀 [SUPER HACK]: Yeh background thread script load hote hi automatic chalu ho jayegi
monitor_thread = Thread(target=start_json_monitoring)
monitor_thread.daemon = True
monitor_thread.start()

if __name__ == "__main__":
    # Agar local ya python command se chale toh port bind karein
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
