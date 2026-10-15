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
- **Aufgabe Scanner (Mission 09)** – gelöst (beide Schiffe gemeinsam), Code danach vereinfacht.
  Skript `aufgabeScanner.py`. Details im Abschnitt "Aufgabe Scanner", Startanleitung im README.

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
| RabbitMQ (eigener Broker für scanner) | 2014 | AMQP, siehe "Aufgabe Scanner" |
| whatsupp | 2040 | Missionstext/Chat, `GET /content` (JSON inkl. Fortschritt) |

## Projektstruktur

```
src/
  components/components.py   IP + Basis-URLs der Komponenten. IP = Umgebungsvariable SHIP_IP,
                             Default "192.168.100.50" (Michael). Marvin/.51: SHIP_IP=192.168.100.51
  helpers/                   cargoHold.py, communication.py, easySteering.py, stationChat.py,
                             relay.py, energyManagement.py, vacuumEnergy*.py, scanner.py
  aufgabe1.py
  aufgabe2Elyse.py
  aufgabe2Shangris.py
  aufgabeRaumAnomalie.py
  aufgabeScanner.py
k8s/rabbitmq.yaml            RabbitMQ-Broker für den Scanner
docs/rabbitmq-setup.md       Setup-Anleitung Broker pro VM
requirements.txt             requests, websocket-client, pymongo, pika
```

Start aus dem Projektordner: `python src/<skript>.py` (kein `cd src` nötig).
Für ein anderes Schiff: `SHIP_IP=192.168.100.51 python src/<skript>.py` (gilt für alle Skripte,
weil `components.py` die IP liest; ohne Variable wird .50 verwendet).

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
- Ports unter 5000 sind nur **zwischen den VMs** per Firewall gesperrt (VM→VM erst ab 5000,
  z. B. Relay). Vom Laptop über VPN sind die Komponenten-Ports (20xx, auch 2014) erreichbar.
  Code, der Ports < 5000 der *anderen* VM bräuchte, muss deshalb auf der jeweiligen VM laufen.
- Deployment per `git pull` auf der VM. Bei Problemen alten Bytecode löschen:
  `find ~/theship -name __pycache__ -type d -exec rm -rf {} +`
- Debian-VMs: `sudo apt install -y python3-pip python3-venv git` (pip fehlt standardmässig).

## Arbeitsweise mit Claude

- Bei Refactorings das Verhalten nicht ändern. Protokoll-Feldnamen, Stationsnamen, Koordinaten
  und Ports nie anfassen, ausser explizit verlangt.
- Vor grösseren Änderungen kurz den Plan zeigen.
- Code wird auf den VMs ausgeführt. Kurze Tests vom Laptop gegen eine VM gehen (siehe Gotchas).
- `kubectl` auf der VM nur als `sudo k3s kubectl` (kein `~/.kube/config` für ship).

## Aufgabe Scanner

Mission: Beide Schiffe müssen je 60 s in der Nähe von **G-Station 0-5** bleiben, die regelmässig
bei (14148/10804) vorbeikommt. Fortschritt im WhatsUpp-Widget (Port 2040, Raw State: kind
`progress`, curr/max pro Person).

- **Broker:** RabbitMQ im k3s der eigenen VM, Namespace `rabbitmq` (nicht `theship-vendor`, den
  verwaltet der Installer), Image `rabbitmq:4`, Service `NodePort 2014 → 5672`, kein Volume.
  Manifest `k8s/rabbitmq.yaml`, Anleitung `docs/rabbitmq-setup.md`.
- **Scanner-Pod** (`theship-vendor/scanner`) verbindet sich mit `K8S_HOST:2014` (= eigene
  VM-IP), Login pika-Standard guest/guest, und versucht es alle 2 s neu. Startet der Broker
  später, ist kein Reinstall nötig.
- **Exchanges** (beide `fanout`): `scanner/status` (Text, z. B. `scanning`) und
  `scanner/detected_objects`. Auf `detected_objects` kommt etwa alle **0.2 s** eine JSON-Liste:
  `[{"name": "Core Station", "pos": {"x": 0.0, "y": 0.0, "r": 316.3}}, ...]`.
  `r` ist ein Drehwinkel, kein Radius. Neben Stationen erscheinen auch Schiffe (Name = IP),
  viele mit 0/0.
- **Der Scanner sieht nur Objekte in der Nähe** (Sichtweite mind. ~2300). Von Core (0/0) aus ist
  G-Station 0-5 nicht in der Liste, vom Treffpunkt aus die ganze Bahn.
- **Bahn:** abgerundetes Quadrat 1800 × 1800 um (15048/11104), x 14148–15948, y 10204–12004,
  im Uhrzeigersinn, Umlauf ~96 s, ~55 Einheiten/s. Der Treffpunkt liegt auf der linken Kante.
- **"In der Nähe"** = `stations_in_reach` ≈ 240–250 Einheiten. `curr` zählt +1/s und fällt beim
  Verlassen **sofort auf 0**. `done` gilt nur, solange man drin bleibt. Die Mission ist erst
  fertig (`is_finished` im Chat), wenn beide gleichzeitig done sind → beide Skripte parallel starten.
  Nach dem Abschluss **verschwindet der Chat** aus `/content`; das Skript endet bei `is_finished`
  oder fehlendem Chat. Die Mission lässt sich nicht erneut öffnen.
- **Steuerung:** Ziel direkt auf die Station hängt hinterher, weil Easy Steering vor dem Ziel
  abbremst. Lösung: Ziel = Position + Geschwindigkeit · `LEAD_SECONDS` (3 s). Testlauf: Distanz
  Mittel 65, Median 44, max 230, nie aus der Reichweite gefallen.
- `/pos` `velocity` ist etwa Einheiten pro Tick (× ~25 ≈ Einheiten/s), wird nicht gebraucht.
- WhatsUpp: `GET :2040/content` → `contacts["09 - Scanner"].chats[0]` mit `messages`
  (`kind` `simple`/`progress`), `is_finished`, `choices`. Helper `helpers/whatsupp.py`:
  `getMissionChat(contactName)` (oder `None`) und `getProgress(chat, playerName)`.
- Helper `src/helpers/scanner.py`: `startScanner(host)` startet einen Daemon-Thread (die
  pika-Verbindung lebt nur dort, pika ist nicht threadsicher, Neuverbinden nach 2 s).
  `getObject(name)` liefert `{"x", "y", "receivedAt"}` (`receivedAt` = `time.monotonic()`) oder `None`.
- Bewusste Vereinfachungen in `aufgabeScanner.py`: keine Fehlerbehandlung in der Folgeschleife
  (ein Timeout beendet das Skript, Schiff stoppt), kein Fallback, wenn die Station verschwindet.
  Gesamtfrist `MAX_RUNTIME_SECONDS = 600` (Regel 2).
- Start und Stolpersteine: README, Abschnitt "Aufgabe Scanner".
