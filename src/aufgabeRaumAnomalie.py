from components.components import RELIEF
from helpers.communication import stationsInReach
from helpers.easySteering import setTarget
from helpers.energyManagement import enableComponents
from helpers.vacuumEnergySensor import measureVacuumEnergy
from helpers.vacuumEnergyStore import storeVacuumEnergy

SHIELD_COMPONENTS = ["sensor_void_energy", "shield_generator"]

enableComponents(SHIELD_COMPONENTS)
storeVacuumEnergy(measureVacuumEnergy())

setTarget(RELIEF["coordinates"])
print(f"Setted course on {RELIEF['name']}")

while RELIEF["name"] not in stationsInReach():
    storeVacuumEnergy(measureVacuumEnergy())

print(f"{RELIEF['name']} reached")