from pymongo import MongoClient
from components.components import MONGO_CONNECTION_STRING

vacuumEnergy = MongoClient(MONGO_CONNECTION_STRING)["theshipdb"]["vacuum-energy"]

def storeVacuumEnergy(hexData):
    vacuumEnergy.replace_one({}, {"data": hexData}, upsert=True)