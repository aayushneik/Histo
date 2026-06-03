import requests
import time
import json
import os
from threading import Thread
from flask import Flask, send_file, jsonify

# ---- GLOBAL VARIABLES FOR LIVE DEBUGGING ----
DEBUG_INFO = {
    "last_check_time": "Never",
    "api_status_code": "None",
    "last_error": "No error yet",
    "total_saved_periods": 0,
    "raw_api_sample": "No data fetched yet"
}

app = Flask(__name__)

# 📊 Home Page ab aapko poori live report dikhayega ki peeche kya chal raha hai
@app.route('/', strict_slashes=False)
def home():
    status_html = f"""
    <html>
    <head><title>Wingo Tracker Dashboard</title></head>
    <body style="font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333;">
        <h1 style="color: #2c3e50;">🚀 Wingo Live Tracker Status</h1>
        <hr>
        <h3>📊 Current Status:</h3>
        <ul>
            <li><b>Last Checked At:</b> {DEBUG_INFO['last_check_time']}</li>
            <li><b>API Response Code:</b> <span style="color: blue;">{DEBUG_INFO['api_status_code']}</span></li>
            <li><b>Total Periods Saved:</b> <span style="color: green; font-weight: bold;">{DEBUG_INFO['total_saved_periods']}</span></li>
            <li><b>Last Error/Warning:</b> <span style="color: red;">{DEBUG_INFO['last_error']}</span></li>
        </ul>
        <hr>
        <h3>📁 Data Links:</h3>
        <p>👉 Apni JSON File dekhne ke liye yahan click karein: <a href="/data" target="_blank">/data</a></p>
        <hr>
        <h3>📡 Raw API Sample (Peeche se kya data aa raha hai):</h3>
        <pre style="background: #e8ecef; padding: 15px; border-radius: 5px; overflow-x: auto;">{DEBUG_INFO['raw_api_sample']}</pre>
    </body>
    </html>
    """
    return status_html

@app.route('/data', strict_slashes=False)
def download_file():
    json_filename = "wingo_history.json"
    if os.path.exists(json_filename) and os.path.getsize(json_filename) > 0:
        return send_file(json_filename, mimetype='application/json')
    else:
        return jsonify({"status": "error", "message": "File khali hai ya abhi tak koi naya period save nahi hua."})

# ---- AAPKA WINGO LIVE TRACKER CODE WITH DEBUG LOGGING ----
def get_wingo_live_data():
    url = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    payload = {"pageIndex": 1, "pageSize": 20, "type": 1}
    
    DEBUG_INFO["last_check_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Dono tarike try karenge (POST aur GET) agar koi ek block ho raha ho
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        DEBUG_INFO["api_status_code"] = str(response.status_code)
        
        if response.status_code != 200:
            # Try GET
            response = requests.get(url, params=payload, headers=headers, timeout=8)
            DEBUG_INFO["api_status_code"] = f"GET Mode: {response.status_code}"
            
        if response.status_code == 200:
            try:
                data = response.json()
                # Save sample for user to see on dashboard
                DEBUG_INFO["raw_api_sample"] = json.dumps(data, indent=2)[:800]
                DEBUG_INFO["last_error"] = "None (Success)"
                
                for key in ['data', 'Data', 'list', 'List', 'result', 'Result']:
                    if key in data:
                        if isinstance(data[key], list): return data[key]
                        elif isinstance(data[key], dict) and 'list' in data[key]: return data[key]['list']
                if isinstance(data, list): return data
            except Exception as json_err:
                DEBUG_INFO["raw_api_sample"] = response.text[:500]
                DEBUG_INFO["last_error"] = f"JSON Parsing Error: {json_err}"
        else:
            DEBUG_INFO["raw_api_sample"] = response.text[:500]
            DEBUG_INFO["last_error"] = f"Server returned error code: {response.status_code}"
            
    except Exception as e:
        DEBUG_INFO["api_status_code"] = "FAILED"
        DEBUG_INFO["last_error"] = f"Connection Error: {e}"
        
    return []

def start_json_monitoring():
    json_filename = "wingo_history.json"
    
    while True:
        saved_data = []
        saved_periods = set()
        
        if os.path.exists(json_filename) and os.path.getsize(json_filename) > 0:
            try:
                with open(json_filename, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    for entry in saved_data:
                        saved_periods.add(str(entry.get("period")))
            except Exception:
                saved_data = []

        DEBUG_INFO["total_saved_periods"] = len(saved_periods)
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
            
            if has_new_data:
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(saved_data, f, indent=4, ensure_ascii=False)
                DEBUG_INFO["total_saved_periods"] = len(saved_periods)
                    
        time.sleep(5)

# Background Thread Automatic Start
monitor_thread = Thread(target=start_json_monitoring)
monitor_thread.daemon = True
monitor_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)        if os.path.exists(json_filename) and os.path.getsize(json_filename) > 0:
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
