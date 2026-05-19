import json
import os
import threading
import time
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests

BASE_DIR = "/addon"
STATIC_DIR = os.path.join(BASE_DIR, "app")
STATUS_URL = "https://dc.status.playit.gg/"
INTERVAL = 60
STATUS_DATA = {
    "last_update": None,
    "overall": "unknown",
    "regions": {},
    "error": None,
}


def load_options():
    global STATUS_URL, INTERVAL
    options_file = "/data/options.json"
    if os.path.exists(options_file):
        try:
            with open(options_file, "r", encoding="utf-8") as f:
                options = json.load(f)
            STATUS_URL = options.get("status_url", STATUS_URL)
            INTERVAL = int(options.get("interval", INTERVAL))
        except Exception as err:
            print(f"Failed to load options.json: {err}")


def update_status():
    global STATUS_DATA
    try:
        response = requests.get(STATUS_URL, timeout=20)
        response.raise_for_status()
        data = None
        if "application/json" in response.headers.get("Content-Type", ""):
            data = response.json()
        else:
            data = response.text

        regions = {}
        overall = "unknown"
        if isinstance(data, dict):
            if "components" in data and isinstance(data["components"], list):
                for comp in data["components"]:
                    name = comp.get("name") or comp.get("id")
                    status = comp.get("status") or comp.get("indicator") or comp.get("state")
                    if name:
                        regions[name] = status or "unknown"
            if "status" in data:
                if isinstance(data["status"], dict):
                    overall = data["status"].get("description") or data["status"].get("indicator") or overall
                else:
                    overall = data["status"]
        else:
            overall = str(data)[:120]

        STATUS_DATA = {
            "last_update": datetime.utcnow().isoformat() + "Z",
            "overall": overall,
            "regions": regions,
            "error": None,
        }
    except Exception as err:
        STATUS_DATA = {
            "last_update": datetime.utcnow().isoformat() + "Z",
            "overall": "error",
            "regions": {},
            "error": str(err),
        }
        print(f"Status poll failed: {err}")


def poll_loop():
    while True:
        update_status()
        time.sleep(INTERVAL)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(STATUS_DATA).encode("utf-8"))
            return
        return super().do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    load_options()
    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print(f"Starting Playit Status UI on http://0.0.0.0:8080, polling {STATUS_URL} every {INTERVAL}s")
    server.serve_forever()
