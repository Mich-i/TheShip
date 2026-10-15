import math
import time
from components.components import IP
from helpers.communication import getPosition
from helpers.easySteering import setTarget
from helpers.scanner import getObject, startScanner
from helpers.whatsupp import getMissionChat, getProgress

PLAYER_NAMES = {
    "192.168.100.50": "Stutz Michael",
    "192.168.100.51": "Eggerschwiler Marvin",
}
MISSION_CONTACT = "09 - Scanner"
STATION_NAME = "G-Station 0-5"
RENDEZVOUS = {"x": 14148, "y": 10804}
RENDEZVOUS_RADIUS = 100
LEAD_SECONDS = 3
VELOCITY_WINDOW_SECONDS = 1
LOOP_INTERVAL_SECONDS = 0.3
LOG_INTERVAL_SECONDS = 2
MAX_RUNTIME_SECONDS = 600

if IP not in PLAYER_NAMES:
    raise SystemExit(f"Unknown ship IP {IP}. Set SHIP_IP to one of: {', '.join(PLAYER_NAMES)}")
playerName = PLAYER_NAMES[IP]

def distanceBetween(first, second):
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])

print(f"Ship {IP} ({playerName}) is following {STATION_NAME}")
startScanner(IP)
deadline = time.monotonic() + MAX_RUNTIME_SECONDS

try:
    setTarget(RENDEZVOUS)
    while distanceBetween(getPosition(), RENDEZVOUS) > RENDEZVOUS_RADIUS:
        if time.monotonic() > deadline:
            raise SystemExit(f"Time limit of {MAX_RUNTIME_SECONDS}s reached")
        time.sleep(1)
    print("Rendezvous reached")

    stationHistory = []
    nextLogAt = 0
    chat = getMissionChat(MISSION_CONTACT)

    while chat is not None and not chat["is_finished"]:
        if time.monotonic() > deadline:
            raise SystemExit(f"Time limit of {MAX_RUNTIME_SECONDS}s reached")

        station = getObject(STATION_NAME)
        if station is not None:
            stationHistory.append(station)
            stationHistory = [
                entry for entry in stationHistory
                if entry["receivedAt"] >= station["receivedAt"] - VELOCITY_WINDOW_SECONDS
            ]
            oldest = stationHistory[0]
            elapsedSeconds = station["receivedAt"] - oldest["receivedAt"]
            if elapsedSeconds > 0:
                velocityX = (station["x"] - oldest["x"]) / elapsedSeconds
                velocityY = (station["y"] - oldest["y"]) / elapsedSeconds
                setTarget({"x": station["x"] + velocityX * LEAD_SECONDS, "y": station["y"] + velocityY * LEAD_SECONDS})

        if station is not None and time.monotonic() >= nextLogAt:
            progress = getProgress(chat, playerName)
            distance = distanceBetween(getPosition(), station)
            print(f"distance={distance:.0f} progress={progress['curr']:.0f}/{progress['max']:.0f}s")
            nextLogAt = time.monotonic() + LOG_INTERVAL_SECONDS

        time.sleep(LOOP_INTERVAL_SECONDS)
        chat = getMissionChat(MISSION_CONTACT)

    print("Mission completed")
finally:
    setTarget("stop")
    print("Ship stopped")
