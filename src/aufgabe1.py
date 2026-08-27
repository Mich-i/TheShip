from helpers.communication import buy, sell
from helpers.easySteering import setTarget, waitUntilAtStation
from helpers.cargoHold import getInventory

TARGETAMOUNT = 12

AZURA = "Azura Station"
CORE = "Core Station"
VESTA = "Vesta Station"
VESTA_COORDINATES = {"x": 7000, "y": 7000}

boughtTargetAmount = False

while not boughtTargetAmount:
    setTarget(AZURA)
    azuraStation = waitUntilAtStation(AZURA)

    ironPrice = azuraStation["resources"]["IRON"]["buy_price"]
    inventory = getInventory()

    affordableAmount = inventory["hold"]["credits"] // ironPrice
    amountToBuy = min(affordableAmount, inventory["hold"]["hold_free"])

    if amountToBuy > 0:
        buy(AZURA, "IRON", amountToBuy)

    if amountToBuy >= TARGETAMOUNT:
        boughtTargetAmount = True
    else:
        setTarget(CORE)
        waitUntilAtStation(CORE)

        inventory = getInventory()
        ironAmount = inventory["hold"]["resources"]["IRON"]
        if ironAmount > 0:
            sell(CORE, "IRON", ironAmount)

setTarget(VESTA_COORDINATES)
waitUntilAtStation(VESTA)

print("Mission completed")
