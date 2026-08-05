"""Flask web application for the climate logger."""

from dataclasses import asdict

from flask import jsonify, render_template

from src.main import ClimateLogger
from . import app


def _get_climate_logger() -> ClimateLogger:
    return app.config["CLIMATE_LOGGER"]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/average")
def average_api():
    average = _get_climate_logger().get_latest_average()
    if average is None:
        return jsonify({"status": "collecting"}), 503
    return jsonify(asdict(average))
