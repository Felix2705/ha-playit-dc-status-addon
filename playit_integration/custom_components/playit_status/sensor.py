import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

STATE_OK = "betriebsbereit"
STATE_ISSUE = "störung"
STATE_DEGRADED = "eingeschränkt"
STATE_UNKNOWN = "unbekannt"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    coordinator = hass.data[DOMAIN]["coordinator"]

    entities = [PlayitOverallSensor(coordinator)]

    data = coordinator.data or {}
    regions = data.get("regions", {}) if isinstance(data, dict) else {}
    for name in regions:
        entities.append(PlayitRegionSensor(coordinator, name))

    async_add_entities(entities, True)


class PlayitBaseSensor(SensorEntity):
    def __init__(self, coordinator, name):
        self.coordinator = coordinator
        self._name = name
        self._attr_extra_state_attributes = {}

    @property
    def should_poll(self):
        return False

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "playit_status")},
            name="Playit Status",
            manufacturer="playit.gg",
        )


class PlayitOverallSensor(PlayitBaseSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "Playit Overall")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "playit_status_overall"

    @property
    def state(self):
        data = self.coordinator.data or {}
        overall = data.get("overall") if isinstance(data, dict) else None
        if overall:
            return overall

        # Fallback (nur deutsch)
        regions = data.get("regions", {}) if isinstance(data, dict) else {}
        if not regions:
            return STATE_UNKNOWN

        values = [str(v).lower() for v in regions.values() if v]
        if any(v == STATE_ISSUE for v in values):
            return STATE_ISSUE
        if any(v == STATE_DEGRADED for v in values):
            return STATE_DEGRADED
        return STATE_OK

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "regions": data.get("regions", {}),
            ATTR_ATTRIBUTION: "Daten von playit status",
        }


class PlayitRegionSensor(PlayitBaseSensor):
    def __init__(self, coordinator, region_name):
        super().__init__(coordinator, region_name)
        self._region = region_name

    @property
    def name(self):
        return f"Playit {self._region}"

    @property
    def unique_id(self):
        slug = re.sub(r"[^a-z0-9]+", "_", self._region.lower()).strip("_")
        return f"playit_status_region_{slug}"

    @property
    def device_info(self) -> DeviceInfo:
        slug = re.sub(r"[^a-z0-9]+", "_", self._region.lower()).strip("_")
        return DeviceInfo(
            identifiers={(DOMAIN, slug)},
            name=f"Playit {self._region}",
            manufacturer="playit.gg",
        )

    @property
    def state(self):
        data = self.coordinator.data or {}
        regions = data.get("regions", {}) if isinstance(data, dict) else {}
        return regions.get(self._region, STATE_UNKNOWN)

    @property
    def extra_state_attributes(self):
        return {ATTR_ATTRIBUTION: "Daten von playit status"}
