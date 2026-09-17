import json
import threading
import time
import websocket
from components.components import RECONNECT_DELAY_SECONDS

def connectToStation(name, wsUrl, field, onPayload):
    state = {"ws": None}
    ready = threading.Event()

    def onOpen(ws):
        state["ws"] = ws
        ready.set()
        print(f"[{name}] connected")

    def onMessage(ws, message):
        try:
            payload = json.loads(message).get(field)
        except json.JSONDecodeError:
            print(f"[{name}] not JSON: {message!r}")
            return
        if payload is None:
            print(f"[{name}] without '{field}': {message!r}")
            return
        print(f"[{name}] <- {payload}")
        onPayload(payload)

    def onError(ws, error):
        print(f"[{name}] {type(error).__name__}: {error}")

    def onClose(ws, code, message):
        state["ws"] = None
        ready.clear()
        print(f"[{name}] getrennt ({code})")

    def loop():
        while True:
            app = websocket.WebSocketApp(
                wsUrl,
                on_open=onOpen,
                on_message=onMessage,
                on_error=onError,
                on_close=onClose,
            )
            app.run_forever()
            time.sleep(RECONNECT_DELAY_SECONDS)

    threading.Thread(target=loop, daemon=True).start()
    ready.wait(timeout=15)

    def sendToStation(payload, source):
        ws = state["ws"]
        if ws is None:
            print(f"[{name}] not connected, message discarded")
            return
        ws.send(json.dumps({"source": source, field: payload}))
        print(f"[{name}] --> {payload}")

    return sendToStation
