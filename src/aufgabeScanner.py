import math
import time
import requests
from components.components import IP
from helpers.communication import getPosition, stationsInReach
from helpers.easySteering import setTarget
from helpers.scanner import getObject, startScanner
from helpers.whatsupp import describeMessage, getMissionChat, getProgressEntries

PLAYER_NAMES = {
    "192.168.100.50": "Stutz Michael",
    "192.168.100.51": "Eggerschwiler Marvin",
}
MISSION_CONTACT = "09 - Scanner"
STATION_NAME = "G-Station 0-5"
RENDEZVOUS = {"x": 14148, "y": 10804}
RENDEZVOUS_RADIUS = 100

# Ziel = Station + Geschwindigkeit * LEAD_SECONDS. Easy Steering bremst vor dem Ziel ab,
# deshalb liegt das Ziel vor der Station, damit wir neben ihr fliegen statt hinter ihr.
LEAD_SECONDS = 3
VELOCITY_WINDOW_SECONDS = 1
STALE_SECONDS = 2
LOST_SECONDS = 10
LOOP_INTERVAL_SECONDS = 0.3
LOG_INTERVAL_SECONDS = 1
# Die Mission ist erst fertig, wenn beide Schiffe gleichzeitig 60 s erreicht haben.
# Die Frist laesst Zeit, auf den Partner zu warten, und fuer mehrere 60-s-Versuche.
MAX_DURATION_SECONDS = 600
# Nach dem Abschluss noch auf weitere WhatsUpp-Nachrichten (Teilaufgaben) warten
FOLLOW_UP_SECONDS = 15

if IP not in PLAYER_NAMES:
    raise SystemExit(f"Unknown ship IP {IP}. Set SHIP_IP to one of: {', '.join(PLAYER_NAMES)}")
playerName = PLAYER_NAMES[IP]


def distanceBetween(first, second):
    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


def printNewMessages(chat, seenMessageCount):
    for message in chat["messages"][seenMessageCount:]:
        print(f"WhatsUpp {describeMessage(message)}")
    return len(chat["messages"])


print(f"Ship {IP} ({playerName}): following {STATION_NAME}")
startScanner(IP)
startTime = time.monotonic()
deadline = startTime + MAX_DURATION_SECONDS

try:
    chat = getMissionChat(MISSION_CONTACT)
    if chat is None:
        raise RuntimeError(f"No WhatsUpp chat '{MISSION_CONTACT}' found")
    seenMessageCount = len(chat["messages"])
    shownChoices = chat["choices"]

    setTarget(RENDEZVOUS)
    while distanceBetween(getPosition(), RENDEZVOUS) > RENDEZVOUS_RADIUS:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Rendezvous not reached within {MAX_DURATION_SECONDS}s")
        time.sleep(1)
    print(f"Rendezvous {RENDEZVOUS['x']}/{RENDEZVOUS['y']} reached")

    stationHistory = []
    target = RENDEZVOUS
    wasInReach = False
    nextLogAt = 0
    missionFinished = False

    while not missionFinished:
        now = time.monotonic()
        if now > deadline:
            raise TimeoutError(f"Mission not finished within {MAX_DURATION_SECONDS}s")

        station = getObject(STATION_NAME)
        if station is not None and (not stationHistory or station["receivedAt"] != stationHistory[-1]["receivedAt"]):
            stationHistory.append(station)
            stationHistory = [
                entry for entry in stationHistory
                if entry["receivedAt"] >= station["receivedAt"] - VELOCITY_WINDOW_SECONDS
            ]

        dataAge = now - stationHistory[-1]["receivedAt"] if stationHistory else math.inf
        if dataAge <= STALE_SECONDS and len(stationHistory) >= 2:
            oldest = stationHistory[0]
            newest = stationHistory[-1]
            elapsedBetween = newest["receivedAt"] - oldest["receivedAt"]
            velocityX = (newest["x"] - oldest["x"]) / elapsedBetween
            velocityY = (newest["y"] - oldest["y"]) / elapsedBetween
            target = {"x": newest["x"] + velocityX * LEAD_SECONDS, "y": newest["y"] + velocityY * LEAD_SECONDS}
        elif dataAge > LOST_SECONDS:
            target = RENDEZVOUS

        try:
            setTarget(target)
            position = getPosition()
            inReach = STATION_NAME in stationsInReach()
            chat = getMissionChat(MISSION_CONTACT)
        except requests.RequestException as error:
            print(f"Request failed: {error}")
            time.sleep(LOOP_INTERVAL_SECONDS)
            continue

        progressEntries = getProgressEntries(chat)
        if playerName not in progressEntries:
            raise RuntimeError(f"No progress for {playerName} in WhatsUpp chat '{MISSION_CONTACT}'")
        missionFinished = chat["is_finished"] or all(entry["done"] for entry in progressEntries.values())

        seenMessageCount = printNewMessages(chat, seenMessageCount)
        if chat["choices"] != shownChoices:
            print(f"WhatsUpp choices: {chat['choices']}")
            shownChoices = chat["choices"]

        distanceText = "unknown"
        stationText = "unknown"
        if stationHistory:
            distanceText = f"{distanceBetween(position, stationHistory[-1]):.0f}"
            stationText = f"{stationHistory[-1]['x']:.0f}/{stationHistory[-1]['y']:.0f}"

        if inReach != wasInReach:
            print(f"{'Entered' if inReach else 'Left'} reach of {STATION_NAME} at distance {distanceText}")
            wasInReach = inReach

        if now >= nextLogAt:
            progressText = " ".join(
                f"{name.split()[0]}={entry['curr']:.0f}/{entry['max']:.0f}s{'(done)' if entry['done'] else ''}"
                for name, entry in progressEntries.items()
            )
            print(
                f"t={now - startTime:5.1f}s ship={position['x']:.0f}/{position['y']:.0f} "
                f"station={stationText} distance={distanceText} "
                f"in reach={'yes' if inReach else 'no'} progress: {progressText}"
            )
            nextLogAt = now + LOG_INTERVAL_SECONDS

        time.sleep(LOOP_INTERVAL_SECONDS)

    print(f"Mission finished after {time.monotonic() - startTime:.0f}s, watching WhatsUpp for {FOLLOW_UP_SECONDS}s")
    followUpEnd = time.monotonic() + FOLLOW_UP_SECONDS
    while time.monotonic() < followUpEnd:
        try:
            chat = getMissionChat(MISSION_CONTACT)
        except requests.RequestException as error:
            print(f"Request failed: {error}")
        else:
            seenMessageCount = printNewMessages(chat, seenMessageCount)
            if chat["choices"] != shownChoices:
                print(f"WhatsUpp choices: {chat['choices']}")
                shownChoices = chat["choices"]
        time.sleep(1)
finally:
    try:
        setTarget("stop")
        print("Ship stopped")
    except requests.RequestException as error:
        print(f"Could not stop ship: {error}")
