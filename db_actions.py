#!/usr/bin/env python3
"""Initialize the climate database and register sensors."""

import argparse
import json
import sys

from sqlalchemy.exc import SQLAlchemyError

from src.database import db, db_filename, initialize_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "init",
        help="Create any missing database tables.",
    )

    register_parser = subparsers.add_parser(
        "register-sensor",
        help="Register a sensor in the database.",
    )
    register_parser.add_argument("--name", required=True, help="Sensor name.")
    register_parser.add_argument(
        "--ipv4-address",
        required=True,
        help="Sensor IPv4 address.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.command == "init":
            initialize_database()
            print(f"Initialized database: {db_filename}")
            return 0

        sensor = db.create_sensor(
            name=args.name,
            ipv4_address=args.ipv4_address,
        )
        print(json.dumps(sensor, sort_keys=True))
        return 0
    except SQLAlchemyError as error:
        print(f"Database error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
