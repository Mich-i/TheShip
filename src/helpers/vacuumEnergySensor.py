import time
import requests
from components.components import modules

SENSOR_URL = modules["sensor-void-energy"]
MEASUREMENT_ID = "shield-generator-input"
POLL_INTERVAL_SECONDS = 0.2
MEASUREMENT_TIMEOUT_SECONDS = 10


def discardMeasurement():
    requests.delete(f"{SENSOR_URL}/measurements/{MEASUREMENT_ID}", timeout=5)


def measureVacuumEnergy():
    discardMeasurement()

    requests.post(
        f"{SENSOR_URL}/trigger_measurement",
        json={"request_id": MEASUREMENT_ID},
        timeout=5,
    ).raise_for_status()

    deadline = time.monotonic() + MEASUREMENT_TIMEOUT_SECONDS
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