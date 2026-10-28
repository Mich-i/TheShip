import math
import requests
from components.components import REQUEST_TIMEOUT_SECONDS, modules

# Gemessen: Laserwinkel 0 = Schiffswinkel - 90, also Laserwinkel = Weltwinkel - Schiffswinkel + 90.
# Weltwinkel laufen im Uhrzeigersinn: 0 = +x, 90 = -y, 180 = -x.
LASER_ANGLE_OFFSET = 90


def getLaserState():
    url = f"{modules['laser']}/state"
    return requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS).json()


def activateLaser():
    requests.post(f"{modules['laser']}/activate", timeout=REQUEST_TIMEOUT_SECONDS)


def deactivateLaser():
    requests.post(f"{modules['laser']}/deactivate", timeout=REQUEST_TIMEOUT_SECONDS)


def aimLaserAt(shipPosition, target):
    worldAngle = -math.degrees(math.atan2(target["y"] - shipPosition["y"], target["x"] - shipPosition["x"]))
    angle = (worldAngle - shipPosition["angle"] + LASER_ANGLE_OFFSET) % 360
    requests.put(f"{modules['laser']}/angle", json={"angle": angle}, timeout=REQUEST_TIMEOUT_SECONDS)
