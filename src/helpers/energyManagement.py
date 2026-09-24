import requests
from components.components import modules

def enableShieldComponents():
    for node in modules["energy-management"]:
        if requests.get(f"{node}/status").json()["role"] != "active":
            continue
        limits = requests.get(f"{node}/limits").json()
        limits["sensor_void_energy"] = 1.0
        limits["shield_generator"] = 1.0
        requests.put(f"{node}/limits", json=limits)
        return
    raise RuntimeError("Kein aktiver Energy-Management-Node gefunden")