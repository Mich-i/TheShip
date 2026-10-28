import math
import time
from helpers.cargoHold import getInventory
from helpers.communication import getPosition, stationsInReach
from helpers.easySteering import setTarget
from helpers.laser import activateLaser, aimLaserAt, deactivateLaser, getLaserState
from helpers.whatsupp import getMissionChat

MISSION_CONTACT = "10 - Laser"
ARAKROCK = {"x": -18236, "y": -11783}
# Direkt auf dem Asteroiden trifft der Laser nicht, darum mit Abstand daneben halten.
MINING_POSITION = {"x": ARAKROCK["x"] + 300, "y": ARAKROCK["y"]}
VESTA = "Vesta Station"
VESTA_COORDINATES = {"x": 7000, "y": 7000}
ARRIVAL_RADIUS = 50
FLIGHT_TIMEOUT_SECONDS = 300
MINING_TIMEOUT_SECONDS = 120
MINING_INTERVAL_SECONDS = 1


def distanceBetween(first, second):
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


def flyTo(target):
    setTarget(target)
    deadline = time.monotonic() + FLIGHT_TIMEOUT_SECONDS
    while distanceBetween(getPosition(), target) > ARRIVAL_RADIUS:
        if time.monotonic() > deadline:
            raise TimeoutError(f"{target} not reached within {FLIGHT_TIMEOUT_SECONDS}s")
        time.sleep(1)


def stoneInHold():
    hold = getInventory()["hold"]
    return hold["resources"]["STONE"], hold["hold_size"]


print("Mining stone at Arakrock")
flyTo(MINING_POSITION)
print("Arakrock reached")

# Der Laser schaltet sich nach etwa 10 s selbst ab, darum bei Bedarf neu aktivieren.
stone, holdSize = stoneInHold()
deadline = time.monotonic() + MINING_TIMEOUT_SECONDS
try:
    while stone < holdSize:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Hold not full within {MINING_TIMEOUT_SECONDS}s. Is the technician logged in?")

        aimLaserAt(getPosition(), ARAKROCK)
        state = getLaserState()
        if not state["is_active"] and not state["is_cooling_down"]:
            activateLaser()

        print(f"stone={stone}/{holdSize} active={state['is_active']} mining={state['is_mining']}")
        time.sleep(MINING_INTERVAL_SECONDS)
        stone, holdSize = stoneInHold()
finally:
    deactivateLaser()
    print("Laser deactivated")

print(f"Hold full ({stone}/{holdSize}), flying to {VESTA}")
# Das Ziel bleibt gesetzt, damit das Schiff bei Vesta angedockt bleibt.
flyTo(VESTA_COORDINATES)
if VESTA not in stationsInReach():
    raise RuntimeError(f"{VESTA} not in reach")
print(f"Docked at {VESTA}")

chat = getMissionChat(MISSION_CONTACT)
if chat is None:
    print("Mission completed")
else:
    for message in chat["messages"]:
        if message["data"]["kind"] == "progress":
            for entry in message["data"]["entries"]:
                print(f"{entry['name']}: {'done' if entry['done'] else 'open'}")
    print("Mission completed" if chat["is_finished"] else "Waiting for partner")
