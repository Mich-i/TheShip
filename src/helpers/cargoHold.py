import requests
from components.components import REQUEST_TIMEOUT_SECONDS, modules

def getInventory():
    url = f"{modules['cargo-hold']}/hold"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    return response.json()
