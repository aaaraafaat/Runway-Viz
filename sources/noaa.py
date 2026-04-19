# sources/noaa.py
import requests
import re
from datetime import datetime
from sources.base import WeatherFetcher
import config

class NOAAFetcher(WeatherFetcher):
    def fetch(self, icao):
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    raw_metar = data[0].get('rawOb', '')
                    if raw_metar:
                        parsed = self._parse_metar(raw_metar)
                        parsed['success'] = True
                        parsed['source'] = 'NOAA'
                        parsed['raw_metar'] = raw_metar
                        parsed['timestamp'] = datetime.now().isoformat()
                        return parsed
        except Exception as e:
            return {'success': False, 'source': 'NOAA', 'error': str(e)}
        return {'success': False, 'source': 'NOAA', 'error': 'No data'}

    def _parse_metar(self, metar):
        import re
        wind_match = re.search(r'(\d{3})(\d{2})KT', metar)
        wind_dir = int(wind_match.group(1)) if wind_match else None
        wind_speed = int(wind_match.group(2)) if wind_match else 0
        vis_match = re.search(r'(\d{4}) ', metar)
        vis_miles = int(vis_match.group(1)) / 1609.34 if vis_match else 10
        has_ts = 'TS' in metar or 'TSRA' in metar
        # Temperature and dewpoint: e.g., "28/25"
        temp_match = re.search(r'(\d{2})/(\d{2})', metar)
        temp = int(temp_match.group(1)) if temp_match else None
        dewpoint = int(temp_match.group(2)) if temp_match else None
        # QNH (altimeter setting): e.g., "Q1005" or "A2992"
        qnh_match = re.search(r'Q(\d{4})', metar)
        if qnh_match:
            qnh_hpa = int(qnh_match.group(1))
        else:
            qnh_hpa = None
        alerts = []
        if wind_speed > config.CROSSWIND_LIMIT_KNOTS:
            alerts.append(f"CROSSWIND ALERT: {wind_speed} kts (limit {config.CROSSWIND_LIMIT_KNOTS})")
        if vis_miles < config.VISIBILITY_LIMIT_MILES:
            alerts.append(f"LOW VISIBILITY: {vis_miles:.1f} miles (limit {config.VISIBILITY_LIMIT_MILES})")
        return {
            'wind_speed': wind_speed,
            'wind_dir': wind_dir,
            'visibility': round(vis_miles, 1),
            'has_thunderstorm': has_ts,
            'alerts': alerts,
            'temperature': temp,
            'dewpoint': dewpoint,
            'qnh_hpa': qnh_hpa
        }