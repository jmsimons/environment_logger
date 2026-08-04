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
from importlib import import_module
from pathlib import Path
from typing import Any


SENSOR_GPIO = 4
SAMPLE_INTERVAL_SECONDS = 5.0
RETRY_INTERVAL_SECONDS = 2.0
AVERAGE_INTERVAL_SECONDS = 60.0
DEFAULT_LOG_PATH = Path(__file__).with_name("climate_log.csv")


@dataclass(frozen=True)
class ClimateAverage:
    timestamp_utc: str
    temperature_c: float
    temperature_f: float
    humidity_percent: float
    sample_count: int


class ClimateLogger:
    """Sample an AM2302 and persist one average for each completed minute."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        try:
            adafruit_dht = import_module("adafruit_dht")
            board = import_module("board")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "AM2302 support requires the adafruit-circuitpython-dht package "
                "and its Raspberry Pi GPIO dependencies"
            ) from error

        self.sensor: Any = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        self.latest_average: ClimateAverage | None = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def run(self) -> None:
        temperatures: list[float] = []
        humidities: list[float] = []
        interval_end = time.monotonic() + AVERAGE_INTERVAL_SECONDS

        while not self.stop_event.is_set():
            sample_succeeded = False
            try:
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                if temperature is not None and humidity is not None:
                    temperatures.append(float(temperature))
                    humidities.append(float(humidity))
                    sample_succeeded = True
            except RuntimeError as error:
                logging.debug("Transient AM2302 read failure: %s", error)
            except Exception:
                logging.exception("Unexpected AM2302 read failure")

            now = time.monotonic()
            if now >= interval_end:
                if temperatures and humidities:
                    average = self._build_average(temperatures, humidities)
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

    def get_latest_average(self) -> ClimateAverage | None:
        with self.lock:
            return self.latest_average

    def stop(self) -> None:
        self.stop_event.set()

    def close(self) -> None:
        self.stop()
        self.sensor.exit()

    @staticmethod
    def _build_average(
        temperatures: list[float], humidities: list[float]
    ) -> ClimateAverage:
        temperature_c = sum(temperatures) / len(temperatures)
        humidity_percent = sum(humidities) / len(humidities)
        return ClimateAverage(
            timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            temperature_c=temperature_c,
            temperature_f=(temperature_c * 9.0 / 5.0) + 32.0,
            humidity_percent=humidity_percent,
            sample_count=len(temperatures),
        )

    def _append_average(self, average: ClimateAverage) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.log_path.exists() or self.log_path.stat().st_size == 0
        with self.log_path.open("a", newline="", encoding="utf-8") as log_file:
            writer = csv.DictWriter(log_file, fieldnames=asdict(average).keys())
            if write_header:
                writer.writeheader()
            writer.writerow(asdict(average))
