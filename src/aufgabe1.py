from helpers.communication import buy, sell
from helpers.easy_steering import setTarget, waitUntilAtStation
from helpers.cargo_hold import getInventory

TARGETAMOUNT = 12

boughtTargetAmount = False

while not boughtTargetAmount:
    setTarget("Azura Station")
    azuraStation = waitUntilAtStation("Azura Station")

    ironPrice = azuraStation["resources"]["IRON"]["buy_price"]
    inventory = getInventory()

    affordableAmount = inventory["hold"]["credits"] // ironPrice
    amountToBuy = min(affordableAmount, inventory["hold"]["hold_free"])

    if amountToBuy > 0:
        buy("Azura Station", "IRON", amountToBuy)

    if amountToBuy >= TARGETAMOUNT:
        boughtTargetAmount = True
    else:
        setTarget("Core Station")
        waitUntilAtStation("Core Station")

        inventory = getInventory()
        ironAmount = inventory["hold"]["resources"]["IRON"]
        if ironAmount > 0:
            sell("Core Station", "IRON", ironAmount)

setTarget({"x": 7000, "y": 7000})
waitUntilAtStation("Vesta Station")

print("Mission completed")
