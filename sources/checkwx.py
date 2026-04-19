# sources/checkwx.py
import requests
import re
from datetime import datetime
from .base import WeatherFetcher
import config

class CheckWXFetcher(WeatherFetcher):
    def fetch(self, icao):
        if not config.CHECKWX_API_KEY:
            return {'success': False, 'source': 'CheckWX', 'error': 'No API key'}
        url = f"https://api.checkwx.com/metar/{icao}/decoded"
        headers = {"X-API-Key": config.CHECKWX_API_KEY}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and data.get('results', 0) > 0:
                    raw = data['data'][0].get('raw_text', '')
                    if raw:
                        parsed = self._parse_metar(raw)
                        parsed['success'] = True
                        parsed['source'] = 'CheckWX'
                        parsed['raw_metar'] = raw
                        parsed['timestamp'] = datetime.now().isoformat()
                        return parsed
        except Exception as e:
            return {'success': False, 'source': 'CheckWX', 'error': str(e)}
        return {'success': False, 'source': 'CheckWX', 'error': 'No data'}

    def _parse_metar(self, metar):
        wind_match = re.search(r'(\d{3})(\d{2})KT', metar)
        wind_dir = int(wind_match.group(1)) if wind_match else None
        wind_speed = int(wind_match.group(2)) if wind_match else 0
        vis_match = re.search(r'(\d{4}) ', metar)
        if vis_match:
            vis_miles = int(vis_match.group(1)) / 1609.34
        else:
            vis_miles = 10
        has_ts = 'TS' in metar or 'TSRA' in metar
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
            'alerts': alerts
        }