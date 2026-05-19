from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_URL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

MODE_INTEGRATION = "integration"
MODE_GUI_ONLY = "gui_only"


def load_mode_from_addon() -> str:
    """
    Mode wird ausschließlich vom Supervisor-Add-on gesteuert:
    /config/playit_status/mode.json

    Ziel: Keine Mode-Auswahl mehr im HA-Integrationsdialog.
    """
    mode_file = "/config/playit_status/mode.json"
    try:
        with open(mode_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        mode = (payload or {}).get("mode")
        if mode in {MODE_INTEGRATION, MODE_GUI_ONLY}:
            return mode
    except Exception:
        pass
    return MODE_INTEGRATION


class PlayitCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, url: str, interval: int):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.url = url

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)

        _LOGGER.debug("PlayitCoordinator: Update startet. url=%s", self.url)

        try:
            # 1) Versuche direkt JSON (falls /status oder API-Endpunkt)
            async with session.get(self.url, timeout=20) as resp:
                text = await resp.text()

                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = None

                if isinstance(data, dict):
                    parsed = parse_json(data)
                    if parsed.get("regions") or parsed.get("overall"):
                        _LOGGER.debug(
                            "PlayitCoordinator: Direct-JSON ok. overall=%s regions=%d",
                            parsed.get("overall"),
                            len(parsed.get("regions") or {}),
                        )
                        return parsed

                # 2) Optional: falls URL die Add-on-Base ist, versuche /status daneben
                status_url = build_status_url(self.url)
                if status_url != self.url:
                    try:
                        async with session.get(status_url, timeout=20) as status_resp:
                            status_data = await status_resp.json(content_type=None)
                            if isinstance(status_data, dict):
                                parsed = parse_json(status_data)
                                if parsed.get("regions") or parsed.get("overall"):
                                    return parsed
                    except Exception:
                        pass

                # 3) Fallback: Public status page scrape
                api_url = extract_api_url(text)
                if api_url:
                    async with session.get(api_url, timeout=20) as api_resp:
                        api_data = await api_resp.json(content_type=None)
                        return parse_json(api_data)

                _LOGGER.debug("PlayitCoordinator: Fallback parse_html. url=%s text_len=%d", self.url, len(text or ""))
                return parse_html(text)

        except asyncio.TimeoutError as err:
            _LOGGER.exception("PlayitCoordinator: Timeout beim Abfragen. url=%s", self.url)
            raise UpdateFailed("Timeout fetching playit status") from err
        except Exception as err:
            _LOGGER.exception("PlayitCoordinator: Update fehlgeschlagen. url=%s err=%s", self.url, err)
            raise UpdateFailed(err) from err


def build_status_url(base_url: str) -> str:
    """
    Wenn base_url eine Add-on-Base ist, dann ist /status darunter.
    (Falls base_url schon /status ist, wird es nicht verändert.)
    """
    parsed = urlsplit(base_url)
    path = parsed.path.rstrip("/")

    if path.endswith("/status"):
        return base_url

    if path:
        new_path = f"{path}/status"
    else:
        new_path = "/status"

    return urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment))


def extract_api_url(html_text: str) -> str | None:
    match = re.search(r"window\.pspApiPath\s*=\s*['\"]([^'\"]+)['\"]", html_text)
    if match:
        api_url = match.group(1)
        if api_url.startswith("/"):
            return f"https://dc.status.playit.gg{api_url}"
        return api_url

    match = re.search(r"https?://[^'\"]+/api/getMonitorList/[^'\"]+", html_text)
    if match:
        return match.group(0)

    match = re.search(r"['\"](/api/getMonitorList/[^'\"]+)['\"]", html_text)
    if match:
        return f"https://dc.status.playit.gg{match.group(1)}"

    return None


