"""Flask routes for the climate logger."""

from datetime import datetime, timezone
from math import isfinite

from flask import Response, jsonify, render_template, request

from src import RUNTIME_LOG_PATH
from . import app, db


AVERAGE_SENSOR_ID = 0


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/sensor-readings")
def sensor_readings():
    readings = []
    for reading in db.get_all_sensor_readings():
        timestamp = datetime.fromtimestamp(reading["timestamp_utc"], timezone.utc)
        readings.append(
            {
                **reading,
                "timestamp_iso": timestamp.isoformat(),
                "timestamp_display": timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
        )
    return render_template("sensor_readings.html", readings=readings)


@app.get("/runtime-log")
def runtime_log():
    try:
        log_text = RUNTIME_LOG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Response("Runtime log is unavailable.\n", status=404, mimetype="text/plain")
    return Response(log_text, mimetype="text/plain")


@app.get("/api/average")
def average_api():
    average = db.get_latest_sensor_reading(AVERAGE_SENSOR_ID)
    if average is None:
        return jsonify({"status": "collecting"}), 503

    weather = db.get_latest_weather_reading()
    temperature_c = average["temperature_c"]
    return jsonify(
        {
            "timestamp_utc": _timestamp_iso(average["timestamp_utc"]),
            "temperature_c": temperature_c,
            "temperature_f": (temperature_c * 9.0 / 5.0) + 32.0,
            "humidity_percent": average["humidity_percent"],
            "num_readings": average["num_readings"],
            "outdoor_timestamp_utc": (
                _timestamp_iso(weather["timestamp_utc"]) if weather else None
            ),
            "outdoor_temperature_c": (
                weather["temperature_c"] if weather else None
            ),
            "outdoor_temperature_f": (
                weather["temperature_f"] if weather else None
            ),
            "outdoor_humidity_percent": (
                weather["humidity_percent"] if weather else None
            ),
            "outdoor_weather_code": None,
            "outdoor_description": weather["description"] if weather else None,
        }
    )


@app.post("/api/sensor-readings")
def create_sensor_reading_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    required_fields = {
        "sensor_id",
        "timestamp_utc",
        "temperature",
        "humidity",
        "num_readings",
    }
    missing_fields = sorted(required_fields - payload.keys())
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    sensor_id = payload["sensor_id"]
    timestamp_utc = payload["timestamp_utc"]
    temperature = payload["temperature"]
    humidity = payload["humidity"]
    num_readings = payload["num_readings"]

    if not isinstance(sensor_id, int) or isinstance(sensor_id, bool):
        return jsonify({"error": "sensor_id must be an integer."}), 400
    if not isinstance(timestamp_utc, int) or isinstance(timestamp_utc, bool):
        return jsonify({"error": "timestamp_utc must be an integer."}), 400
    if not _is_finite_number(temperature):
        return jsonify({"error": "temperature must be a finite number."}), 400
    if not _is_finite_number(humidity):
        return jsonify({"error": "humidity must be a finite number."}), 400
    if (
        not isinstance(num_readings, int)
        or isinstance(num_readings, bool)
        or num_readings < 1
    ):
        return jsonify({"error": "num_readings must be a positive integer."}), 400

    try:
        db.get_sensor_by_id(sensor_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 404

    reading = db.create_sensor_reading(
        sensor_id=sensor_id,
        timestamp_utc=timestamp_utc,
        temperature_c=float(temperature),
        humidity_percent=float(humidity),
        num_readings=num_readings,
    )
    return jsonify(reading), 201


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    )


def _timestamp_iso(timestamp_utc: int) -> str:
    return datetime.fromtimestamp(timestamp_utc, timezone.utc).isoformat()
