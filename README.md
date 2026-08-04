# Climate Logger

Reads an AM2302/DHT22 sensor every five seconds, retrying failed readings every
two seconds, records a non-overlapping one-minute temperature and humidity
average in CSV, and serves the latest average through Flask.

## Wiring

The application uses BCM GPIO numbering and selects GPIO4 for sensor data.

| AM2302 | Raspberry Pi |
| --- | --- |
| VCC | 3.3 V, physical pin 1 |
| DATA | GPIO4, physical pin 7 |
| GND | Ground, physical pin 6 |

Use a 4.7–10 kΩ pull-up resistor between VCC and DATA when the sensor module
does not include one.

## Installation

On Raspberry Pi OS:

```bash
sudo apt update
sudo apt install python3-venv libgpiod2
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 run.py
```

The web page is available at `http://<raspberry-pi-address>:5000/`. The current
average is also available as JSON from `/api/average`. The first response is
available after one minute of valid samples.

By default, averages are appended to `src/climate_log.csv`. Override the web
listener or log path as needed:

```bash
python3 run.py --host 0.0.0.0 --port 8080 --log-file /var/lib/climate_logger/climate.csv
```