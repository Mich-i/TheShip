import time
import uuid
import requests
from components.components import modules

def measureVacuumEnergy():
    url = f"{modules['sensor-void-energy']}"
    requestId = uuid.uuid4().hex
    requests.post(f"{url}/trigger_measurement", json={"request_id": requestId})

    measurement = {"state": "measuring"}
    while measurement["state"] != "measured":
        time.sleep(0.2)
        measurement = requests.get(f"{url}/measurements/{requestId}").json()

    requests.delete(f"{url}/measurements/{requestId}")
    return measurement["result"]