import requests
from components.components import modules

def stationsInReach():
    url = f"{modules['communication']}/stations_in_reach"
    return requests.get(url).json()["stations"]

def buy(station, what, amount):
    url = f"{modules['communication']}/buy"
    requests.post(url, json={"station": station, "what": what, "amount": amount})

def sell(station, what, amount):
    url = f"{modules['communication']}/sell"
    requests.post(url, json={"station": station, "what": what, "amount": amount})