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
# Gemessen: ~2.5 % pro Sekunde, also ~40 s bis 100 %. Der Rest ist Zeit, bis auch
# der Partner auf 100 % ist: Die Mission ist erst fertig, wenn beide gleichzeitig 100 % haben.
ANALYSIS_TIMEOUT_SECONDS = 600
PROGRESS_INTERVAL_SECONDS = 5

if IP not in PLAYER_NAMES:
    raise SystemExit(f"Unknown ship IP {IP}. Set SHIP_IP to one of: {', '.join(PLAYER_NAMES)}")
playerName = PLAYER_NAMES[IP]


def distanceBetween(first, second):
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


print(f"Ship {IP} ({playerName}): analyzing Uran Stone")
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

    # Der Fortschritt faellt auf 0, sobald der Analyzer keine Daten mehr bekommt.
    # Darum weiter Daten liefern, bis die Mission fuer beide abgeschlossen ist
    # (is_finished, oder der Chat verschwindet nach dem Abschluss).
    deadline = time.monotonic() + ANALYSIS_TIMEOUT_SECONDS
    chat = getMissionChat(MISSION_CONTACT)
    while chat is not None and not chat["is_finished"]:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Mission not finished within {ANALYSIS_TIMEOUT_SECONDS}s")

        progressText = ", ".join(
            f"{name} {getProgress(chat, name)['curr']:.0f}%" for name in PLAYER_NAMES.values()
        )
        print(f"Analysis progress: {progressText}")
        time.sleep(PROGRESS_INTERVAL_SECONDS)

        # Bewusste Ausnahme: Ein einzelner Fehler beim Lesen des Fortschritts beendet den
        # Lauf nicht, wir fragen beim naechsten Durchgang einfach wieder.
        try:
            chat = getMissionChat(MISSION_CONTACT)
        except requests.RequestException as error:
            print(f"Could not read progress, trying again: {error}")

    print("Mission completed")
finally:
    server.stop(grace=None)
    print("Sensor data server stopped")
