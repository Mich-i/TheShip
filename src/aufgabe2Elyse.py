import time
from components.components import ELYSE, MISSION_DURATION_SECONDS, MISSION_STEP_SECONDS, START_SEED
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.relay import sendToPeer, startServer
from helpers.stationChat import connectToStation

print(f"Fliege zu {ELYSE['name']}")
setTarget(ELYSE["coordinates"])
waitUntilAtStation(ELYSE["name"])
setTarget("stop")
print("Angekommen, halte Position")

sendToStation = connectToStation(
    ELYSE["name"],
    ELYSE["ws_url"],
    ELYSE["field"],
    lambda payload: sendToPeer(ELYSE["peer"], ELYSE["name"], payload),
)

startServer(lambda message: sendToStation(message["payload"], message["from"]))

sendToStation(START_SEED, ELYSE["partner"])

for remaining in range(MISSION_DURATION_SECONDS, 0, -MISSION_STEP_SECONDS):
    print(f"connected: {remaining}s")
    time.sleep(MISSION_STEP_SECONDS)

print("Mission completed")