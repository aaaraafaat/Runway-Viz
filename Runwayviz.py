import requests
import os
import sys
import time
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

AIRFIELDS = ['VGZR', 'VGEG', 'VGSY', 'VGJR']  # Dhaka, Chittagong, Sylhet, Jessore
CROSSWIND_LIMIT_KNOTS = 12
VISIBILITY_LIMIT_MILES = 5

def fetch_metar_checkwx(icao, api_key):
    """Fetch METAR from CheckWX API (requires API key)"""
    url = f"https://api.checkwx.com/metar/{icao}/decoded"
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                return data['results'][0].get('raw', '')
    except Exception as e:
        print(f"CheckWX error for {icao}: {e}")
    return None

def fetch_metar_noaa(icao):
    """Fallback to NOAA"""
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get('rawOb', '')
    except:
        pass
    return None

def fetch_metar(icao):
    api_key = os.environ.get("CHECKWX_API_KEY")
    if api_key:
        metar = fetch_metar_checkwx(icao, api_key)
        if metar:
            return metar
    # Fallback to NOAA
    return fetch_metar_noaa(icao)

def parse_metar_simple(metar_string):
    import re
    # Wind speed and direction
    wind_match = re.search(r'(\d{3})(\d{2})KT', metar_string)
    if wind_match:
        wind_dir = int(wind_match.group(1))
        wind_speed = int(wind_match.group(2))
    else:
        wind_dir = None
        wind_speed = 0
    # Visibility in meters to miles
    vis_match = re.search(r'(\d{4}) ', metar_string)
    if vis_match:
        visibility_miles = int(vis_match.group(1)) / 1609.34
    else:
        visibility_miles = 10
    # Thunderstorm
    has_ts = 'TS' in metar_string or 'TSRA' in metar_string
    alerts = []
    if wind_speed > CROSSWIND_LIMIT_KNOTS:
        alerts.append(f"CROSSWIND ALERT: {wind_speed} kts (limit {CROSSWIND_LIMIT_KNOTS})")
    if visibility_miles < VISIBILITY_LIMIT_MILES:
        alerts.append(f"LOW VISIBILITY: {visibility_miles:.1f} miles (limit {VISIBILITY_LIMIT_MILES})")
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        'alerts': alerts,
        'is_safe': len(alerts) == 0,
        'wind_dir': wind_dir,
        'wind_speed': wind_speed,
        'visibility_miles': round(visibility_miles, 1),
        'has_thunderstorm': has_ts,
        'raw_metar': metar_string[:120]
    }

def generate_report():
    lines = ["=== Runway Viz Report ===", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"]
    for icao in AIRFIELDS:
        metar = fetch_metar(icao)
        if metar:
            wx = parse_metar_simple(metar)
            status = "SAFE" if wx['is_safe'] else "ALERT"
            lines.append(f"\n{icao}: {status}")
            lines.extend(wx['alerts'])
            lines.append(f"   Wind: {wx['wind_speed']} kts {wx['wind_dir']}° | Vis: {wx['visibility_miles']} mi")
            if wx['has_thunderstorm']:
                lines.append("   ⛈️ Thunderstorm reported")
            lines.append(f"   Raw METAR: {wx['raw_metar']}...")
        else:
            lines.append(f"\n{icao}: FETCH FAILED - check ICAO or API")
    return "\n".join(lines)

if __name__ == "__main__":
    try:
        report = generate_report()
        print(report)
        with open("latest_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        print("\n[SUCCESS] Report saved")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)