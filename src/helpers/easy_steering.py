import requests
import time

from components.components import modules


def set_target(target):
    url = f"{modules['easy-steering']}/set_target"
    requests.post(url, json={"target": target})


def wait_until_at_station(station_name):
    while True:
        url = f"{modules['communication']}/stations_in_reach"
        response = requests.get(url)
        stations = response.json()["stations"]

        if station_name in stations:
            return stations[station_name]

        time.sleep(2)
