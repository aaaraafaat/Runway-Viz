import requests
import sys
import re
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Updated ICAO codes – VGHS for Dhaka instead of VGZR
AIRFIELDS = ['VGHS', 'VGEG', 'VGSY', 'VGJR']
CROSSWIND_LIMIT = 12
VISIBILITY_LIMIT = 5

def fetch_metar_checkwx(icao, api_key):
    url = f"https://api.checkwx.com/metar/{icao}/decoded"
    headers = {"X-API-Key": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get('results', 0) > 0:
                return data['data'][0].get('raw_text', '')
    except:
        pass
    return None

def fetch_metar_noaa(icao):
    url = f"https://aviationweather.gov/cgi-bin/data/metar.php?ids={icao}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and resp.text.strip() and "No data" not in resp.text:
            return resp.text.strip()
    except:
        pass
    return None

def fetch_metar(icao):
    api_key = os.environ.get("CHECKWX_API_KEY")
    if api_key:
        metar = fetch_metar_checkwx(icao, api_key)
        if metar:
            return metar
    return fetch_metar_noaa(icao)

def parse_metar(metar):
    wind_match = re.search(r'(\d{3})(\d{2})KT', metar)
    if wind_match:
        wind_dir = int(wind_match.group(1))
        wind_speed = int(wind_match.group(2))
    else:
        wind_dir = None
        wind_speed = 0
    vis_match = re.search(r'(\d{4}) ', metar)
    if vis_match:
        vis_miles = int(vis_match.group(1)) / 1609.34
    else:
        vis_miles = 10
    alerts = []
    if wind_speed > CROSSWIND_LIMIT:
        alerts.append(f"CROSSWIND ALERT: {wind_speed} kts (limit {CROSSWIND_LIMIT})")
    if vis_miles < VISIBILITY_LIMIT:
        alerts.append(f"LOW VISIBILITY: {vis_miles:.1f} miles (limit {VISIBILITY_LIMIT})")
    has_ts = 'TS' in metar or 'TSRA' in metar
    return {
        'wind_speed': wind_speed,
        'wind_dir': wind_dir,
        'visibility': round(vis_miles, 1),
        'alerts': alerts,
        'has_thunderstorm': has_ts,
        'raw': metar[:100]
    }

def generate_report():
    lines = ["=== Runway Viz Report ===", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"]
    for icao in AIRFIELDS:
        metar = fetch_metar(icao)
        if metar:
            wx = parse_metar(metar)
            status = "SAFE" if not wx['alerts'] else "ALERT"
            lines.append(f"\n{icao}: {status}")
            lines.extend(wx['alerts'])
            wind_str = f"{wx['wind_speed']} kts"
            if wx['wind_dir']:
                wind_str += f" {wx['wind_dir']}°"
            lines.append(f"   Wind: {wind_str} | Vis: {wx['visibility']} mi")
            if wx['has_thunderstorm']:
                lines.append("   ⛈️ Thunderstorm reported")
            lines.append(f"   Raw METAR: {wx['raw']}...")
        else:
            lines.append(f"\n{icao}: FETCH FAILED - no METAR data")
    return "\n".join(lines)

if __name__ == "__main__":
    import os
    try:
        report = generate_report()
        print(report)
        with open("latest_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        print("\n[SUCCESS] Report saved")
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)