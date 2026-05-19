from datetime import timedelta
import asyncio
import logging
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_URL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PlayitCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, url: str, interval: int):
        self.hass = hass
        self.url = url
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(self.url, timeout=20) as resp:
                text = await resp.text()
                data = None

                try:
                    data = await resp.json()
                except Exception:
                    data = None

                if data:
                    parsed = parse_json(data)
                    if parsed["regions"]:
                        return parsed

                api_url = extract_api_url(text)
                if api_url:
                    async with session.get(api_url, timeout=20) as api_resp:
                        api_data = await api_resp.json()
                        return parse_json(api_data)

                return parse_html(text)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout fetching playit status") from err
        except Exception as err:
            raise UpdateFailed(err) from err


def extract_api_url(html_text: str):
    match = re.search(r"window\.pspApiPath\s*=\s*['\"]([^'\"]+)['\"]", html_text)
    if match:
        return match.group(1)

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
    statuses = [str(v).lower() for v in regions.values() if v]
    if any("down" in s or "outage" in s or "danger" in s or "error" in s or "degrad" in s or "fail" in s for s in statuses):
        return "issue"
    if all(s in {"operational", "ok", "up", "available"} for s in statuses):
        return "operational"
    return "unknown"


def parse_json(data):
    result = {
        "overall": None,
        "regions": {},
        "raw": data,
    }

    if isinstance(data, dict):
        if "status" in data and not isinstance(data["status"], dict):
            result["overall"] = normalize_status(data["status"])

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
            result["regions"][name] = status

        if not result["overall"]:
            result["overall"] = derive_overall_from_regions(result["regions"])

    return result


def parse_html(text: str):
    # naive parsing: find lines with common status words and preceding headings
    result = {"overall": None, "regions": {}, "raw": text}
    lines = text.splitlines()
    keywords = ["Operational", "operational", "Degraded", "degraded", "Major", "Outage", "maintenance"]
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                # try to get a nearby heading for a name
                name = None
                # look backwards for a tag with text
                for j in range(max(0, i-3), i+1):
                    l = lines[j].strip()
                    if l and not any(x in l for x in ["<svg", "cookie", "button"]):
                        # strip tags
                        import re

                        name = re.sub(r"<[^>]+>", "", l).strip()
                        break
                if not name:
                    name = f"line_{i}"
                result["regions"][name] = line.strip()

    return result


async def async_setup(hass: HomeAssistant, config: dict):
    conf = config.get(DOMAIN, {})
    url = conf.get("url", DEFAULT_URL)
    interval = conf.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coordinator = PlayitCoordinator(hass, url, interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})["coordinator"] = coordinator

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    return True
