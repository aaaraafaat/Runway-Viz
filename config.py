# config.py
import os

# List of ICAO codes to monitor
AIRFIELDS = ['VGHS', 'VGEG', 'VGSY', 'VGJR']

# Weather limits
CROSSWIND_LIMIT_KNOTS = 12
VISIBILITY_LIMIT_MILES = 5

# Mapping from ICAO to BAF station name (for OCR)
ICAO_TO_BAF_STATION = {
    'VGHS': 'BAF AKR',   # Dhaka
    'VGEG': 'BAF ZHR',   # Chittagong (user said BAF ZHR = Chittagong)
    'VGSY': 'BAF ???',   # Unknown, will try to match by ICAO later
    'VGJR': 'BAF MTR',   # Jessore
    'VGTJ': 'BAF BSR',   # Tejgaon (optional)
}

# CheckWX API key from GitHub secrets
CHECKWX_API_KEY = os.environ.get("CHECKWX_API_KEY", "")