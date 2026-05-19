<<<<<<< HEAD
# ha-playit-dc-status-addon
Dieses Addon für Home Assistent zeigt den Aktuellen Playit.gg Server Status der einzelnen reginen und wenn es Allgemein eine Störung gibt 
=======
Playit Server Status — Home Assistant Custom Integration
=========================================================

Kurz: Dieses Repository enthält eine Home Assistant Custom Integration, die die Statusseite von playit.gg abfragt und einen Gesamtstatus sowie einzelne Regionensensoren bereitstellt.

Inhalt
------
- `custom_components/playit_status/` — die Integration (Manifest, `__init__.py`, `sensor.py`, README)

Schnellinstallation
-------------------
1. Repository klonen oder die Ordnerstruktur in dein Home Assistant Config‑Ordner kopieren.

```bash
git clone <DEIN_REPO_URL>
# oder kopieren:
# copy custom_components/playit_status nach <config_dir>/custom_components/playit_status
```

2. Konfiguration zu `configuration.yaml` hinzufügen:

```yaml
playit_status:
  url: "https://dc.status.playit.gg/"
  scan_interval: 60
```

3. Home Assistant neu starten.

Erzeugte Entitäten
------------------
- `sensor.playit_status_overall` — Gesamtzustand (`operational` / `issue` oder vom Dienst gelieferte Beschreibung)
- `sensor.playit_status_region_<name>` — ein Sensor pro erkannter Region (Name basiert auf der Seite)

Beispiel: Wenn eine Region "DC West" heißt, erscheint `sensor.playit_status_region_DC West`.

Fehlersuche
-----------
- Prüfe die Home Assistant Logs auf Fehler mit dem Schlüssel `playit_status`.
- Manche Statusseiten rendern Inhalte via JavaScript; in diesem Fall kann die Integration nur eingeschränkte Informationen erhalten. Als Alternative kannst du einen externen Dienst nutzen, der die Seite rendert.

Upload zu GitHub
----------------
1. Im lokalen Repo initialisieren (falls noch nicht geschehen):

```bash
git init
git add .
git commit -m "Initial commit: Playit Server Status integration"
```

2. Remote hinzufügen und pushen:

```bash
git remote add origin https://github.com/<username>/<repo>.git
git branch -M main
git push -u origin main
```

Vorgeschlagene Repositorybeschreibung (Kurz):
"Home Assistant integration to poll Playit.gg server status and expose overall + per-region sensors."

Lizenz
------
Dieses Projekt ist unter der MIT‑Lizenz lizenziert (siehe LICENSE Datei).

Weiteres
-------
- Internes README der Integration: `custom_components/playit_status/README.md`
- Wenn du möchtest, erstelle ich eine `config_flow` für die Integration, damit sie per UI konfigurierbar ist.

Lovelace UI (Sidebar) & Refresh
--------------------------------
Um eine Sidebar‑Seite mit aktuellem Zeitpunkt und einem Refresh‑Button anzulegen, gibt es zwei einfache Schritte:

1. Lovelace View hinzufügen

  - Öffne Lovelace Raw Config Editor (Einstellungen → Steuerung → Drei Punkte → Rohkonfiguration bearbeiten) und füge den Inhalt von `lovelace_playit_view.yaml` in deine `views:`-Liste ein. Die View hat `navigation: true` und erscheint in der linken Seitenleiste.

2. Script zum manuellen Refresh

  - Füge `playit_scripts.yaml` zu deiner Konfiguration hinzu oder kopiere den Inhalt in deine `scripts.yaml`.
  - Falls du die Datei separat nutzt, binde sie in `configuration.yaml` ein:

```yaml
script: !include playit_scripts.yaml
```

Zusätzlich brauchst du das `sensor.time`/`time and date` Integration, damit die aktuelle Uhrzeit als `sensor.time` angezeigt wird.

Dateien im Repo:
- `lovelace_playit_view.yaml` — Lovelace view snippet
- `playit_scripts.yaml` — Beispielscript zum Auslösen von `homeassistant.update_entity`

- `lovelace_playit_advanced.yaml` — erweiterte Ansicht mit `button-card` Vorlagen (siehe Hinweise)
- `template_sensors.yaml` — Template sensor für letzte Aktualisierung

Custom cards / Ressourcen
-------------------------
Die erweiterte Ansicht nutzt `custom:button-card` für das tabellarische Layout. Installiere es per HACS oder manuell und füge die Ressource hinzu:

1. HACS → Frontend → Suche `button-card` → installieren.
2. Alternativ manuell: Resources → URL: `/hacsfiles/button-card/button-card.js`, Typ: `module`.

Konfigurationseinbindung
-----------------------
- Füge `template_sensors.yaml` zu deiner `configuration.yaml` ein:

