#!/usr/bin/env python3
"""Log one-minute AM2302 climate averages and serve the latest reading.

Raspberry Pi wiring (BCM numbering):
    AM2302 VCC  -> 3.3 V (physical pin 1)
    AM2302 DATA -> GPIO4 (physical pin 7)
    AM2302 GND  -> Ground (physical pin 6)

Install dependencies with:
    python3 -m pip install adafruit-circuitpython-dht flask

The libgpiod system package may also be required by Blinka on Raspberry Pi OS.
"""

from __future__ import annotations

import csv
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .sensor import SensorReader
from .weather import WeatherClient, WeatherReading


SAMPLE_INTERVAL_SECONDS = 5.0
RETRY_INTERVAL_SECONDS = 2.0
AVERAGE_INTERVAL_SECONDS = 60.0
WEATHER_INTERVAL_SECONDS = 15.0 * 60.0
DEFAULT_LOG_PATH = Path(__file__).with_name("climate_log.csv")


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
    """Sample an AM2302 and persist one average for each completed minute."""

    def __init__(
        self,
        log_path: Path,
        weather_client: WeatherClient | None = None,
        sensor_reader: SensorReader | None = None,
    ) -> None:
        self.log_path = log_path
        self.weather_client = weather_client or WeatherClient()
        self.latest_weather: WeatherReading | None = None
        self.sensor_reader = sensor_reader or SensorReader()
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
                    self._append_average(average)
                    with self.lock:
                        self.latest_average = average
                    logging.info(
                        "Minute average: %.1f F, %.1f%% RH (%d samples)",
                        average.temperature_f,
                        average.humidity_percent,
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
                logging.info(
                    "Local weather: %.1f F, %.1f%% RH, %s",
                    weather.temperature_f,
                    weather.humidity_percent,
                    weather.description,
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

    def _append_average(self, average: ClimateAverage) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.log_path.exists() or self.log_path.stat().st_size == 0
        fieldnames = list(asdict(average))
        if not write_header:
            self._upgrade_log_schema(fieldnames)
        with self.log_path.open("a", newline="", encoding="utf-8") as log_file:
            writer = csv.DictWriter(log_file, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(asdict(average))

    def _upgrade_log_schema(self, fieldnames: list[str]) -> None:
        with self.log_path.open(newline="", encoding="utf-8") as log_file:
            reader = csv.DictReader(log_file)
            if reader.fieldnames == fieldnames:
                return
            rows = list(reader)

        temporary_path = self.log_path.with_suffix(f"{self.log_path.suffix}.tmp")
        with temporary_path.open("w", newline="", encoding="utf-8") as log_file:
            writer = csv.DictWriter(log_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in fieldnames})
        temporary_path.replace(self.log_path)
