# Climate Logger

Reads an AM2302/DHT22 sensor every five seconds, retrying failed readings every
two seconds, stores sensor and weather readings in SQLite, calculates a
non-overlapping one-minute average, and serves the latest average through Flask.

Local weather comes from Open-Meteo for `32.924637745862825,
-117.16058117149171`. A lightweight background thread fetches current outdoor
temperature, humidity, and conditions at startup and every 15 minutes. Each
successful weather observation is stored in the database. Each one-minute sensor
average uses the most recent weather observation. If a request fails, the last
successful observation is retained so indoor logging continues.

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

Initialize the database and register the local sensor before starting the
logger:

```bash
python3 db_actions.py init
python3 db_actions.py register-sensor \
	--name "Indoor AM2302" \
	--ipv4-address 192.168.1.42
```

The registration command prints the stored sensor as JSON, including its
generated ID. New sensors are registered with `low_battery` set to `false`.

```bash
python3 run.py
```

The web page is available at `http://<raspberry-pi-address>:5000/`. The latest
stored one-minute average for sensor ID `0` is available as JSON from
`/api/average`, together with the latest stored weather reading. The endpoint
returns data after sensor ID `0` has at least one stored average.

Each completed local one-minute average is stored in the database under sensor
ID `1`. That sensor must already be registered in the database.

Registered sensors can submit readings with `POST /api/sensor-readings`:

```bash
curl -X POST http://<raspberry-pi-address>:5000/api/sensor-readings \
	-H 'Content-Type: application/json' \
	-d '{"sensor_id": 1, "timestamp_utc": 1786200000, "temperature": 22.4, "humidity": 48.5, "num_readings": 12}'
```

`timestamp_utc` is a Unix timestamp in UTC seconds and `num_readings` is the
number of samples represented by the submitted average. A successful insert
returns the stored reading with HTTP `201`; unknown sensor IDs return HTTP `404`.

Operational events and errors are appended to `src/climate_logger.log` and still
printed to the console. Temperature and humidity readings are stored only in the
database. The latest average API includes indoor readings plus outdoor
temperature, humidity, condition, and observation time. Override the web
listener as needed:

```bash
python3 run.py --host 0.0.0.0 --port 8080
```

## Start on boot

From the project directory on the Raspberry Pi, register and start the systemd
service with the virtual environment's Python interpreter:

```bash
sudo env/bin/python setup.py
```

The installer writes `environment-logger.service`, enables it at boot, and
starts it immediately. Inspect the service or follow its output with:

```bash
systemctl status environment-logger.service
journalctl -u environment-logger.service -f
```