from components.components import RELIEF
from helpers.communication import stationsInReach
from helpers.easySteering import setTarget
from helpers.energyManagement import enableShieldComponents
from helpers.vacuumEnergySensor import measureVacuumEnergy
from helpers.vacuumEnergyStore import storeVacuumEnergy

enableShieldComponents()
storeVacuumEnergy(measureVacuumEnergy())

setTarget(RELIEF["coordinates"])
print(f"Kurs auf {RELIEF['name']} gesetzt")

while RELIEF["name"] not in stationsInReach():
    storeVacuumEnergy(measureVacuumEnergy())

print(f"{RELIEF['name']} erreicht")