# The Ship

Steuerung des Schiffs über die REST- und WebSocket-Schnittstellen der Bordkomponenten.

Team: Stutz Michael (VM 192.168.100.50), Eggerschwiler Marvin (VM 192.168.100.51)

## Überblick

- Aufgabe 1 läuft lokal auf dem Laptop.
- Aufgabe 2 läuft auf den VMs, weil dort die Kommunikations-Ports zwischen den Maschinen erreichbar sind.
- Das Projekt nutzt HTTP für Steuerung und Cargo Hold sowie WebSocket-Verbindungen für die Kommunikationsstationen.

## Lokales Setup

Einmalig:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Starten aus dem Projektordner:

```powershell
.\.venv\Scripts\python.exe src\aufgabe1.py
```

> Wichtig: `python -m venv .venv` kann unter Windows den Microsoft-Store-Stub treffen. Dann ist `pip` nicht verfügbar. Nutze den kompletten Pfad zu Python 3.13.

## Aufgabe 1: Eisenhandel

Ziel: Schiff vollbeladen mit Eisen bei Vesta Station andocken.

- Bei Azura Station Eisen kaufen (5 pro Stück)
- Bei Core Station Eisen verkaufen (10 pro Stück)
- Geld verdoppelt sich pro Runde; aus 20 Credits entstehen so in wenigen Runden 12 Eisen
- Danach Kurs auf 7000/7000

Datei: `src/aufgabe1.py`

## Aufgabe 2: Kommunikation zwischen Stationen

Elyse Terminal und Shangris Station sollen miteinander kommunizieren. Das Comm-Modul funktioniert nur in Reichweite der Station; die Stationen liegen etwa 100.000 Einheiten auseinander.

Ziel:
- Nachricht an die Partnerstation senden
- Relay zwischen den VMs verwenden
- mindestens alle 3 Sekunden weiterleiten
- mindestens 20 Sekunden in beide Richtungen laufen lassen

Die eigentliche Hürde ist das unterschiedliche JSON-Feld:
- Elyse erwartet `msg`
- Shangris erwartet `data`

Der Relay selbst kennt nur `from` und `payload` und darf den Inhalt nicht verändern.

## VM-Setup und Start

Auf der VM:

```bash
ssh ship@192.168.100.50
sudo apt update && sudo apt install -y python3-pip python3-venv git
cd ~
git clone <repo-url> theship
cd theship
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Starten auf beiden VMs zur gleichen Zeit:

```bash
cd ~/theship
.venv/bin/python src/aufgabe2Elyse.py
.venv/bin/python src/aufgabe2Shangris.py
```

Die Laufzeit muss sich überlappen. Im Cockpit unter `http://192.168.100.50:2000` sollten die beiden Zähler hochlaufen.

## Struktur

```text
src/
  aufgabe1.py
  aufgabe2Elyse.py
  aufgabe2Shangris.py
  components/
    components.py
  helpers/
    easySteering.py
    relay.py
    stationChat.py
    communication.py
    cargoHold.py
```

## Wichtige Hinweise

- `relay.py` ist die Verbindungsstelle zwischen den beiden VMs.
- `stationChat.py` verbindet das Schiff mit der jeweiligen Station und übersetzt `msg`/`data` an den Endpunkten.
- `easySteering.py` steuert die Anfahrt und das Andocken.
- `components.py` enthält zentrale Konfigurationen wie Ports, Stationen und Partner.
- `DURATION` ist bewusst größer als die Mindestanforderung, damit Startunterschiede keine Probleme verursachen.

## Ports und Adressen

- Easy Steering: 2009
- Communication: 2011
- Cargo Hold: 2012
- Relay: 5000
- Elyse WebSocket: `ws://127.0.0.1:2026/api`
- Shangris WebSocket: `ws://127.0.0.1:2025/ws`

**Das Projekt wird lokal für Aufgabe 1 und auf der VM für Aufgabe 2 verwendet, weil nur dort die fremde VM per TCP erreichbar ist.**
