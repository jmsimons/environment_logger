
#!/usr/bin/env python3
"""Run the climate logger from the project root."""

import argparse
import logging
import signal
import threading
from pathlib import Path

from src import ClimateLogger, create_app
from src.main import DEFAULT_LOG_PATH, SAMPLE_INTERVAL_SECONDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Log AM2302 one-minute averages and serve them over HTTP."
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument("--log-file", default=DEFAULT_LOG_PATH, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    climate_logger = ClimateLogger(args.log_file)
    sampler = threading.Thread(
        target=climate_logger.run,
        name="am2302-sampler",
        daemon=True,
    )
    sampler.start()

    def stop(_signal_number, _frame) -> None:
        climate_logger.stop()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        create_app(climate_logger).run(
            host=args.host,
            port=args.port,
            debug=False,
            use_reloader=False,
        )
    finally:
        climate_logger.stop()
        sampler.join(timeout=SAMPLE_INTERVAL_SECONDS + 1.0)
        climate_logger.close()


if __name__ == "__main__":
    main()
