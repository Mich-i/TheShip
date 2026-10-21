import math
import time
import requests
from components.components import ANALYZER_SERVER_PORT, IP
from helpers.analyzerServer import startAnalyzerServer
from helpers.communication import getPosition
from helpers.easySteering import setTarget
from helpers.energyManagement import enableComponents
from helpers.whatsupp import getMissionChat, getProgress

PLAYER_NAMES = {
    "192.168.100.50": "Stutz Michael",
    "192.168.100.51": "Eggerschwiler Marvin",
}
MISSION_CONTACT = "05 - Analyzer Alpha"
URAN_STONE = {"x": -2100, "y": 3600}
ARRIVAL_RADIUS = 100
ANALYZER_COMPONENTS = ["sensor_void_energy", "analyzer_alpha"]
FLIGHT_TIMEOUT_SECONDS = 300
ANALYSIS_TIMEOUT_SECONDS = 1800
PROGRESS_INTERVAL_SECONDS = 10

if IP not in PLAYER_NAMES:
    raise SystemExit(f"Unknown ship IP {IP}. Set SHIP_IP to one of: {', '.join(PLAYER_NAMES)}")
playerName = PLAYER_NAMES[IP]


def distanceBetween(first, second):
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


enableComponents(ANALYZER_COMPONENTS)
print("Power enabled for sensor and analyzer")

server = startAnalyzerServer()
print(f"Sensor data server listening on port {ANALYZER_SERVER_PORT}")

try:
    # Das Ziel bleibt gesetzt, damit Easy Steering das Schiff dort festhaelt.
    setTarget(URAN_STONE)
    deadline = time.monotonic() + FLIGHT_TIMEOUT_SECONDS
    while distanceBetween(getPosition(), URAN_STONE) > ARRIVAL_RADIUS:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Uran Stone not reached within {FLIGHT_TIMEOUT_SECONDS}s")
        time.sleep(1)
    print("Uran Stone reached, holding position")

    deadline = time.monotonic() + ANALYSIS_TIMEOUT_SECONDS
    percent = 0
    while percent < 100:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Analysis stuck at {percent:.1f}% after {ANALYSIS_TIMEOUT_SECONDS}s")
        time.sleep(PROGRESS_INTERVAL_SECONDS)

        # Bewusste Ausnahme: Ein einzelner Fehler beim Lesen des Fortschritts beendet den
        # langen Lauf nicht, wir fragen beim naechsten Durchgang einfach wieder.
        try:
            chat = getMissionChat(MISSION_CONTACT)
        except requests.RequestException as error:
            print(f"Could not read progress, trying again: {error}")
            continue
        if chat is None:
            print("Mission chat is gone, the mission is finished")
            break
        percent = getProgress(chat, playerName)["curr"]
        print(f"Analysis progress: {percent:.1f}%")

    print("Analysis completed")
finally:
    server.stop(grace=None)
    print("Sensor data server stopped")
