# Runwayviz.py
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sources.noaa import NOAAFetcher
from sources.baf_ocr import BAFOCRfetcher
from sources.checkwx import CheckWXFetcher
import config

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_report():
    lines = ["=== Runway Viz Report ===", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"]
    
    fetchers = [NOAAFetcher(), CheckWXFetcher()]
    
    for icao in config.AIRFIELDS:
        weather = None
        for fetcher in fetchers:
            result = fetcher.fetch(icao)
            if result.get('success'):
                weather = result
                break
            else:
                print(f"[{fetcher.__class__.__name__}] Failed for {icao}: {result.get('error')}")
        
        if not weather:
            lines.append(f"\n{icao}: FETCH FAILED - all sources unavailable")
            continue
        
        status = "SAFE" if not weather['alerts'] else "ALERT"
        lines.append(f"\n{icao}: {status} [Source: {weather['source']}, Time: {weather.get('timestamp', 'unknown')}]")
        lines.extend(weather['alerts'])
        wind_str = f"{weather['wind_speed']} kts"
        if weather.get('wind_dir'):
            wind_str += f" {weather['wind_dir']}°"
        lines.append(f"   Wind: {wind_str} | Vis: {weather['visibility']} mi")
        if weather.get('has_thunderstorm'):
            lines.append("   ⛈️ Thunderstorm reported")
        if weather.get('raw_metar'):
            lines.append(f"   Raw: {weather['raw_metar'][:100]}...")
        if weather.get('temperature') is not None:
            lines.append(f"   Temp: {weather['temperature']}°C / Dew: {weather.get('dewpoint', '?')}°C")
        if weather.get('qnh_hpa'):
            lines.append(f"   QNH: {weather['qnh_hpa']} hPa")
    return "\n".join(lines)

if __name__ == "__main__":
    try:
        report = generate_report()
        print(report)
        with open("latest_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        print("\n[SUCCESS] Report saved with source attribution")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)