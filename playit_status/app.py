import json
import os
import re
import shutil
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests
import sys

BASE_DIR = "/addon"
STATIC_DIR = os.path.join(BASE_DIR, "app")
STATUS_URL = "https://dc.status.playit.gg/"
STATUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PlayitStatus/1.0; +https://github.com/Felix2705/ha-playit-server-status)"
}
INTERVAL = 60
STATUS_DATA = {
    "last_update": None,
    "overall": "unbekannt",
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
        return "unbekannt"
    value = str(value).strip().lower()
    if value in {"ok", "good", "operational", "up", "success", "available"}:
        return "betriebsbereit"
    if value in {"danger", "down", "error", "outage", "critical", "failed", "issue"}:
        return "störung"
    if value in {"warning", "degraded", "partial", "minor"}:
        return "eingeschränkt"
    return "unbekannt"


def derive_overall_from_regions(regions):
    if not regions:
        return "unbekannt"

    statuses = [str(value).lower() for value in regions.values() if value]
    if any(
        "down" in s
        or "outage" in s
        or "danger" in s
        or "error" in s
        or "degrad" in s
        or "fail" in s
        or "störung" in s
        or "eingeschränkt" in s
        for s in statuses
    ):
        return "störung"
    if all(s in {"betriebsbereit", "ok", "up", "available", "good", "success"} for s in statuses):
        return "betriebsbereit"
    if any("warning" in s or "partial" in s or "minor" in s for s in statuses):
        return "eingeschränkt"
    return "unbekannt"


def parse_playit_json(data):
    regions = {}
    overall = "unbekannt"

    if isinstance(data, dict):
        counts = data.get("statistics", {}).get("counts", {})
        down = int(counts.get("down", 0) or 0)
        up = int(counts.get("up", 0) or 0)
        if down > 0:
            overall = f"{down} Störung"
        elif up > 0:
            overall = "betriebsbereit"
        else:
            overall = normalize_status(data.get("status", "unbekannt"))

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

        if overall == "unbekannt":
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
            "overall": "fehler",
            "regions": {},
            "error": str(err),
        }
        print(f"Statusabfrage fehlgeschlagen: {err}")


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


def copy_integration_into_ha():
    """
    Kopiert die Custom-Integration aus dem Container-Image nach:
    /config/custom_components/playit_status

    Ziel: In HA unter Einstellungen -> Geräte & Dienste -> Integration sichtbar machen.
    """
    src = "/addon/custom_components_src/playit_status"
    dst = "/config/custom_components/playit_status"
    cfg_cc_root = "/config/custom_components"

    def log(msg: str) -> None:
        print(f"[PlayitStatus] {msg}", file=sys.stderr, flush=True)

    log(f"copy_integration_into_ha(): src={src} dst={dst}")

    # Diagnose: Verzeichnis-Existenz
    if not os.path.exists(src):
        log(f"Integration-Quelle NICHT gefunden: {src}")
        try:
            log(f"/addon exists: {os.path.exists('/addon')}")
            log(f"/addon contents: {os.listdir('/addon')}")
        except Exception as err:
            log(f"konntes /addon nicht lesen: {err}")
        raise FileNotFoundError(src)

    try:
        log(f"/config exists: {os.path.exists('/config')}")
        log(f"/config/custom_components exists: {os.path.exists(cfg_cc_root)}")
        log(f"src contents: {os.listdir(src)}")

        os.makedirs(cfg_cc_root, exist_ok=True)

        # Python 3.12: dirs_exist_ok=True erlaubt Overwrite/Update
        shutil.copytree(src, dst, dirs_exist_ok=True)

        # Verifikation nach dem Kopieren
        if not os.path.exists(dst):
            raise FileNotFoundError(dst)

        manifest = os.path.join(dst, "manifest.json")
        if not os.path.exists(manifest):
            raise FileNotFoundError(manifest)

        log(f"Integration nach HA kopiert: {dst}")
        log(f"dst contents: {os.listdir(dst)}")
        log(f"manifest.json ok: {manifest}")
    except Exception as err:
        log(f"Integration-Kopie fehlgeschlagen: {err}")
        raise


if __name__ == "__main__":
    # Erst Integration bereitstellen, dann normal starten
    copy_integration_into_ha()
    load_options()
    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print(f"Starte Playit-Statusoberfläche auf http://0.0.0.0:8080, Abfrage von {STATUS_URL} alle {INTERVAL}s")
    server.serve_forever()
