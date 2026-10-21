import requests
from components.components import modules

REQUEST_TIMEOUT_SECONDS = 5


def findActiveNode():
    for node in modules["energy-management"]:
        try:
            status = requests.get(f"{node}/status", timeout=REQUEST_TIMEOUT_SECONDS).json()
        except requests.RequestException:
            continue
        if status.get("role") == "active":
            return node
    raise RuntimeError("No active energy management node found")


def enableComponents(componentNames):
    node = findActiveNode()

    # PUT ersetzt alle Limits: erst lesen, ergaenzen, dann alles zurueckschicken.
    limits = requests.get(f"{node}/limits", timeout=REQUEST_TIMEOUT_SECONDS).json()
    for componentName in componentNames:
        limits[componentName] = 1.0

    response = requests.put(f"{node}/limits", json=limits, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    if response.json().get("kind") != "success":
        raise RuntimeError(f"Energy management rejected the limits: {response.text}")