# Playit Server Status

Dieses Repository enthält zwei Komponenten:

- `playit_status/` — ein Home Assistant Supervisor Add-on mit Ingress-Weboberfläche.
- `playit_integration/` — eine Custom Integration mit `custom_components/playit_status`.

Nutze das Add-on, wenn du die Statusüberwachung in Supervisor betreiben möchtest, oder die Integration für direkte Sensoren in Home Assistant.

## Ordnerstruktur

- `README.md`
- `repository.yaml`
- `playit_status/`
- `playit_integration/`

## Hinweise

- Die Add-on-Struktur ist jetzt wie beim MAP2MQTT-Repo aufgesetzt, sodass der Supervisor das Repository als Add-on-Repository erkennen kann.
- Für die Integration nutze den Ordner `playit_integration/`.