```yaml
sensor: !include template_sensors.yaml
```

- Füge `lovelace_playit_advanced.yaml` über den Raw Config Editor in deine `views:` ein oder lade die Datei direkt in `ui-lovelace.yaml`.
# ha-playit-dc-status-addon

Dieses Addon / Integration für Home Assistant zeigt den aktuellen Playit.gg Server-Status: einen Gesamtzustand sowie einzelne Regionsensoren. Es enthält eine Custom Integration und mehrere Lovelace-Snippets für ein Dashboard.

Inhalt
------
- `custom_components/playit_status/` — die Integration (Manifest, `__init__.py`, `sensor.py`, README)
- Lovelace Views & Templates: `lovelace_playit_view.yaml`, `lovelace_playit_advanced.yaml`, `lovelace_playit_auto.yaml`, `lovelace_templates.yaml`
- Beispieldateien: `playit_scripts.yaml`, `template_sensors.yaml`, `config_example.yaml`

Schnellinstallation
-------------------
1. Repository klonen oder die Ordnerstruktur in dein Home Assistant Config‑Ordner kopieren.

```bash
git clone https://github.com/Felix2705/ha-playit-dc-status-addon
# oder kopieren:
# copy custom_components/playit_status nach <config_dir>/custom_components/playit_status
```

2. Konfiguration zu `configuration.yaml` hinzufügen:

```yaml
playit_status:
  url: "https://dc.status.playit.gg/"
  scan_interval: 60
```

3. Optional: Template‑Sensor und Scripts einbinden (siehe unten).

4. Home Assistant neu starten.

Erzeugte Entitäten
------------------
- `sensor.playit_status_overall` — Gesamtzustand (`operational` / `issue` oder vom Dienst gelieferte Beschreibung)
- `sensor.playit_status_region_<name>` — ein Sensor pro erkannter Region (Name basiert auf der Seite)

Fehlersuche
-----------
- Prüfe die Home Assistant Logs auf Fehler mit dem Schlüssel `playit_status`.
- Manche Statusseiten rendern Inhalte via JavaScript; in diesem Fall kann die Integration nur eingeschränkte Informationen erhalten. Als Alternative kannst du einen externen Dienst nutzen, der die Seite rendert.

Lovelace UI (Sidebar) & Refresh
------------------------------
Um eine Sidebar‑Seite mit aktuellem Zeitpunkt und einem Refresh‑Button anzulegen, gibt es zwei Schritte:

1. Lovelace View hinzufügen

  - Öffne Lovelace Raw Config Editor und füge den Inhalt von `lovelace_playit_view.yaml` oder `lovelace_playit_advanced.yaml` in deine `views:`-Liste ein.

2. Script zum manuellen Refresh

  - Füge `playit_scripts.yaml` zu deiner Konfiguration hinzu oder kopiere den Inhalt in deine `scripts.yaml`.
  - Falls du die Datei separat nutzt, binde sie in `configuration.yaml` ein:

```yaml
script: !include playit_scripts.yaml
```

Zusätzlich brauchst du das `sensor.time`/`time and date` Integration, damit die aktuelle Uhrzeit als `sensor.time` angezeigt wird.

Weitere Dateien
---------------
- `lovelace_templates.yaml` — Vorlagen für `button-card` (füge die Templates in Lovelace Raw Config unter `button_card_templates:` ein)
- `lovelace_playit_auto.yaml` — automatische View mit `auto-entities`, listet alle `sensor.playit_status_region_*` automatisch

Custom cards / Ressourcen
-------------------------
Die erweiterte Ansicht nutzt `custom:button-card` und `custom:auto-entities`.

Installiere sie per HACS oder manuell und füge die Ressourcen hinzu:

Resources:
- `/hacsfiles/button-card/button-card.js` (Type: module)
- `/hacsfiles/lovelace-auto-entities/auto-entities.js` (Type: module)

Konfigurationseinbindung
-----------------------
- Füge `template_sensors.yaml` zu deiner `configuration.yaml` ein:

```yaml
sensor: !include template_sensors.yaml
```

- Füge `lovelace_playit_advanced.yaml` oder `lovelace_playit_auto.yaml` über den Raw Config Editor in deine `views:` ein oder lade die Datei direkt in `ui-lovelace.yaml`.

Git & Upload
------------
Wenn du möchtest, führe ich den lokalen Commit und Push aus. Du hast bereits das Repo angegeben; ich kann nun pushen, falls deine lokale Umgebung GitHub‑Zugang hat (SSH key oder gespeicherte HTTPS‑Credentials).

Danke — sag mir, ob ich das Repo noch mit Tags, einer Release‑Vorlage oder einer `CHANGELOG.md` erweitern soll.
