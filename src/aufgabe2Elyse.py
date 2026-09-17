import time
from components.components import IP
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.relay import sendToPeer, startServer
from helpers.stationChat import connect

NAME = "Elyse Terminal"
WS = f"ws://{IP}:2026/api"
FIELD = "msg"
COORDINATES = {"x": -70565, "y": 72811}
PEER = "192.168.100.51"
PARTNER = "Shangris Station"

DURATION = 30
SEED = [1, 2, 3, 4]

print(f"Fliege zu {NAME}")
setTarget(COORDINATES)
waitUntilAtStation(NAME)
setTarget("stop")
print("Angekommen, halte Position")

sendToStation = connect(NAME, WS, FIELD, lambda payload: sendToPeer(PEER, NAME, payload))

startServer(lambda message: sendToStation(message["payload"], message["from"]))

sendToStation(SEED, PARTNER)

for remaining in range(DURATION, 0, -5):
    print(f"connected: {remaining}s")
    time.sleep(5)

print("Mission completed")
