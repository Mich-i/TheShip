import time
import requests
from components.components import modules

SENSOR_URL = modules["sensor-void-energy"]
MEASUREMENT_ID = "vacuum-energy-reading"
POLL_INTERVAL_SECONDS = 0.2
MEASUREMENT_TIMEOUT_SECONDS = 10


def discardMeasurement():
    requests.delete(f"{SENSOR_URL}/measurements/{MEASUREMENT_ID}", timeout=5)


def measureVacuumEnergy():
    discardMeasurement()
    deadline = time.monotonic() + MEASUREMENT_TIMEOUT_SECONDS

    # Nach einem DELETE lehnt der Sensor dieselbe ID noch bis ca. 1 s lang ab
    # ("duplicated request_id found"). Dann kurz warten und nochmals ausloesen.
    while True:
        response = requests.post(
            f"{SENSOR_URL}/trigger_measurement",
            json={"request_id": MEASUREMENT_ID},
            timeout=5,
        )
        if "duplicated request_id" not in response.text:
            break
        if time.monotonic() > deadline:
            raise TimeoutError(f"Sensor still rejects {MEASUREMENT_ID} after {MEASUREMENT_TIMEOUT_SECONDS}s")
        time.sleep(POLL_INTERVAL_SECONDS)
    response.raise_for_status()

    try:
        while time.monotonic() < deadline:
            measurement = requests.get(
                f"{SENSOR_URL}/measurements/{MEASUREMENT_ID}", timeout=5
            ).json()
            if measurement.get("state") == "measured":
                return measurement["result"]
            time.sleep(POLL_INTERVAL_SECONDS)

        raise TimeoutError(
            f"Sensor returned no result within {MEASUREMENT_TIMEOUT_SECONDS}s"
        )
    finally:
        discardMeasurement()