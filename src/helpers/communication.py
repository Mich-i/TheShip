import requests
from components.components import REQUEST_TIMEOUT_SECONDS, modules

def getPosition():
    url = f"{modules['communication']}/pos"
    return requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS).json()["pos"]

def stationsInReach():
    url = f"{modules['communication']}/stations_in_reach"
    return requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS).json()["stations"]

def buy(station, what, amount):
    url = f"{modules['communication']}/buy"
    requests.post(url, json={"station": station, "what": what, "amount": amount}, timeout=REQUEST_TIMEOUT_SECONDS)

def sell(station, what, amount):
    url = f"{modules['communication']}/sell"
    requests.post(url, json={"station": station, "what": what, "amount": amount}, timeout=REQUEST_TIMEOUT_SECONDS)