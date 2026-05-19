Playit Server Status
=====================

Custom integration to poll a Playit status page and expose an overall sensor plus one sensor per region.

Installation
------------

1. Start first the **Supervisor Add-on** `Playit DC Status`.
2. Then in Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen**
3. Search for **„Playit Server Status“** and add it.
4. URL/Scan-Interval kannst du im Dialog setzen (Standard: `https://dc.status.playit.gg/`, `60s`).

Entities
--------

- `sensor.playit_overall` — overall derived state (`betriebsbereit` / `störung` / `eingeschränkt`)
- `sensor.playit_<region>` — one sensor per region detected on the status page

Notes and troubleshooting
-------------------------

- The integration attempts to parse JSON from the provided URL. If the site blocks programmatic access or only renders via JavaScript, parsing may fail or produce approximate results.
- If sensors are missing, check Home Assistant logs for `playit_status` errors and adjust `url` if necessary.

License
-------

MIT
