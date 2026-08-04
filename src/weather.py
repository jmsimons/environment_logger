"""Fetch current local weather conditions from Open-Meteo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


WEATHER_LATITUDE = 32.924637745862825
WEATHER_LONGITUDE = -117.16058117149171
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass(frozen=True)
class WeatherReading:
    timestamp_utc: str
    temperature_c: float
    temperature_f: float
    humidity_percent: float
    weather_code: int
    description: str


class WeatherClient:
    """Retrieve current modelled conditions for the configured location."""

    def __init__(
        self,
        latitude: float = WEATHER_LATITUDE,
        longitude: float = WEATHER_LONGITUDE,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> WeatherReading:
        query = urlencode(
            {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "timezone": "GMT",
            }
        )
        request = Request(
            f"{OPEN_METEO_URL}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "environment-logger/1.0",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        return self._parse_response(payload)

    @staticmethod
    def _parse_response(payload: dict[str, Any]) -> WeatherReading:
        current = payload["current"]
        temperature_c = float(current["temperature_2m"])
        weather_code = int(current["weather_code"])
        timestamp = datetime.fromisoformat(str(current["time"]))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        return WeatherReading(
            timestamp_utc=timestamp.isoformat(timespec="seconds"),
            temperature_c=temperature_c,
            temperature_f=(temperature_c * 9.0 / 5.0) + 32.0,
            humidity_percent=float(current["relative_humidity_2m"]),
            weather_code=weather_code,
            description=WEATHER_DESCRIPTIONS.get(weather_code, "Unknown conditions"),
        )
