# sources/baf_ocr.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pytesseract
from PIL import Image
from io import BytesIO
from datetime import datetime
from sources.base import WeatherFetcher
import config

class BAFOCRfetcher(WeatherFetcher):
    def fetch(self, icao):
        station_name = config.ICAO_TO_BAF_STATION.get(icao)
        if not station_name:
            return {'success': False, 'source': 'BAF', 'error': f'No BAF station mapped for {icao}'}
        
        main_url = "https://met.baf.mil.bd/weather"
        try:
            resp = requests.get(main_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            img_tag = soup.find('img', src=re.compile(r'/uploads/images/sliders/'))
            if not img_tag:
                return {'success': False, 'source': 'BAF', 'error': 'No slider image found'}
            img_url = urljoin(main_url, img_tag['src'])
            print(f"[BAF] Found image: {img_url}")
        except Exception as e:
            return {'success': False, 'source': 'BAF', 'error': f'Page fetch failed: {e}'}
        
        try:
            headers = {"Referer": main_url}
            img_resp = requests.get(img_url, headers=headers, timeout=15)
            img_resp.raise_for_status()
            img = Image.open(BytesIO(img_resp.content))
            img = img.convert('L')
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            text = pytesseract.image_to_string(img, config='--psm 6')
            print(f"[BAF] OCR extracted {len(text)} characters")
        except Exception as e:
            return {'success': False, 'source': 'BAF', 'error': f'OCR failed: {e}'}
        
        rows = text.split('\n')
        for row in rows:
            if station_name in row:
                wind_match = re.search(r'(\d{3})/(\d{2})', row)
                wind_dir = int(wind_match.group(1)) if wind_match else None
                wind_speed = int(wind_match.group(2)) if wind_match else 0
                vis_match = re.search(r'(\d{4})\s*M', row)
                vis_miles = int(vis_match.group(1)) / 1609.34 if vis_match else 10
                has_ts = 'TS' in row or 'THUNDER' in row
                alerts = []
                if wind_speed > config.CROSSWIND_LIMIT_KNOTS:
                    alerts.append(f"CROSSWIND ALERT: {wind_speed} kts (limit {config.CROSSWIND_LIMIT_KNOTS})")
                if vis_miles < config.VISIBILITY_LIMIT_MILES:
                    alerts.append(f"LOW VISIBILITY: {vis_miles:.1f} miles (limit {config.VISIBILITY_LIMIT_MILES})")
                return {
                    'success': True,
                    'source': 'BAF',
                    'timestamp': datetime.now().isoformat(),
                    'wind_speed': wind_speed,
                    'wind_dir': wind_dir,
                    'visibility': round(vis_miles, 1),
                    'has_thunderstorm': has_ts,
                    'alerts': alerts,
                    'raw_metar': f"BAF OCR: {row[:100]}"
                }
        return {'success': False, 'source': 'BAF', 'error': f'Station {station_name} not found in OCR output'}