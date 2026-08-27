import requests

from components.components import modules


def stations_in_reach():
    url = f"{modules['communication']}/stations_in_reach"
    return requests.get(url).json()["stations"]


def buy(station, what, amount):
    url = f"{modules['communication']}/buy"
    return requests.post(
        url, json={"station": station, "what": what, "amount": amount}
    ).json()


def sell(station, what, amount):
    url = f"{modules['communication']}/sell"
    return requests.post(
        url, json={"station": station, "what": what, "amount": amount}
    ).json()
