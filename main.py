import requests
import json
import os
from flask import Flask, send_file, jsonify, render_template_string

app = Flask(__name__)
JSON_FILENAME = "wingo_history.json"

# ---- LIVE API SE DATA NIKALNE KA LOGIC ----
def fetch_and_update_data():
    url = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    payload = {"pageIndex": 1, "pageSize": 20, "type": 1}
    
    # 1. Pehle se saved data load karein
    saved_data = []
    saved_periods = set()
    
    if os.path.exists(JSON_FILENAME) and os.path.getsize(JSON_FILENAME) > 0:
        try:
            with open(JSON_FILENAME, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                for entry in saved_data:
                    saved_periods.add(str(entry.get("period")))
        except Exception:
            saved_data = []

    # 2. Fresh Live API Call
    api_status = "Unknown"
    api_error = "None"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        api_status = str(response.status_code)
        
        if response.status_code != 200:
            response = requests.get(url, params=payload, headers=headers, timeout=8)
            api_status = f"GET Mode: {response.status_code}"
            
        if response.status_code == 200:
            data = response.json()
            records = []
            
            # Key finding dynamically
            for key in ['data', 'Data', 'list', 'List', 'result', 'Result']:
                if key in data:
                    if isinstance(data[key], list): records = data[key]
                    elif isinstance(data[key], dict) and 'list' in data[key]: records = data[key]['list']
            if not records and isinstance(data, list): 
                records = data
                
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
                    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
                        json.dump(saved_data, f, indent=4, ensure_ascii=False)
        else:
            api_error = f"Server returned {response.status_code}"
    except Exception as e:
        api_status = "FAILED"
        api_error = str(e)
        
    return saved_data, api_status, api_error

# 🏠 1. LIVE DASHBOARD PAGE
@app.route('/', strict_slashes=False)
def home():
    data_list, status, error = fetch_and_update_data()
    
    # Sirf aakhiri ke 5 records dashboard par live dekhne ke liye
    latest_records = data_list[-5:] if data_list else []
    latest_records.reverse() # Taaki sabse naya upar dikhe
    
    table_rows = ""
    for item in latest_records:
        table_rows += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">{item['period']}</td>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight:bold;">{item['number']}</td>
            <td style="padding: 10px; border: 1px solid #ddd;"><span style="background:#e0e0e0; padding:3px 8px; border-radius:4px;">{item['color']}</span></td>
            <td style="padding: 10px; border: 1px solid #ddd; text-transform: uppercase;">{item['size']}</td>
        </tr>
        """
        
    if not table_rows:
        table_rows = "<tr><td colspan='4' style='padding:10px; text-align:center; color:gray;'>Abhi tak koi data save nahi hua. Refresh karein!</td></tr>"

    html_template = f"""
    <html>
    <head>
        <title>Wingo Real-time Dashboard</title>
        <meta http-equiv="refresh" content="10"> </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 30px; background-color: #f7f9fc;">
        <div style="max-width: 900px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <h1 style="color: #1e3a8a; margin-top: 0;">🎮 Wingo Live Tracker Panel</h1>
            <p style="color: #64748b;">Yeh page har 10 second me automatic refresh hokar live data check aur save karta hai.</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            
            <div style="display: flex; gap: 20px; margin-bottom: 25px;">
                <div style="flex: 1; background: #eff6ff; padding: 15px; border-radius: 8px; border-left: 5px solid #3b82f6;">
                    <b style="color: #1e40af;">API Status:</b> <span style="color:#2563eb;">{status}</span>
                </div>
                <div style="flex: 1; background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 5px solid #10b981;">
                    <b style="color: #065f46;">Total Saved Periods:</b> <span style="font-size: 18px; font-weight: bold; color:#059669;">{len(data_list)}</span>
                </div>
            </div>

            {f'<div style="background:#fef2f2; color:#991b1b; padding:10px; border-radius:6px; margin-bottom:15px;"><b>Error Note:</b> {error}</div>' if error != "None" else ""}

            <div style="margin-bottom: 25px;">
                <a href="/data" target="_blank" style="display: inline-block; background: #10b981; color: white; padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; box-shadow: 0 2px 5px rgba(16,185,129,0.3);">📥 Poori JSON File Download/View Karein</a>
            </div>

            <h3 style="color: #334155;">⏱️ Latest 5 Live Generations:</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; background: #fff;">
                <thead>
                    <tr style="background: #f1f5f9; color: #475569;">
                        <th style="padding: 12px; border: 1px solid #ddd;">Period ID</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Number</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Color</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Size</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

# 📁 2. RAW DATA DOWNLOAD LINK
@app.route('/data', strict_slashes=False)
def download_file():
    # Jab koi /data kholega tab bhi instant live update hoga taaki naya data miss na ho
    data_list, _, _ = fetch_and_update_data()
    if os.path.exists(JSON_FILENAME) and os.path.getsize(JSON_FILENAME) > 0:
        return send_file(JSON_FILENAME, mimetype='application/json')
    else:
        return jsonify([])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
