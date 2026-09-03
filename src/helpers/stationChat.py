import json
import threading
import time

import websocket


def connect(station, onPayload):
    field = station["field"]
    state = {"ws": None}
    ready = threading.Event()

    def onOpen(ws):
        state["ws"] = ws
        ready.set()
        print(f"[{station['name']}] connected")

    def onMessage(ws, message):
        try:
            payload = json.loads(message).get(field)
        except json.JSONDecodeError:
            print(f"[{station['name']}] not JSON: {message!r}")
            return
        if payload is None:
            print(f"[{station['name']}] without '{field}': {message!r}")
            return
        print(f"[{station['name']}] <- {payload}")
        onPayload(payload)

    def onError(ws, error):
        print(f"[{station['name']}] {type(error).__name__}: {error}")

    def onClose(ws, code, message):
        state["ws"] = None
        ready.clear()
        print(f"[{station['name']}] getrennt ({code})")

    def loop():
        while True:
            app = websocket.WebSocketApp(
                station["ws"],
                on_open=onOpen,
                on_message=onMessage,
                on_error=onError,
                on_close=onClose,
            )
            app.run_forever()
            time.sleep(2)

    threading.Thread(target=loop, daemon=True).start()
    ready.wait(timeout=15)

    def send(payload, source):
        ws = state["ws"]
        if ws is None:
            print(f"[{station['name']}] not connected, message discarded")
            return
        ws.send(json.dumps({"source": source, field: payload}))
        print(f"[{station['name']}] --> {payload}")

    return send