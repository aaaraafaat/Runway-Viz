import os

AIRFIELDS = ['VGHS', 'VGEG']   # Dhaka and Chittagong only

CROSSWIND_LIMIT_KNOTS = 12
VISIBILITY_LIMIT_MILES = 5

# BAF mapping is not used (but kept to avoid errors)
ICAO_TO_BAF_STATION = {
    'VGHS': 'BAF AKR',
    'VGEG': 'BAF ZHR',
}

CHECKWX_API_KEY = os.environ.get("CHECKWX_API_KEY", "")