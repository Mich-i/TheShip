import json
import threading
import time
import pika
from components.components import RECONNECT_DELAY_SECONDS

SCANNER_PORT = 2014
EXCHANGE = "scanner/detected_objects"
SOCKET_TIMEOUT_SECONDS = 5
SILENCE_WARNING_SECONDS = 5

# Die Liste wird bei jeder Nachricht ersetzt, nie veraendert.
# receivedAt ist time.monotonic() beim Empfang.
state = {"objects": [], "receivedAt": None}
lock = threading.Lock()


def receiveObjects(host, onObjects):
    # pika ist nicht threadsicher: Verbindung nur in diesem Thread erstellen und benutzen.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=SCANNER_PORT,
            socket_timeout=SOCKET_TIMEOUT_SECONDS,
            blocked_connection_timeout=SOCKET_TIMEOUT_SECONDS,
        )
    )
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
        queue = channel.queue_declare(queue="", exclusive=True).method.queue
        channel.queue_bind(exchange=EXCHANGE, queue=queue)
        print(f"[scanner] connected to {host}:{SCANNER_PORT}")

        for method, properties, body in channel.consume(
            queue, auto_ack=True, inactivity_timeout=SILENCE_WARNING_SECONDS
        ):
            if body is None:
                print(f"[scanner] no objects received for {SILENCE_WARNING_SECONDS}s")
                continue
            try:
                objects = json.loads(body)
            except json.JSONDecodeError:
                print(f"[scanner] not JSON: {body!r}")
                continue

            with lock:
                state["objects"] = objects
                state["receivedAt"] = time.monotonic()

            if onObjects is not None:
                onObjects(objects)
    finally:
        if connection.is_open:
            connection.close()


def scannerLoop(host, onObjects):
    while True:
        try:
            receiveObjects(host, onObjects)
        except Exception as error:
            print(f"[scanner] connection to {host}:{SCANNER_PORT} failed: {error!r}")
        time.sleep(RECONNECT_DELAY_SECONDS)


def startScanner(host, onObjects=None):
    threading.Thread(target=scannerLoop, args=(host, onObjects), daemon=True).start()


def getLatestObjects():
    with lock:
        return list(state["objects"])


def getObject(name):
    with lock:
        objects = state["objects"]
        receivedAt = state["receivedAt"]

    for detectedObject in objects:
        if detectedObject["name"] == name:
            position = detectedObject["pos"]
            return {"x": position["x"], "y": position["y"], "receivedAt": receivedAt}
    return None
