import requests
from components.components import modules

def getInventory():
    url = f"{modules['cargo-hold']}/hold"
    response = requests.get(url)
    return response.json()
