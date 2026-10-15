import json
import threading
import time
import pika
from components.components import RECONNECT_DELAY_SECONDS

SCANNER_PORT = 2014
EXCHANGE = "scanner/detected_objects"

# Neueste Objektliste vom Scanner. receivedAt ist time.monotonic() beim Empfang.
state = {"objects": [], "receivedAt": None}
lock = threading.Lock()


def receiveObjects(host):
    # pika ist nicht threadsicher: Verbindung nur in diesem Thread erstellen und benutzen.
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=SCANNER_PORT))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
    queue = channel.queue_declare(queue="", exclusive=True).method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue)
    print(f"[scanner] connected to {host}:{SCANNER_PORT}")

    for method, properties, body in channel.consume(queue, auto_ack=True):
        with lock:
            state["objects"] = json.loads(body)
            state["receivedAt"] = time.monotonic()


def scannerLoop(host):
    while True:
        try:
            receiveObjects(host)
        except Exception as error:
            print(f"[scanner] connection to {host}:{SCANNER_PORT} failed: {error!r}")
        time.sleep(RECONNECT_DELAY_SECONDS)


def startScanner(host):
    threading.Thread(target=scannerLoop, args=(host,), daemon=True).start()


def getObject(name):
    with lock:
        objects = state["objects"]
        receivedAt = state["receivedAt"]

    for detectedObject in objects:
        if detectedObject["name"] == name:
            position = detectedObject["pos"]
            return {"x": position["x"], "y": position["y"], "receivedAt": receivedAt}
    return None
