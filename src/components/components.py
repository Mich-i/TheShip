IP = "127.0.0.1"
RELAY_PORT = 5000
HTTP_TIMEOUT_SECONDS = 2
RECONNECT_DELAY_SECONDS = 2
MISSION_DURATION_SECONDS = 30
MISSION_STEP_SECONDS = 5
START_SEED = [1, 2, 3, 4]

modules = {
    "easy-steering": f"http://{IP}:2009",
    "communication": f"http://{IP}:2011",
    "cargo-hold": f"http://{IP}:2012",
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