def normalize_status(value) -> str:
    """
    Gibt ausschließlich DE-States zurück:
    - betriebsbereit
    - störung
    - eingeschränkt
    - unbekannt
    """
    if not value:
        return "unbekannt"

    s = str(value).strip().lower()

    # Deutsch (vom Add-on)
    if s in {"betriebsbereit", "störung", "eingeschränkt", "unbekannt"}:
        return s

    # Englisch (vom Public API)
    if s in {"ok", "good", "operational", "up", "success", "available"}:
        return "betriebsbereit"
    if s in {"danger", "down", "error", "outage", "critical", "failed", "issue"}:
        return "störung"
    if s in {"warning", "degraded", "partial", "minor"}:
        return "eingeschränkt"

    # Heuristik: Wortfragmente
    if any(x in s for x in ["down", "outage", "danger", "error", "critical", "failed", "issue"]):
        return "störung"
    if any(x in s for x in ["warning", "degrad", "partial", "minor"]):
        return "eingeschränkt"
    if any(x in s for x in ["operational", "ok", "up", "available", "success", "good"]):
        return "betriebsbereit"

    return "unbekannt"


def derive_overall_from_regions(regions: dict[str, str]) -> str:
    if not regions:
        return "unbekannt"

    statuses = [normalize_status(v) for v in regions.values()]

    if any(s == "störung" for s in statuses):
        return "störung"
    if all(s == "betriebsbereit" for s in statuses):
        return "betriebsbereit"
    if any(s == "eingeschränkt" for s in statuses):
        return "eingeschränkt"
    return "unbekannt"


def parse_json(data) -> dict:
    result = {"overall": None, "regions": {}, "raw": data}

    if not isinstance(data, dict):
        return result

    if "overall" in data:
        result["overall"] = normalize_status(data.get("overall"))

    if isinstance(data.get("regions"), dict):
        result["regions"] = {str(k): normalize_status(v) for k, v in data["regions"].items()}

    # Falls es doch die Public API ist (ohne overall/regions Mapping)
    if not result["regions"]:
        # optional: status Gesamtwert (wenn vorhanden)
        if "status" in data and not isinstance(data["status"], dict):
            result["overall"] = normalize_status(data.get("status"))

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
            if not isinstance(item, dict):
                continue
            name = (
                item.get("name")
                or item.get("groupName")
                or str(item.get("monitorId") or item.get("id") or "unknown")
            )
            status = normalize_status(
                item.get("statusClass")
                or item.get("label")
                or item.get("state")
                or item.get("status")
                or item.get("indicator")
            )
            result["regions"][name] = status

    # Gesamt ableiten, wenn nicht vorhanden oder unbekannt
    if not result.get("overall"):
        result["overall"] = derive_overall_from_regions(result.get("regions", {}))

    return result


def parse_html(text: str) -> dict:
    # Sehr grober Fallback – sollte selten gebraucht werden
    result = {"overall": None, "regions": {}, "raw": text}
    lines = text.splitlines()

    keywords = ["Operational", "operational", "Degraded", "degraded", "Major", "Outage", "maintenance", "warning"]

    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                name = f"line_{i}"
                for j in range(max(0, i - 3), i + 1):
                    l = lines[j].strip()
                    if l and not any(x in l for x in ["<svg", "cookie", "button"]):
                        name = re.sub(r"<[^>]+>", "", l).strip() or name
                        break
                result["regions"][name] = normalize_status(line.strip())

    result["overall"] = derive_overall_from_regions(result["regions"])
    return result


async def _setup_coordinator_and_maybe_sensors(
    hass: HomeAssistant, url: str, interval: int, mode: str
) -> bool:
    # Im GUI-only Modus: keine Sensoren, kein Polling (Add-on GUI nutzen)
    if mode != MODE_INTEGRATION:
        return True

    coordinator = PlayitCoordinator(hass, url, interval)
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})["coordinator"] = coordinator
    hass.data[DOMAIN]["mode"] = mode

    # Legacy Platform Loading (sensor.py liest nur coordinator aus hass.data)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, {})

    return True


# Config-Entry Setup (wichtig, damit HA die Integration korrekt anbietet und auswählbar wird)
async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    url = entry.data.get("url", DEFAULT_URL)
    interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    # Mode kommt ausschließlich aus dem Supervisor-Add-on
    mode = load_mode_from_addon()

    return await _setup_coordinator_and_maybe_sensors(hass, url, interval, mode)


# Legacy YAML Support (falls jemand es noch so nutzt)
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    conf = config.get(DOMAIN, {})
    url = conf.get("url", DEFAULT_URL)
    interval = conf.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    # Mode kommt ausschließlich aus dem Supervisor-Add-on
    mode = load_mode_from_addon()

    return await _setup_coordinator_and_maybe_sensors(hass, url, interval, mode)
