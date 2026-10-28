import os

# Andere VM bzw. vom Laptop: SHIP_IP=192.168.100.51 python src/<skript>.py
IP = os.environ.get("SHIP_IP", "192.168.100.50")
RELAY_PORT = 5000
# Unser gRPC-Server, den der Analyzer-Pod unter <VM-IP>:2102 abfragt
ANALYZER_SERVER_PORT = 2102
HTTP_TIMEOUT_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 10
RECONNECT_DELAY_SECONDS = 2
MISSION_DURATION_SECONDS = 30
MISSION_STEP_SECONDS = 5
START_SEED = [1, 2, 3, 4]
MONGO_CONNECTION_STRING = f"mongodb://theship:theship1234@{IP}:2021/theshipdb"

modules = {
    "easy-steering": f"http://{IP}:2009",
    "communication": f"http://{IP}:2011",
    "cargo-hold": f"http://{IP}:2012",
    "laser": f"http://{IP}:2018",
    "energy-management": [f"http://{IP}:2032", f"http://{IP}:2033"],
    "sensor-void-energy": f"http://{IP}:2037",
    "whatsupp": f"http://{IP}:2040",
}

ELYSE = {
    "name": "Elyse Terminal",
    "ws_url": f"ws://{IP}:2026/api",
    "field": "msg",
    "coordinates": {"x": -70565, "y": 72811},
    "peer": "192.168.100.51",
    "partner": "Shangris Station",
}

SHANGRIS = {
    "name": "Shangris Station",
    "ws_url": f"ws://{IP}:2025/ws",
    "field": "data",
    "coordinates": {"x": 4446, "y": 4340},
    "peer": "192.168.100.50",
    "partner": "Elyse Terminal",
}

STATIONS = {
    "elyse": ELYSE,
    "shangris": SHANGRIS,
}

PARTNER = {
    "elyse": "shangris",
    "shangris": "elyse",
}

RELIEF = {
    "name": "Relief Station",
    "coordinates": {"x": 150000, "y": 150000},
}