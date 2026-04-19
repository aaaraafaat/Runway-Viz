# sources/base.py
from abc import ABC, abstractmethod

class WeatherFetcher(ABC):
    @abstractmethod
    def fetch(self, icao):
        """Return dict with keys: success, source, timestamp, wind_speed, wind_dir, visibility, has_thunderstorm, alerts, raw_metar, error"""
        pass