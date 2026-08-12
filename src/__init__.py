"""Climate logger package."""

import logging
from pathlib import Path


# Setup logging before any app components are imported/init'd.
RUNTIME_LOG_PATH = Path(__file__).with_name("climate_logger.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(RUNTIME_LOG_PATH, encoding="utf-8"),
    ],
)


# Import app resources necessary for initialization.
from .main import (
    ClimateLogger,
    DEFAULT_SENSOR_ID,
    SAMPLE_INTERVAL_SECONDS,
)
from .database import db
from .webapp import app

__all__ = [
    "ClimateLogger",
    "DEFAULT_SENSOR_ID",
    "RUNTIME_LOG_PATH",
    "SAMPLE_INTERVAL_SECONDS",
    "db",
    "app",
]
