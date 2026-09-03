import sys
import time

from components.components import partner, stations
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.relay import sendToPeer, startServer
from helpers.stationChat import connect

DURATION = 30
SEED = [1, 2, 3, 4]


def main(key):
    station = stations[key]
    partnerStation = stations[partner[key]]

    print(f"Fliege zu {station['name']}")
    setTarget(station["coordinates"])
    waitUntilAtStation(station["name"])
    setTarget("stop")
    print("Angekommen, halte Position")

    sendToStation = connect(
        station,
        lambda payload: sendToPeer(station["peer"], station["name"], payload),
    )

    startServer(lambda message: sendToStation(message["payload"], message["from"]))

    sendToStation(SEED, partnerStation["name"])

    for remaining in range(DURATION, 0, -5):
        print(f"connected: {remaining}s")
        time.sleep(5)

    print("Mission completed")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in stations:
        sys.exit(f"Aufruf: python src\\aufgabe2.py {' | '.join(stations)}")
    main(sys.argv[1])