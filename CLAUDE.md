# CLAUDE.md – TheShip

@README.md

## Worum es geht

TheShip ist ein Schulprojekt (verteilte Systeme) in Form eines Spiels. Jedes Team steuert
Raumschiffe, die als VMs laufen. Jede VM hat mehrere Bordkomponenten (Steuerung, Frachtraum,
Kommunikation usw.), die man über HTTP-REST und WebSockets anspricht. Pro Aufgabe gibt es eine
Mission, die man durch Skripte löst, die diese Schnittstellen aufrufen: Handeln, Navigieren,
Nachrichten zwischen Stationen weiterleiten usw.

Team: Michael Stutz (VM 192.168.100.50) und Marvin Eggerschwiler (VM 192.168.100.51).
Zugang über WireGuard-VPN, dann `ssh ship@<ip>`. Web-Cockpit: `http://<ip>:2000`,
Doku pro Komponente: `http://<ip>:2000/doc/<ComponentName>/0`.

## Stand der Aufgaben

- **Aufgabe 1 (Einleitung)** – gelöst. Eisen bei Azura Station kaufen, bei Core Station
  verkaufen, bis der Frachtraum voll ist (12/12), dann zu Vesta Station (7000/7000) fliegen.
- **Aufgabe 2 (Kommunikation)** – gelöst. Je ein Schiff parkt bei Elyse Terminal
  (-70565/72811) und Shangris Station (4446/4340). Ein Skript pro VM verbindet sich per
  WebSocket mit dem lokalen Kommunikationsmodul und leitet Nachrichten per HTTP (Port 5000,
  `ThreadingHTTPServer`) an die Partner-VM weiter.
- **Aufgabe 3 (Anomalie)** – funktional gelöst, **muss noch refactored werden**.
  <!-- TODO: hier kurz ergänzen: Ziel der Mission, beteiligte Komponenten/Ports, Dateiname(n) -->

## Bordkomponenten (Ports)

| Komponente | Port | Zweck |
|---|---|---|
| cockpit_frontend | 2000 | Web-UI |
| cockpit_backend | 2001, 2002, 2060 | zentraler Spielzustand |
| thruster | 2003–2008 | einzelne Triebwerke |
| easy_steering | 2009 | `POST /set_target` (Stationsname, `{"x","y"}`, `"stop"`, `"idle"`) |
| navigation | 2010 | Position |
| communication | 2011 | `GET /pos`, `GET /stations_in_reach`, `POST /buy`, `POST /sell` |
| cargo_hold | 2012 | `GET /hold` (Credits, Ressourcen, hold_free) |
| whatsupp | 2040 | Missionstext/Chat |

## Projektstruktur

```
src/
  components/components.py   IP + Basis-URLs der Komponenten (IP = "127.0.0.1", läuft auf der VM)
  helpers/                   cargo_hold.py, communication.py, easy_steering.py, station_chat.py
  aufgabe1.py
  aufgabe2Elyse.py
  aufgabe2Shangris.py
  (Aufgabe 3 ...)
requirements.txt             requests, websocket-client
```

Start aus dem Projektordner: `python src/<skript>.py` (kein `cd src` nötig).

## Code-Stil (verbindlich)

- Flache, lineare Skripte von oben nach unten, **keine `main()`-Funktion**. Stil wie `aufgabe1.py`.
- Einfachheit und Lesbarkeit vor cleveren Abstraktionen. Keine unnötigen Klassen oder Schichten.
- Wiederverwendbares gehört in `src/helpers/`, Konstanten (Koordinaten, Ports, Namen) oben im Skript.
- Bezeichner vollständig auf Englisch, **keine Abkürzungen** (`msg`, `txt`, `res`, `dir` usw. verboten).
  Ausnahme: Feldnamen aus externen Protokollen (siehe Gotchas) bleiben wie vorgegeben.
- Konsolenausgaben (`print`) auf Englisch.

## Gotchas

- `set_target` mit Stationsname funktioniert nur für Stationen, die im Easy-Steering-Widget einen
  Button haben (Core, Azura). Für alle anderen Koordinaten verwenden – der Name wird sonst mit
  `success` akzeptiert, aber ignoriert.
- "Andocken" = in Reichweite sein (`stations_in_reach`), kein eigener Call.
- Aufgabe 2: Elyse verwendet das Feld `msg`, Shangris `data`. Zwischen den VMs gilt das neutrale
  Format `{"from": ..., "payload": [...]}`. Diese Feldnamen nicht umbenennen.
- Der XOR-verschlüsselte Payload (0xAA) muss Byte für Byte unverändert durchgereicht werden.
- Shangris-WebSocket läuft auf Port **2025** (Prosa-Doku sagt fälschlich 2024).
- Ports unter 5000 sind zwischen den VMs per Firewall gesperrt → Code muss auf den VMs laufen,
  nicht auf dem Laptop.
- Deployment per `git pull` auf der VM. Bei Problemen alten Bytecode löschen:
  `find ~/theship -name __pycache__ -type d -exec rm -rf {} +`
- Debian-VMs: `sudo apt install -y python3-pip python3-venv git` (pip fehlt standardmässig).

## Arbeitsweise mit Claude

- Bei Refactorings das Verhalten nicht ändern. Protokoll-Feldnamen, Stationsnamen, Koordinaten
  und Ports nie anfassen, ausser explizit verlangt.
- Vor grösseren Änderungen kurz den Plan zeigen.
- Code wird auf den VMs ausgeführt; lokal kann nicht gegen das Spiel getestet werden.
