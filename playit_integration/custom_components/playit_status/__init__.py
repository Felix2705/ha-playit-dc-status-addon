from datetime import timedelta
import asyncio
import logging
import re
from urllib.parse import urlsplit, urlunsplit

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

                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = None

                if isinstance(data, dict):
                    parsed = parse_json(data)
                    if parsed["overall"] != "unknown" or parsed["regions"] or "overall" in data:
                        return parsed

                status_url = build_status_url(self.url)
                if status_url != self.url:
                    try:
                        async with session.get(status_url, timeout=20) as status_resp:
                            status_data = await status_resp.json(content_type=None)
                            if isinstance(status_data, dict):
                                parsed = parse_json(status_data)
                                if parsed["overall"] != "unknown" or parsed["regions"] or "overall" in status_data:
                                    return parsed
                    except Exception:
                        pass

                api_url = extract_api_url(text)
                if api_url:
                    async with session.get(api_url, timeout=20) as api_resp:
                        api_data = await api_resp.json(content_type=None)
                        return parse_json(api_data)

                return parse_html(text)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout fetching playit status") from err
        except Exception as err:
            raise UpdateFailed(err) from err


def build_status_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    path = parsed.path.rstrip("/")

    if path.endswith("/status"):
        return base_url

    if path:
        new_path = f"{path}/status"
    else:
        new_path = "/status"

    return urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment))


def extract_api_url(html_text: str):
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
    if any(
        "down" in s
        or "outage" in s
        or "danger" in s
        or "error" in s
        or "degrad" in s
        or "fail" in s
        for s in statuses
    ):
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

    if not isinstance(data, dict):
        return result

    if "overall" in data:
        result["overall"] = normalize_status(data.get("overall"))

    if isinstance(data.get("regions"), dict):
        result["regions"] = {
            str(name): normalize_status(status)
            for name, status in data["regions"].items()
        }

    if not result["regions"]:
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
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("groupName") or str(
                item.get("monitorId") or item.get("id") or "unknown"
            )
            status = normalize_status(
                item.get("statusClass")
                or item.get("label")
                or item.get("state")
                or item.get("status")
                or item.get("indicator")
            )
            result["regions"][name] = status

    if not result["overall"]:
        result["overall"] = derive_overall_from_regions(result["regions"])

    return result


def parse_html(text: str):
    result = {"overall": None, "regions": {}, "raw": text}
    lines = text.splitlines()
    keywords = ["Operational", "operational", "Degraded", "degraded", "Major", "Outage", "maintenance"]

    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                name = None
                for j in range(max(0, i - 3), i + 1):
                    l = lines[j].strip()
                    if l and not any(x in l for x in ["<svg", "cookie", "button"]):
                        name = re.sub(r"<[^>]+>", "", l).strip()
                        break
                if not name:
                    name = f"line_{i}"
                result["regions"][name] = line.strip()

    if result["regions"]:
        result["overall"] = derive_overall_from_regions(result["regions"])

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
