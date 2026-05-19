Playit DC Status — Supervisor Add-on (skeleton)
==============================================

Dieses Verzeichnis enthält ein einfaches Supervisor Add‑on Skeleton für das Polling der Playit Statusseite.

Wichtig: Dieses Add‑on ist ein Hilfsmittel — es ist nicht nötig, wenn du die Integration per HACS installierst. Es dient als Beispiel, wie man ein Add‑on baut, das periodisch die Status‑URL abfragt und die Ergebnisse im Add‑on‑Log ausgibt.

Installation
------------
1. Füge dieses Repository zu deinem Supervisor Add‑on Store (Supervisor -> Add‑on Store -> Repositories).
2. Das Add‑on erscheint unter dem Namen "Playit DC Status Add-on".
3. Du kannst die Option `status_url` und `interval` in den Add‑on Einstellungen konfigurieren.

Hinweis
------
Das Add‑on schreibt seine Pollergebnisse in das Add‑on‑Log. Wenn du die Daten in Home Assistant als Sensoren nutzen möchtest, ist der HACS‑Weg (Custom Integration) die passendere Lösung.
