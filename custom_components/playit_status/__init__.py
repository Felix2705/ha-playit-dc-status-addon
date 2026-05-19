from datetime import timedelta
import asyncio
import logging

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
                # Try JSON first
                try:
                    data = await resp.json()
                except Exception:
                    data = None

                if data:
                    return parse_json(data)

                # fallback: simple HTML/text parsing
                return parse_html(text)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout fetching playit status") from err
        except Exception as err:
            raise UpdateFailed(err) from err


def parse_json(data):
    # Handle typical statuspage-like structures
    result = {
        "overall": None,
        "regions": {},
        "raw": data,
    }

    # components array
    if isinstance(data, dict):
        if "components" in data and isinstance(data["components"], list):
            for comp in data["components"]:
                name = comp.get("name") or comp.get("id")
                status = comp.get("status") or comp.get("indicator") or comp.get("state")
                if name:
                    result["regions"][name] = status or "unknown"

        # summary or status
        if "status" in data:
            # status may be dict
            if isinstance(data["status"], dict):
                result["overall"] = data["status"].get("description") or data["status"].get("indicator")
            else:
                result["overall"] = data["status"]

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
