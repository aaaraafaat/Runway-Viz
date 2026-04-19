import requests
from datetime import datetime
import time
import sys
import os

# Force UTF-8 for Windows console (fixes UnicodeEncodeError)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# List of Bangladesh airfields (ICAO codes)
AIRFIELDS = ['VGZR', 'VGEG', 'VGSY', 'VGJR', 'VGBR', 'VGTJ']  # add any valid ICAO


# Aircraft limits (Cessna 152 example)
CROSSWIND_LIMIT_KNOTS = 12
VISIBILITY_LIMIT_MILES = 5


def fetch_metar_with_retry(icao, retries=2):
    # Try CheckWX first (more reliable for BD airports)
    api_key = os.environ.get("CHECKWX_API_KEY")
    if api_key:
        url = f"https://api.checkwx.com/metar/{icao}/decoded"
        headers = {"X-API-Key": api_key}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    return data['results'][0].get('raw', '')
        except:
            pass
    
    # Fallback to NOAA
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0].get('rawOb', '')
        except:
            time.sleep(2)
    return None

def parse_metar_simple(metar_string):
    """Manual METAR parser (avoids metar library bugs)"""
    import re
    
    # Extract wind: direction and speed in knots (e.g., 31005KT)
    wind_match = re.search(r'(\d{3})(\d{2})KT', metar_string)
    if wind_match:
        wind_speed_knots = int(wind_match.group(2))
    else:
        wind_speed_knots = 0
    
    # Extract visibility in statute miles (e.g., 6000 = 6000 meters, convert)
    vis_match = re.search(r'(\d{4}) ', metar_string)
    if vis_match:
        visibility_meters = int(vis_match.group(1))
        visibility_miles = visibility_meters / 1609.34
    else:
        visibility_miles = 10  # default good visibility
    
    crosswind = wind_speed_knots  # simplified: assume worst-case
    
    alerts = []
    if crosswind > CROSSWIND_LIMIT_KNOTS:
        alerts.append(f"CROSSWIND ALERT: {crosswind:.0f} knots (limit {CROSSWIND_LIMIT_KNOTS})")
    if visibility_miles < VISIBILITY_LIMIT_MILES:
        alerts.append(f"LOW VISIBILITY: {visibility_miles:.1f} miles (limit {VISIBILITY_LIMIT_MILES})")
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        'alerts': alerts,
        'is_safe': len(alerts) == 0,
        'crosswind_knots': crosswind,
        'visibility_miles': round(visibility_miles, 1)
    }

def generate_report():
    """Generate report for all airfields (no emojis, pure ASCII)"""
    report_lines = ["=== Runway Viz Report ==="]
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    
    for icao in AIRFIELDS:
        metar = fetch_metar_with_retry(icao)
        if metar:
            analysis = parse_metar_simple(metar)
            if analysis:
                status = "SAFE" if analysis['is_safe'] else "ALERT"
                report_lines.append(f"\n{icao}: {status}")
                if analysis['alerts']:
                    report_lines.extend(analysis['alerts'])
                report_lines.append(f"   Wind: {analysis['crosswind_knots']} kts | Vis: {analysis['visibility_miles']} mi")
                report_lines.append(f"   Raw METAR: {metar[:80]}...")
            else:
                report_lines.append(f"\n{icao}: PARSE ERROR - could not read METAR")
        else:
            report_lines.append(f"\n{icao}: FETCH FAILED - check network or API")
    
    return "\n".join(report_lines)

# ---------- THE MAIN BLOCK WITH TRY-EXCEPT (this is what you asked for) ----------
if __name__ == "__main__":
    try:
        report = generate_report()
        print(report)
        with open("latest_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        print("\n[SUCCESS] Report saved to latest_report.txt")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)