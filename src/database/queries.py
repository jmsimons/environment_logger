"""Database queries grouped by reading table."""

from sqlalchemy import select

from .base_queries import BaseTableQueries
from .models import Sensor, SensorReading, WeatherReading


class SensorQueries(BaseTableQueries):
    """Registered sensor queries for the database interface."""

    model_class = Sensor

    def create_sensor(
        self,
        name: str,
        ipv4_address: str,
        current_session=None,
    ) -> dict:
        """Register a sensor and return its database representation."""

        with self.session(current_session) as session:
            sensor = Sensor(
                name=name,
                ipv4_address=ipv4_address,
            )
            session.add(sensor)
            session.flush()
            return self._sensor_dict(sensor)

    def get_sensor_by_id(self, sensor_id: int, current_session=None) -> dict:
        """Return the registered sensor matching the given ID."""

        with self.session(current_session) as session:
            sensor = session.get(Sensor, sensor_id)
            if sensor is None:
                raise ValueError(f"Sensor with id '{sensor_id}' not found.")
            return self._sensor_dict(sensor)

    def get_all_sensors(self, current_session=None) -> list[dict]:
        """Return all registered sensors in creation order."""

        statement = select(Sensor).order_by(Sensor.id)
        with self.session(current_session) as session:
            sensors = session.scalars(statement).all()
            return [self._sensor_dict(sensor) for sensor in sensors]

    @staticmethod
    def _sensor_dict(sensor: Sensor) -> dict:
        return {
            "id": sensor.id,
            "name": sensor.name,
            "ipv4_address": sensor.ipv4_address,
            "low_battery": sensor.low_battery,
        }


class SensorReadingQueries(BaseTableQueries):
    """Sensor reading queries for the database interface."""

    model_class = SensorReading

    def create_sensor_reading(
        self,
        sensor_id: int,
        timestamp_utc: int,
        temperature_c: float,
        humidity_percent: float,
        num_readings: int,
        current_session=None,
    ) -> dict:
        """Persist a sensor reading and return its database representation."""

        with self.session(current_session) as session:
            reading = SensorReading(
                sensor_id=sensor_id,
                timestamp_utc=timestamp_utc,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                num_readings=num_readings,
            )
            session.add(reading)
            session.flush()
            return self._sensor_reading_dict(reading)

    def get_latest_sensor_reading(self, sensor_id: int, current_session=None) -> dict | None:
        """Return the newest reading for a sensor, if one exists."""
        statement = (
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id)
            .order_by(SensorReading.timestamp_utc.desc(), SensorReading.id.desc())
            .limit(1)
        )
        with self.session(current_session) as session:
            reading = session.scalars(statement).first()
            return self._sensor_reading_dict(reading) if reading else None

    def get_all_sensor_readings(self, current_session=None) -> list[dict]:
        """Return all sensor readings from oldest to newest."""

        statement = select(SensorReading).order_by(
            SensorReading.timestamp_utc.asc(),
            SensorReading.id.asc(),
        )
        with self.session(current_session) as session:
            readings = session.scalars(statement).all()
            return [self._sensor_reading_dict(reading) for reading in readings]

    @staticmethod
    def _sensor_reading_dict(reading: SensorReading) -> dict:
        return {
            "id": reading.id,
            "sensor_id": reading.sensor_id,
            "timestamp_utc": reading.timestamp_utc,
            "temperature_c": reading.temperature_c,
            "humidity_percent": reading.humidity_percent,
            "num_readings": reading.num_readings,
        }


class WeatherReadingQueries(BaseTableQueries):
    """Weather reading queries for the database interface."""

    model_class = WeatherReading

    def create_weather_reading(
        self,
        timestamp_utc: int,
        temperature_c: float,
        temperature_f: float,
        humidity_percent: float,
        description: str,
        current_session=None,
    ) -> dict:
        """Persist a weather reading and return its database representation."""
        with self.session(current_session) as session:
            reading = WeatherReading(
                timestamp_utc=timestamp_utc,
                temperature_c=temperature_c,
                temperature_f=temperature_f,
                humidity_percent=humidity_percent,
                description=description,
            )
            session.add(reading)
            session.flush()
            return self._weather_reading_dict(reading)

    def get_latest_weather_reading(self, current_session=None) -> dict | None:
        """Return the newest weather reading, if one exists."""
        statement = (
            select(WeatherReading)
            .order_by(WeatherReading.timestamp_utc.desc(), WeatherReading.id.desc())
            .limit(1)
        )
        with self.session(current_session) as session:
            reading = session.scalars(statement).first()
            return self._weather_reading_dict(reading) if reading else None

    @staticmethod
    def _weather_reading_dict(reading: WeatherReading) -> dict:
        return {
            "id": reading.id,
            "timestamp_utc": reading.timestamp_utc,
            "temperature_c": reading.temperature_c,
            "temperature_f": reading.temperature_f,
            "humidity_percent": reading.humidity_percent,
            "description": reading.description,
        }
