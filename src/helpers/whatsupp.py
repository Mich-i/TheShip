import requests
from components.components import REQUEST_TIMEOUT_SECONDS, modules


def getMissionChat(contactName):
    url = f"{modules['whatsupp']}/content"
    content = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS).json()

    contact = content["contacts"].get(contactName)
    if contact is None or not contact["chats"]:
        return None
    return contact["chats"][0]


def getProgressEntries(chat):
    entries = {}
    for message in chat["messages"]:
        if message["data"]["kind"] != "progress":
            continue
        for entry in message["data"]["entries"]:
            entries[entry["name"]] = {"curr": entry["data"]["curr"], "max": entry["data"]["max"], "done": entry["done"]}
    return entries


def describeMessage(message):
    data = message["data"]
    if data["kind"] == "simple":
        return f"{message['sender']}: {data['text']}"
    return f"{message['sender']}: [{data['kind']}]"
