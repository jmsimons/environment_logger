"""Climate logger package."""

import logging
from pathlib import Path

from .main import ClimateLogger


RUNTIME_LOG_PATH = Path(__file__).with_name("climate_logger.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(RUNTIME_LOG_PATH, encoding="utf-8"),
    ],
)


__all__ = ["ClimateLogger"]
