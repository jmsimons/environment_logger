#!/usr/bin/env python3
"""Collect AM2302 climate readings and serve the latest average.

Raspberry Pi wiring (BCM numbering):
    AM2302 VCC  -> 3.3 V (physical pin 1)
    AM2302 DATA -> GPIO4 (physical pin 7)
    AM2302 GND  -> Ground (physical pin 6)

Install dependencies with:
    python3 -m pip install adafruit-circuitpython-dht flask

The libgpiod system package may also be required by Blinka on Raspberry Pi OS.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from src.database import db
from .sensor import SensorReader
from .weather import WeatherClient, WeatherReading


SAMPLE_INTERVAL_SECONDS = 5.0
RETRY_INTERVAL_SECONDS = 2.0
AVERAGE_INTERVAL_SECONDS = 60.0
WEATHER_INTERVAL_SECONDS = 15.0 * 60.0
DEFAULT_SENSOR_ID = 1


@dataclass(frozen=True)
class ClimateAverage:
    timestamp_utc: str
    temperature_c: float
    temperature_f: float
    humidity_percent: float
    sample_count: int
    outdoor_timestamp_utc: str | None
    outdoor_temperature_c: float | None
    outdoor_temperature_f: float | None
    outdoor_humidity_percent: float | None
    outdoor_weather_code: int | None
    outdoor_description: str | None


class ClimateLogger:
    """Sample an AM2302 and calculate one average for each completed minute."""

    def __init__(
        self,
        weather_client: WeatherClient | None = None,
        sensor_reader: SensorReader | None = None,
    ) -> None:
        self.weather_client = weather_client or WeatherClient()
        self.latest_weather: WeatherReading | None = None
        self.sensor_reader = sensor_reader or SensorReader(DEFAULT_SENSOR_ID)
        self.latest_average: ClimateAverage | None = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def run_sensor(self) -> None:
        temperatures: list[float] = []
        humidities: list[float] = []
        interval_end = time.monotonic() + AVERAGE_INTERVAL_SECONDS

        while not self.stop_event.is_set():
            sample_succeeded = False
            try:
                reading = self.sensor_reader.fetch()
                if reading is not None:
                    temperatures.append(reading.temperature_c)
                    humidities.append(reading.humidity_percent)
                    sample_succeeded = True
            except RuntimeError as error:
                logging.debug("Transient AM2302 read failure: %s", error)
            except Exception:
                logging.exception("Unexpected AM2302 read failure")

            now = time.monotonic()
            if now >= interval_end:
                if temperatures and humidities:
                    with self.lock:
                        weather = self.latest_weather
                    average = self._build_average(
                        temperatures,
                        humidities,
                        weather,
                    )
                    self._append_sensor_average(average)
                    with self.lock:
                        self.latest_average = average
                    logging.info(
                        "Minute average updated from %d samples",
                        average.sample_count,
                    )
                else:
                    logging.warning("No valid AM2302 samples collected this minute")

                temperatures.clear()
                humidities.clear()
                interval_end = now + AVERAGE_INTERVAL_SECONDS

            wait_seconds = (
                SAMPLE_INTERVAL_SECONDS
                if sample_succeeded
                else RETRY_INTERVAL_SECONDS
            )
            self.stop_event.wait(wait_seconds)

    def run_weather(self) -> None:
        while not self.stop_event.is_set():
            try:
                weather = self.weather_client.fetch()
                with self.lock:
                    self.latest_weather = weather
                self._append_weather_reading(weather)
                logging.info(
                    "Local weather updated: %s", weather.description
                )
            except Exception as error:
                logging.warning("Unable to fetch local weather: %s", error)

            self.stop_event.wait(WEATHER_INTERVAL_SECONDS)

    def get_latest_average(self) -> ClimateAverage | None:
        with self.lock:
            return self.latest_average

    def stop(self) -> None:
        self.stop_event.set()

    def close(self) -> None:
        self.stop()
        self.sensor_reader.close()

    @staticmethod
    def _build_average(
        temperatures: list[float],
        humidities: list[float],
        weather: WeatherReading | None = None,
    ) -> ClimateAverage:
        temperature_c = sum(temperatures) / len(temperatures)
        humidity_percent = sum(humidities) / len(humidities)
        return ClimateAverage(
            timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            temperature_c=temperature_c,
            temperature_f=(temperature_c * 9.0 / 5.0) + 32.0,
            humidity_percent=humidity_percent,
            sample_count=len(temperatures),
            outdoor_timestamp_utc=(weather.timestamp_utc if weather else None),
            outdoor_temperature_c=(weather.temperature_c if weather else None),
            outdoor_temperature_f=(weather.temperature_f if weather else None),
            outdoor_humidity_percent=(weather.humidity_percent if weather else None),
            outdoor_weather_code=(weather.weather_code if weather else None),
            outdoor_description=(weather.description if weather else None),
        )

    def _append_sensor_average(self, average: ClimateAverage) -> None:
        try:
            db.create_sensor_reading(
                sensor_id=self.sensor_reader.sensor_id,
                timestamp_utc=int(datetime.fromisoformat(average.timestamp_utc).timestamp()),
                temperature_c=average.temperature_c,
                humidity_percent=average.humidity_percent,
                num_readings=average.sample_count,
            )
        except Exception:
            logging.exception("Unable to persist sensor average")

    @staticmethod
    def _append_weather_reading(reading: WeatherReading) -> None:
        try:
            timestamp_utc = int(datetime.fromisoformat(reading.timestamp_utc).timestamp())
            db.create_weather_reading(
                timestamp_utc=timestamp_utc,
                temperature_c=reading.temperature_c,
                temperature_f=reading.temperature_f,
                humidity_percent=reading.humidity_percent,
                description=reading.description,
            )
        except Exception:
            logging.exception("Unable to persist weather reading")
