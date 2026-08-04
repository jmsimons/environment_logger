"""Flask web application for the climate logger."""

from dataclasses import asdict

from flask import Flask, jsonify, render_template_string

from .main import SENSOR_GPIO, ClimateLogger


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <title>Climate Monitor</title>
    <style>
        :root { color-scheme: light dark; font-family: ui-monospace, monospace; }
        body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #18211d; color: #eef5ef; }
        main { width: min(38rem, calc(100% - 2rem)); border-top: 4px solid #e6b85c; padding: 2rem 0; }
        h1 { margin: 0 0 2rem; font: 600 1.1rem/1 sans-serif; letter-spacing: 0; }
        .readings { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
        .reading { border: 1px solid #54635b; padding: 1.25rem; }
        .value { display: block; font-size: clamp(2rem, 10vw, 4.5rem); line-height: 1; }
        .label, footer { color: #aebbb3; }
        .label { display: block; margin-top: .75rem; }
        footer { margin-top: 1.5rem; font-size: .8rem; line-height: 1.6; }
        @media (max-width: 32rem) { .readings { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<main>
    <h1>AM2302 · GPIO {{ gpio }} · ONE-MINUTE AVERAGE</h1>
    {% if average %}
    <section class="readings">
        <div class="reading"><span class="value">{{ "%.1f"|format(average.temperature_f) }}°</span><span class="label">Fahrenheit</span></div>
        <div class="reading"><span class="value">{{ "%.1f"|format(average.humidity_percent) }}%</span><span class="label">Relative humidity</span></div>
    </section>
    <footer>
        {{ average.temperature_c|round(1) }} °C · {{ average.sample_count }} samples<br>
        Minute ending {{ average.timestamp_utc }} UTC
    </footer>
    {% else %}
    <p>Collecting the first minute of samples...</p>
    {% endif %}
</main>
</body>
</html>
"""


def create_app(climate_logger: ClimateLogger) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template_string(
            PAGE_TEMPLATE,
            average=climate_logger.get_latest_average(),
            gpio=SENSOR_GPIO,
        )

    @app.get("/api/average")
    def average_api():
        average = climate_logger.get_latest_average()
        if average is None:
            return jsonify({"status": "collecting"}), 503
        return jsonify(asdict(average))

    return app


__all__ = ["ClimateLogger", "create_app"]
