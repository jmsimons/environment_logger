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
