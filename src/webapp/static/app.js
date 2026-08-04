const POLL_INTERVAL_MS = 10_000;

const page = document.querySelector("[data-average-url]");
const status = document.querySelector("#status");
const readings = document.querySelector("#readings");
const details = document.querySelector("#details");
const temperatureF = document.querySelector("#temperature-f");
const humidityPercent = document.querySelector("#humidity-percent");
const temperatureC = document.querySelector("#temperature-c");
const sampleCount = document.querySelector("#sample-count");
const timestampUtc = document.querySelector("#timestamp-utc");
const weatherStatus = document.querySelector("#weather-status");
const weatherReadings = document.querySelector("#weather-readings");
const weatherDetails = document.querySelector("#weather-details");
const outdoorTemperatureF = document.querySelector("#outdoor-temperature-f");
const outdoorHumidityPercent = document.querySelector("#outdoor-humidity-percent");
const outdoorTemperatureC = document.querySelector("#outdoor-temperature-c");
const outdoorTimestampUtc = document.querySelector("#outdoor-timestamp-utc");
const weatherDescription = document.querySelector("#weather-description");

let requestInFlight = false;

function showAverage(average) {
    temperatureF.textContent = `${Number(average.temperature_f).toFixed(1)}°`;
    humidityPercent.textContent = `${Number(average.humidity_percent).toFixed(1)}%`;
    temperatureC.textContent = `${Number(average.temperature_c).toFixed(1)} °C`;
    sampleCount.textContent = `${average.sample_count} samples`;
    timestampUtc.textContent = `${average.timestamp_utc} UTC`;

    status.hidden = true;
    readings.hidden = false;
    details.hidden = false;

    showWeather(average);
}

function showWeather(average) {
    if (average.outdoor_temperature_f === null) {
        weatherStatus.hidden = false;
        weatherReadings.hidden = true;
        weatherDetails.hidden = true;
        return;
    }

    outdoorTemperatureF.textContent = `${Number(average.outdoor_temperature_f).toFixed(1)}°`;
    outdoorHumidityPercent.textContent = `${Number(average.outdoor_humidity_percent).toFixed(1)}%`;
    outdoorTemperatureC.textContent = `${Number(average.outdoor_temperature_c).toFixed(1)} °C`;
    outdoorTimestampUtc.textContent = `${average.outdoor_timestamp_utc} UTC`;
    weatherDescription.textContent = average.outdoor_description;

    weatherStatus.hidden = true;
    weatherReadings.hidden = false;
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
            if (readings.hidden) {
                status.textContent = "Collecting the first minute of samples...";
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
        if (readings.hidden) {
            status.textContent = "Unable to load climate readings.";
            status.hidden = false;
        }
    } finally {
        requestInFlight = false;
    }
}

pollAverage();
window.setInterval(pollAverage, POLL_INTERVAL_MS);
