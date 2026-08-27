import requests
import time
from components.components import modules

def setTarget(target):
    url = f"{modules['easy-steering']}/set_target"
    requests.post(url, json={"target": target})

def waitUntilAtStation(station_name):
    while True:
        url = f"{modules['communication']}/stations_in_reach"
        response = requests.get(url)
        stations = response.json()["stations"]

        if station_name in stations:
            return stations[station_name]

        time.sleep(2)
