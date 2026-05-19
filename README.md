# Playit Server Status

Dieses Repository enthält zwei Komponenten:

- `playit_status/` — ein Home Assistant Supervisor Add-on mit Ingress-Weboberfläche.
- `playit_integration/` — eine Custom Integration mit `custom_components/playit_status`.

Nutze das Add-on für Supervisor-basierte Installationen oder die Integration für direkte Sensoren in Home Assistant.

## Version

- Add-on: `0.1.9-Beta`
- Integration: `0.1.9-Beta`

## Installation

### Supervisor Add-on

1. Füge dieses Repository als Add-on-Repository hinzu.
2. Installiere das Add-on `Playit DC Status`.
3. Konfiguriere bei Bedarf:
   - `status_url`: `https://dc.status.playit.gg/`
   - `interval`: Aktualisierungsintervall in Sekunden
4. Starte das Add-on und öffne die Ingress-UI.

### Integration in Home Assistant hinzufügen (ohne YAML)

1. Starte zuerst das **Supervisor Add-on**.
2. Danach in Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
3. Suche nach **„Playit Server Status“** und füge die Integration hinzu.
4. URL/Scan-Interval kannst du im Dialog setzen (Standard: `https://dc.status.playit.gg/`, `60s`).

Hinweis: Die Suche funktioniert zuverlässig nach einem Neustart/Reload von Home Assistant.

## Nutzung

- Der Add-on bietet eine Weboberfläche mit dem aktuellen Gesamtstatus und allen Playit-Regionen.
- Die Integration erstellt Sensoren wie:
  - `sensor.playit_status_overall`
  - `sensor.playit_status_region_<RegionName>`

## Funktionsweise

- Der Add-on liest die Playit-Webseite unter `https://dc.status.playit.gg/` aus.
- Er extrahiert die eingebaute API-URL von der Seite und holt die Monitor-Daten.
- So wird der aktuelle Status der einzelnen Standorte zuverlässig erfasst.

## Ordnerstruktur

- `README.md`
- `repository.yaml`
- `playit_status/`
- `playit_integration/`

## Hinweise

- Für die Integration verwende den Ordner `playit_integration/`.
- Bei Problemen prüfe die Add-on-Logs und die Home Assistant-Protokolle.
