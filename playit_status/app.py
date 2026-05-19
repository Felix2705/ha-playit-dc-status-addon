import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests

BASE_DIR = "/addon"
STATIC_DIR = os.path.join(BASE_DIR, "app")
STATUS_URL = "https://dc.status.playit.gg/"
STATUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PlayitStatus/1.0; +https://github.com/Felix2705/ha-playit-server-status)"
}
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


def extract_api_url(html_text):
    match = re.search(r"window\.pspApiPath\s*=\s*['\"]([^'\"]+)['\"]", html_text)
    if match:
        api_url = match.group(1)
        if api_url.startswith("/"):
            return f"https://dc.status.playit.gg{api_url}"
        return api_url

    # fallback for pages with different JS bootstrap code or inline API URLs
    match = re.search(r"https?://[^'\"]+/api/getMonitorList/[^'\"]+", html_text)
    if match:
        return match.group(0)

    match = re.search(r"['\"](/api/getMonitorList/[^'\"]+)['\"]", html_text)
    if match:
        return f"https://dc.status.playit.gg{match.group(1)}"

    return None


def normalize_status(value):
    if not value:
        return "unknown"
    value = str(value).strip().lower()
    if value in {"ok", "good", "operational", "up", "success", "available"}:
        return "operational"
    if value in {"danger", "down", "error", "outage", "critical", "failed"}:
        return "issue"
    if value in {"warning", "degraded", "partial", "minor"}:
        return "degraded"
    return value


def derive_overall_from_regions(regions):
    if not regions:
        return "unknown"

    statuses = [str(value).lower() for value in regions.values() if value]
    if any("down" in s or "outage" in s or "danger" in s or "error" in s or "degrad" in s or "fail" in s for s in statuses):
        return "issue"
    if all(s in {"operational", "ok", "up", "available"} for s in statuses):
        return "operational"
    return "unknown"


def parse_playit_json(data):
    regions = {}
    overall = "unknown"

    if isinstance(data, dict):
        counts = data.get("statistics", {}).get("counts", {})
        down = int(counts.get("down", 0) or 0)
        up = int(counts.get("up", 0) or 0)
        if down > 0:
            overall = f"{down} down"
        elif up > 0:
            overall = "operational"
        else:
            overall = normalize_status(data.get("status", "unknown"))

        items = []
        if isinstance(data.get("data"), list):
            items = data["data"]
        elif isinstance(data.get("psp", {}).get("monitors"), list):
            items = data["psp"]["monitors"]
        elif isinstance(data.get("components"), list):
            items = data["components"]
        elif isinstance(data.get("monitors"), list):
            items = data["monitors"]

        for item in items:
            name = item.get("name") or item.get("groupName") or str(item.get("monitorId") or item.get("id") or "unknown")
            status = normalize_status(item.get("statusClass") or item.get("label") or item.get("state") or item.get("status") or item.get("indicator"))
            regions[name] = status

        if overall == "unknown":
            overall = derive_overall_from_regions(regions)

    return overall, regions


def update_status():
    global STATUS_DATA
    try:
        response = requests.get(STATUS_URL, headers=STATUS_HEADERS, timeout=20)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        data = None
        if "application/json" in content_type:
            data = response.json()
        else:
            html = response.text
            api_url = extract_api_url(html)
            if api_url:
                response = requests.get(api_url, headers=STATUS_HEADERS, timeout=20)
                response.raise_for_status()
                data = response.json()
            else:
                raise ValueError("Playit status page did not expose a JSON API endpoint")

        overall, regions = parse_playit_json(data)

        STATUS_DATA = {
            "last_update": datetime.now(timezone.utc).isoformat(),
            "overall": overall,
            "regions": regions,
            "error": None,
        }
    except Exception as err:
        STATUS_DATA = {
            "last_update": datetime.now(timezone.utc).isoformat(),
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
