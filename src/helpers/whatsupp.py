import requests
from components.components import REQUEST_TIMEOUT_SECONDS, modules


def getMissionChat(contactName):
    # Nach dem Abschluss verschwindet der Chat, dann gibt es None zurueck.
    url = f"{modules['whatsupp']}/content"
    contacts = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS).json()["contacts"]
    if contactName not in contacts:
        return None
    return contacts[contactName]["chats"][0]


def getProgress(chat, playerName):
    for message in chat["messages"]:
        if message["data"]["kind"] == "progress":
            for entry in message["data"]["entries"]:
                if entry["name"] == playerName:
                    return entry["data"]
    return None
