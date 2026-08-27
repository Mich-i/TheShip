import requests

from components.components import modules


def get_hold():
    """Laderaum: resources, credits, hold_size, hold_free."""
    url = f"{modules['cargo-hold']}/hold"
    return requests.get(url).json()["hold"]
