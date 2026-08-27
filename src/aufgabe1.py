# Ziel: Das Schiff vollbeladen mit Eisen bei Vesta Station (7000/7000) andocken.
# Azura Station (-1000/1000) verkauft Eisen guenstig, Core Station (0/0) kauft es teurer.

from helpers.communication import buy, sell
from helpers.easy_steering import set_target, wait_until_at_station
from helpers.cargo_hold import get_inventory

TARGET_AMOUNT = 12

# Money making loop
bought_target_amount = False

while not bought_target_amount:
    set_target("Azura Station")
    azura_station = wait_until_at_station("Azura Station")

    iron_price = azura_station["resources"]["IRON"]["buy_price"]
    inventory = get_inventory()

    affordable_amount = inventory["hold"]["credits"] // iron_price
    amount_to_buy = min(affordable_amount, inventory["hold"]["hold_free"])

    if amount_to_buy > 0:
        buy("Azura Station", "IRON", amount_to_buy)

    if amount_to_buy >= TARGET_AMOUNT:
        bought_target_amount = True
    else:
        set_target("Core Station")
        wait_until_at_station("Core Station")

        inventory = get_inventory()
        iron_amount = inventory["hold"]["resources"]["IRON"]
        if iron_amount > 0:
            sell("Core Station", "IRON", iron_amount)

# Vesta Station hat keinen Button im Easy-Steering-Widget -> Koordinaten noetig
set_target({"x": 7000, "y": 7000})
wait_until_at_station("Vesta Station")

print("Arrived at Vesta Station")
