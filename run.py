#!/usr/bin/env python3
"""Run the climate logger from the project root."""

import argparse
import signal
import threading

from src import (
    DEFAULT_SENSOR_ID,
    SAMPLE_INTERVAL_SECONDS,
    ClimateLogger,
    db,
    app,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Store AM2302 readings and serve climate data over HTTP."
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=5000, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    db.get_sensor_by_id(DEFAULT_SENSOR_ID)

    climate_logger = ClimateLogger()
    weather_updater = threading.Thread(
        target=climate_logger.run_weather,
        name="weather-updater",
        daemon=True,
    )
    sampler = threading.Thread(
        target=climate_logger.run_sensor,
        name="am2302-sampler",
        daemon=True,
    )
    weather_updater.start()
    sampler.start()

    def stop(_signal_number, _frame) -> None:
        climate_logger.stop()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        print("Starting climate logger web server...")
        app.run(
            host=args.host,
            port=args.port,
            debug=False,
            use_reloader=False,
        )
    finally:
        climate_logger.stop()
        sampler.join(timeout=SAMPLE_INTERVAL_SECONDS + 1.0)
        weather_updater.join(
            timeout=climate_logger.weather_client.timeout_seconds + 1.0
        )
        climate_logger.close()


if __name__ == "__main__":
    main()
