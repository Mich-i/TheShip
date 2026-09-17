import time
from components.components import IP
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.relay import sendToPeer, startServer
from helpers.stationChat import connect

NAME = "Shangris Station"
WS = f"ws://{IP}:2025/ws"
FIELD = "data"
COORDINATES = {"x": 4446, "y": 4340}
PEER = "192.168.100.50"
PARTNER = "Elyse Terminal"

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
