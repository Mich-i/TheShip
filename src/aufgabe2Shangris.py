import time
from components.components import MISSION_DURATION_SECONDS, MISSION_STEP_SECONDS, SHANGRIS, START_SEED
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.relay import sendToPeer, startServer
from helpers.stationChat import connectToStation

print(f"Fliege zu {SHANGRIS['name']}")
setTarget(SHANGRIS["coordinates"])
waitUntilAtStation(SHANGRIS["name"])
setTarget("stop")
print("Angekommen, halte Position")

sendToStation = connectToStation(
    SHANGRIS["name"],
    SHANGRIS["ws_url"],
    SHANGRIS["field"],
    lambda payload: sendToPeer(SHANGRIS["peer"], SHANGRIS["name"], payload),
)

startServer(lambda message: sendToStation(message["payload"], message["from"]))

sendToStation(START_SEED, SHANGRIS["partner"])

for remaining in range(MISSION_DURATION_SECONDS, 0, -MISSION_STEP_SECONDS):
    print(f"connected: {remaining}s")
    time.sleep(MISSION_STEP_SECONDS)

print("Mission completed")