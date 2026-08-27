import time

import requests

from components.components import modules
from helpers.communication import stations_in_reach


def set_target(target):
    """Ziel setzen.

    target ist ein Stationsname (nur wenn es im Easy-Steering-Widget einen
    Button dafuer gibt) oder ein Dict mit Koordinaten, z. B. {"x": 7000, "y": 7000}.
    """
    url = f"{modules['easy-steering']}/set_target"
    return requests.post(url, json={"target": target}).json()


def wait_until_at_station(station_name, poll_interval=2, timeout=300):
    """Wartet, bis die Station in Reichweite ist, und gibt ihre Daten zurueck."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        stations = stations_in_reach()
        if station_name in stations:
            return stations[station_name]
        time.sleep(poll_interval)

    raise TimeoutError(f"{station_name} nach {timeout}s nicht erreicht")


def goto(target, station_name):
    """Ziel setzen und warten, bis wir dort sind."""
    set_target(target)
    return wait_until_at_station(station_name)
