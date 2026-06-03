import requests
import time
import json
import os

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

def start_json_monitoring(json_filename="wingo_history.json"):
    print("🚀 Wingo Live JSON Monitoring Script Shuru Ho Chuka Hai...")
    print(f"📝 Naye periods automatic '{json_filename}' me save hote rahenge.\n")
    
    # Loop hamesha chalta rahega
    while True:
        # 1. Pehle se saved data ko JSON file se read karna (agar file exist karti hai)
        saved_data = []
        saved_periods = set()
        
        if os.path.exists(json_filename) and os.path.getsize(json_filename) > 0:
            try:
                with open(json_filename, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    # Saare purane periods ko set me daalna taaki duplicate check ho sake
                    for entry in saved_data:
                        saved_periods.add(str(entry.get("period")))
            except Exception as e:
                print(f"⚠️ JSON read karne me dikkat aayi (File recover ho rahi hai): {e}")
                saved_data = []

        # 2. Live API se fresh data nikalna
        records = get_wingo_live_data()
        has_new_data = False
        
        if records:
            # Puraane se naye periods ki taraf loop chalana (reversed)
            for item in reversed(records):
                period = item.get('issueNumber') or item.get('IssueNumber') or item.get('period') or item.get('Period')
                num_raw = item.get('number') or item.get('Number') or item.get('drawNumber')
                color_raw = item.get('color') or item.get('Color') or item.get('colour')
                
                if period is None or num_raw is None:
                    continue
                
                period_str = str(period).strip()
                
                # Agar yeh period pehle se JSON me nahi hai, toh add karein
                if period_str not in saved_periods:
                    num = int(num_raw)
                    size = "big" if num >= 5 else "small"
                    
                    # Color fallback logic
                    if color_raw:
                        color = str(color_raw).lower().replace(" ", "")
                    else:
                        if num in [1, 3, 7, 9]: color = "green"
                        elif num in [2, 4, 6, 8]: color = "red"
                        elif num == 0: color = "red,violet"
                        elif num == 5: color = "green,violet"
                        else: color = "unknown"
                    
                    # Naya object banana
                    new_entry = {
                        "period": period_str,
                        "number": num,
                        "color": color,
                        "size": size
                    }
                    
                    # List me append karna
                    saved_data.append(new_entry)
                    saved_periods.add(period_str)
                    has_new_data = True
                    print(f"🆕 New Period Saved in JSON -> {period_str} | Num: {num} | Size: {size}")
            
            # 3. Agar naya data mila hai, toh file ko naye format me rewrite karna
            if has_new_data:
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(saved_data, f, indent=4, ensure_ascii=False)
                    
        # Har 5 second me server check karega
        time.sleep(5)

if __name__ == "__main__":
    start_json_monitoring()