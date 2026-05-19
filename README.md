# Playit Server Status — Home Assistant Addon/Integration

Dieses Projekt stellt eine Home Assistant Integration (und optional ein Supervisor Add‑on Skeleton) bereit, die den Status von Playit.gg abfragt und als Sensoren in Home Assistant verfügbar macht.

Kurz:
- Ein `sensor.playit_status_overall` zeigt den Gesamtzustand.
- Pro erkannter Region wird ein `sensor.playit_status_region_<name>` angelegt.

Installation (kurz):
- Empfohlen: Installation über HACS (Add Integration → suche "Playit Server Status" nach Hinzufügen des Custom Repository).
- Manuell: Kopiere `custom_components/playit_status` nach `<config_dir>/custom_components/playit_status` und füge in `configuration.yaml`:

```yaml
playit_status:
  url: "https://dc.status.playit.gg/"
  scan_interval: 60
```

- Optional: Für ein Dashboard siehe die Lovelace‑Snippets im Repo (`lovelace_playit_advanced.yaml`, `lovelace_playit_auto.yaml`).

Supervisor Add‑on:
- Im Ordner `addon/playit_status` befindet sich ein Add‑on‑Skeleton, das die Status‑URL periodisch pollt und die Ergebnisse in die Addon‑Logs schreibt. Nutze dieses Add‑on, wenn du die Überwachung außerhalb der Integration betreiben möchtest.

Fehlersuche:
- Prüfe Home Assistant Logs auf Einträge mit `playit_status`.
- Stelle sicher, dass dein Host Internetzugang hat und die Ziel‑URL erreichbar ist.




