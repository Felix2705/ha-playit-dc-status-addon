from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

MODE_INTEGRATION = "integration"
MODE_GUI_ONLY = "gui_only"

MODE_OPTIONS = [
    selector.SelectOptionDict(value=MODE_INTEGRATION, label="Integration + Sensoren"),
    selector.SelectOptionDict(value=MODE_GUI_ONLY, label="Nur GUI in der Seitenleiste"),
]


class PlayitStatusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            _LOGGER.info(
                "PlayitStatusConfigFlow submit: url=%s scan_interval=%s mode=%s",
                user_input.get("url"),
                user_input.get("scan_interval"),
                user_input.get("mode"),
            )
            _LOGGER.debug("PlayitStatusConfigFlow created entry data=%s", user_input)
            return self.async_create_entry(
                title="Playit Server Status",
                data={
                    "url": user_input["url"],
                    "scan_interval": user_input["scan_interval"],
                    "mode": user_input["mode"],
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required("url", default=DEFAULT_URL): str,
                vol.Required("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required("mode", default=MODE_INTEGRATION): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=MODE_OPTIONS)
                ),
            }
        )

        _LOGGER.debug(
            "PlayitStatusConfigFlow show_form: url_default=%s scan_interval_default=%s mode_default=%s",
            DEFAULT_URL,
            DEFAULT_SCAN_INTERVAL,
            MODE_INTEGRATION,
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
