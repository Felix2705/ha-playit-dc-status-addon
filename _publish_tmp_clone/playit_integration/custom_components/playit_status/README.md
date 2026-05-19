Playit Server Status
====================

Custom integration to poll a Playit status page and expose an overall sensor plus one sensor per region.

Installation
------------
1. Copy the `playit_status` folder into your Home Assistant `custom_components` directory:

   - `<config_dir>/custom_components/playit_status`

2. Add configuration to `configuration.yaml`:

```yaml
playit_status:
  url: "https://dc.status.playit.gg/"
  scan_interval: 60
```

3. Restart Home Assistant.

Entities
--------
- `sensor.playit_overall` — overall derived state (`operational` / `issue` / or the service-provided overall state)
- `sensor.playit_<region>` — one sensor per region detected on the status page

Notes and troubleshooting
-------------------------
- The integration attempts to parse JSON from the provided URL. If the site blocks programmatic access or only renders via JavaScript, parsing may fail or produce approximate results.
- If sensors are missing, check Home Assistant logs for `playit_status` errors and adjust `url` if necessary.

License
-------
MIT
