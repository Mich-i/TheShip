import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import requests
from components.components import RELAY_PORT

def startServer(onMessage):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            self.send_response(200)
            self.end_headers()
            try:
                onMessage(json.loads(body))
            except json.JSONDecodeError:
                print(f"[relay] kein JSON: {body!r}")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("0.0.0.0", RELAY_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[relay] listening on port {RELAY_PORT}")

def sendToPeer(peer, source, payload):
    try:
        requests.post(
            f"http://{peer}:{RELAY_PORT}/message",
            json={"from": source, "payload": payload},
            timeout=2,
        )
        print(f"[relay] --> {peer}: {payload}")
    except requests.RequestException as error:
        print(f"[relay] peer connection failed: {error}")