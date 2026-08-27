"""Aufgabe 1: vollbeladen mit Eisen bei Vesta Station (7000/7000) andocken.

Azura Station (-1000/1000) verkauft Eisen guenstig, Core Station (0/0) kauft
es teurer. Also so lange pendeln, bis der Laderaum voll ist.
"""

from helpers.cargo_hold import get_hold
from helpers.communication import buy, sell
from helpers.easy_steering import goto

VESTA_STATION = {"x": 7000, "y": 7000}

azura = goto("Azura Station", "Azura Station")
hold = get_hold()

while hold["hold_free"] > 0:
    iron_price = azura["resources"]["IRON"]["buy_price"]
    amount_to_buy = min(hold["credits"] // iron_price, hold["hold_free"])

    if amount_to_buy == 0:
        break

    buy("Azura Station", "IRON", amount_to_buy)
    hold = get_hold()
    print(f"Gekauft: {amount_to_buy} IRON, noch frei: {hold['hold_free']}")

    if hold["hold_free"] == 0:
        break

    goto("Core Station", "Core Station")
    sell("Core Station", "IRON", hold["resources"]["IRON"])
    hold = get_hold()
    print(f"Verkauft, Credits: {hold['credits']}")

    azura = goto("Azura Station", "Azura Station")

# Vesta Station hat keinen Button im Easy-Steering-Widget -> Koordinaten noetig
goto(VESTA_STATION, "Vesta Station")

print("Angekommen bei Vesta Station:", get_hold())
