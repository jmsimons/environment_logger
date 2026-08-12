const POLL_INTERVAL_MS = 10_000;

const page = document.querySelector("[data-average-url]");
const status = document.querySelector("#status");
const sensor = document.querySelector("#sensor");
const sensorDetails = document.querySelector("#sensor-details");
const temperatureF = document.querySelector("#temperature-f");
const humidityPercent = document.querySelector("#humidity-percent");
const temperatureC = document.querySelector("#temperature-c");
const sampleCount = document.querySelector("#sample-count");
const timestampLocal = document.querySelector("#timestamp-local");
const weatherStatus = document.querySelector("#weather-status");
const weatherDetails = document.querySelector("#weather-details");
const outdoorTemperatureF = document.querySelector("#outdoor-temperature-f");
const outdoorHumidityPercent = document.querySelector("#outdoor-humidity-percent");
const outdoorTemperatureC = document.querySelector("#outdoor-temperature-c");
const outdoorTimestampLocal = document.querySelector("#outdoor-timestamp-local");
const weatherDescription = document.querySelector("#weather-description");

const localTimeFormatter = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
});

let requestInFlight = false;

function showLocalTime(element, timestamp) {
    const date = new Date(timestamp);
    element.dateTime = timestamp;
    element.textContent = Number.isNaN(date.getTime())
        ? timestamp
        : localTimeFormatter.format(date);
}

function showAverage(average) {
    temperatureF.textContent = `${Number(average.temperature_f).toFixed(1)}°`;
    humidityPercent.textContent = `${Number(average.humidity_percent).toFixed(1)}%`;
    temperatureC.textContent = `${Number(average.temperature_c).toFixed(1)} °C`;
    sampleCount.textContent = `${average.num_readings} samples`;
    showLocalTime(timestampLocal, average.timestamp_utc);

    status.hidden = true;
    sensor.hidden = false;
    sensorDetails.hidden = false;

    showWeather(average);
}

function showWeather(average) {
    if (average.outdoor_temperature_f === null) {
        outdoorTemperatureF.textContent = "--°";
        outdoorHumidityPercent.textContent = "--%";
        weatherDescription.textContent = "Unavailable";
        weatherStatus.hidden = false;
        weatherDetails.hidden = true;
        return;
    }

    outdoorTemperatureF.textContent = `${Number(average.outdoor_temperature_f).toFixed(1)}°`;
    outdoorHumidityPercent.textContent = `${Number(average.outdoor_humidity_percent).toFixed(1)}%`;
    outdoorTemperatureC.textContent = `${Number(average.outdoor_temperature_c).toFixed(1)} °C`;
    showLocalTime(outdoorTimestampLocal, average.outdoor_timestamp_utc);
    weatherDescription.textContent = average.outdoor_description;

    weatherStatus.hidden = true;
    weatherDetails.hidden = false;
}

async function pollAverage() {
    if (requestInFlight) {
        return;
    }

    requestInFlight = true;
    try {
        const response = await fetch(page.dataset.averageUrl, {
            headers: { Accept: "application/json" },
            cache: "no-store",
        });

        if (response.status === 503) {
            if (sensorDetails.hidden) {
                status.textContent = "Waiting for sensor readings...";
                status.hidden = false;
            }
            return;
        }

        if (!response.ok) {
            throw new Error(`Average request failed with status ${response.status}`);
        }

        showAverage(await response.json());
    } catch (error) {
        console.error("Unable to update climate readings", error);
        if (sensorDetails.hidden) {
            status.textContent = "Unable to load climate readings.";
            status.hidden = false;
        }
    } finally {
        requestInFlight = false;
    }
}

if (timestampLocal.dateTime) {
    showLocalTime(timestampLocal, timestampLocal.dateTime);
}
if (outdoorTimestampLocal.dateTime) {
    showLocalTime(outdoorTimestampLocal, outdoorTimestampLocal.dateTime);
}

pollAverage();
window.setInterval(pollAverage, POLL_INTERVAL_MS);
