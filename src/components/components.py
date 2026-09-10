IP = "127.0.0.1"
RELAY_PORT = 5000

modules = {
    "easy-steering": f"http://{IP}:2009",
    "communication": f"http://{IP}:2011",
    "cargo-hold": f"http://{IP}:2012",
}

stations = {
    "elyse": {
        "name": "Elyse Terminal",
        "ws": f"ws://{IP}:2026/api",
        "field": "msg",
        "coordinates": {"x": -70565, "y": 72811},
        "peer": "192.168.100.51",
    },
    "shangris": {
        "name": "Shangris Station",
        "ws": f"ws://{IP}:2025/ws",
        "field": "data",
        "coordinates": {"x": 4446, "y": 4340},
        "peer": "192.168.100.50",
    },
}

partner = {"elyse": "shangris", "shangris": "elyse"}

COMM_ELYSE_WS = "ws://192.168.100.50:2026/api"
COMM_SHANGRIS_WS = "ws://192.168.100.51:2024/ws"

modules = {
    "easy-steering": f"http://{IP}:2009",
    "communication": f"http://{IP}:2011",
    "cargo-hold": f"http://{IP}:2012",
}