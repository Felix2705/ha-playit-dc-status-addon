from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

MODE_INTEGRATION = "integration"
MODE_GUI_ONLY = "gui_only"

MODE_OPTIONS = {
    MODE_INTEGRATION: "Integration + Sensoren",
    MODE_GUI_ONLY: "Nur GUI in der Seitenleiste",
}


class PlayitStatusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Playit Server Status",
                data={
                    "url": user_input["url"],
                    "scan_interval": user_input["scan_interval"],
                    "mode": user_input["mode"],
                },
            )

        schema = vol.Schema(
            {
                vol.Required("url", default=DEFAULT_URL): str,
                vol.Required("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required("mode", default=MODE_INTEGRATION): vol.In(list(MODE_OPTIONS.keys())),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
