"""Read temperature and humidity from the AM2302 sensor."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


SENSOR_GPIO = 4


@dataclass(frozen=True)
class SensorReading:
    temperature_c: float
    humidity_percent: float


class SensorReader:
    """Own the AM2302 hardware and retrieve paired sensor readings."""

    def __init__(self, sensor_id: int) -> None:
        self.sensor_id = sensor_id
        try:
            adafruit_dht = import_module("adafruit_dht")
            board = import_module("board")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "AM2302 support requires the adafruit-circuitpython-dht package "
                "and its Raspberry Pi GPIO dependencies"
            ) from error

        self.sensor: Any = adafruit_dht.DHT22(board.D4, use_pulseio=False)

    def fetch(self) -> SensorReading | None:
        temperature = self.sensor.temperature
        humidity = self.sensor.humidity
        if temperature is None or humidity is None:
            return None
        return SensorReading(
            temperature_c=float(temperature),
            humidity_percent=float(humidity),
        )

    def close(self) -> None:
        self.sensor.exit()
