"""SQLAlchemy table model definitions."""

from sqlalchemy import Float, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Sensor(Base):
    """Represents a sensor."""
    __tablename__ = "sensor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    ipv4_address: Mapped[str] = mapped_column(String(16), nullable=False)
    low_battery: Mapped[bool] = mapped_column(Boolean, default=False)


class SensorReading(Base):
    """Represents sensor readings."""
    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_utc: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False)
    num_readings: Mapped[int] = mapped_column(Integer, nullable=False)


class WeatherReading(Base):
    """Represents weather readings."""
    __tablename__ = "weather_reading"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp_utc: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_f: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
