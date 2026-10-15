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

## Aufgabe Scanner (Mission 09)

Ziel: Beide Schiffe bleiben je 60 s ohne Unterbruch in der Nähe von **G-Station 0-5**, und zwar
gleichzeitig. Die Station fliegt im Uhrzeigersinn ein abgerundetes Quadrat (1800 × 1800 um
15048/11104, etwa 55 Einheiten/s, Umlauf etwa 96 s) und kommt dabei am Treffpunkt **14148/10804**
vorbei.

Datei: `src/aufgabeScanner.py`, Helper `src/helpers/scanner.py` und `src/helpers/whatsupp.py`.

### RabbitMQ

Die Scanner-Komponente veröffentlicht ihre Messungen per AMQP. Sie verbindet sich mit
`<eigene VM-IP>:2014` (guest/guest). Wir betreiben dafür RabbitMQ im k3s der VM
(`k8s/rabbitmq.yaml`, Namespace `rabbitmq`, NodePort 2014). Setup und Check pro VM:
[docs/rabbitmq-setup.md](docs/rabbitmq-setup.md).

Nachrichtenformat: Fanout-Exchange `scanner/detected_objects`, etwa alle 0.2 s eine JSON-Liste
aller Objekte in Sichtweite (mindestens ~2300 Einheiten):

```json
[{"name": "G-Station 0-5", "pos": {"x": 14148.0, "y": 11003.8, "r": 0.0}},
 {"name": "192.168.100.51", "pos": {"x": 14135.0, "y": 11225.0, "r": 90.0}}]
```

`r` ist ein Drehwinkel. Neben Stationen erscheinen auch Schiffe (Name = IP).
`scanner.py` hängt eine eigene, exklusive Queue an dieses Exchange. Das passiert in einem eigenen
Thread, weil pika nicht threadsicher ist. Der Helper merkt sich immer nur die neueste Liste.
Das Skript fragt sie mit `getObject(name)` ab.

### So folgt das Skript

1. Zum Treffpunkt fliegen. Von dort sieht der Scanner die ganze Bahn.
2. Etwa 3-mal pro Sekunde die Position der Station lesen und ihre Geschwindigkeit aus der
   letzten Sekunde schätzen.
3. **Vorhalten:** Ziel = Position + Geschwindigkeit · 3 s (`LEAD_SECONDS`). Easy Steering bremst
   vor dem Ziel ab. Ein Ziel direkt auf der Station hängt deshalb immer hinterher. Mit Vorhalten
   fliegt das Schiff neben ihr. Testlauf: Distanz im Mittel 65, nie aus der Reichweite.
4. Ende, wenn der WhatsUpp-Chat "09 - Scanner" abgeschlossen ist (`is_finished`) oder nicht mehr
   existiert. Nach dem Abschluss verschwindet der Chat. Danach stoppt das Schiff, auch bei Ctrl+C.
   Nach 600 s (`MAX_RUNTIME_SECONDS`) bricht das Skript ab.

### Stolpersteine

- **Der Zähler fällt auf 0**, sobald das Schiff die Reichweite verlässt (~245 Einheiten). Die 60 s
  müssen am Stück erreicht werden.
- **Beide gleichzeitig:** Die Mission ist erst fertig, wenn beide gleichzeitig 60/60 s haben.
  Wer zuerst fertig ist, folgt weiter. Beide Skripte also ungefähr gleichzeitig starten.
- **SHIP_IP** wählt das Schiff und den Namen im Fortschritt. Ohne Variable gilt
  `192.168.100.50`. Marvin braucht immer `SHIP_IP=192.168.100.51`.
- Repo-Pfad (`~/theship`) und venv-Name (`.venv`) müssen auf beiden VMs gleich sein, sonst
  stimmen die Befehle unten nicht.
- Easy Steering kennt nur Core und Azura beim Namen. Der Treffpunkt wird deshalb als Koordinate
  angeflogen.

### Startanleitung

**1. Laptop:** Der neue Stand muss auf GitHub sein.

```powershell
git status
git push
```

**2. Auf jeder VM** (Michael `192.168.100.50`, Marvin `192.168.100.51`):

```bash
ssh ship@192.168.100.50
cd ~/theship
git pull
.venv/bin/python -m pip install -r requirements.txt
```

RabbitMQ prüfen (Pod `Running`, Port offen):

```bash
sudo k3s kubectl -n rabbitmq get pods
timeout 3 bash -c "</dev/tcp/127.0.0.1/2014" && echo "2014 open"
```

Im Cockpit `http://<VM-IP>:2000` muss das Scanner-Widget `Status: scanning` zeigen.
Läuft RabbitMQ auf der VM noch nicht:

```bash
sudo k3s kubectl apply -f k8s/rabbitmq.yaml
sudo k3s kubectl -n rabbitmq rollout status deploy/rabbitmq --timeout=180s
```

Der Scanner verbindet sich innerhalb von 2 s selbst. Details: [docs/rabbitmq-setup.md](docs/rabbitmq-setup.md).

**3. Starten, auf beiden VMs ungefähr gleichzeitig:**

```bash
# Michael, auf 192.168.100.50
cd ~/theship
SHIP_IP=192.168.100.50 .venv/bin/python src/aufgabeScanner.py
```

```bash
# Marvin, auf 192.168.100.51
cd ~/theship
SHIP_IP=192.168.100.51 .venv/bin/python src/aufgabeScanner.py
```

Vom Laptop geht es auch, mit zwei Terminals im Projektordner:
`$env:SHIP_IP = "192.168.100.51"; .\.venv\Scripts\python.exe src\aufgabeScanner.py`

**4. Erfolg und Fehler**

So sieht es aus, wenn es klappt:

```text
Ship 192.168.100.50 (Stutz Michael) is following G-Station 0-5
[scanner] connected to 192.168.100.50:2014
Rendezvous reached
distance=35 progress=12/60s
...
Mission completed
Ship stopped
```

Im WhatsUpp-Widget laufen beide Zähler bis 60/60 s, danach verschwindet der Chat.

| Meldung / Symptom | Ursache und Lösung |
|---|---|
| `[scanner] connection to <IP>:2014 failed` | RabbitMQ läuft nicht: Schritt 2, RabbitMQ aufsetzen |
| `Unknown ship IP ...` | `SHIP_IP` falsch oder vergessen |
| Nach "Rendezvous reached" keine `distance=`-Zeilen | Scanner liefert nichts: Widget prüfen, sonst im Installer `scanner` → reinstall |
| `progress` fällt auf 0 | Schiff war kurz ausser Reichweite. Das Skript folgt weiter und zählt neu |
| Eigener Zähler bei 60, Skript läuft weiter | Normal, es wartet auf den Partner |
| `Time limit of 600s reached` | Partner nicht gestartet: beide gemeinsam neu starten |
| `ModuleNotFoundError: No module named 'pika'` | `pip install -r requirements.txt` vergessen |
| `ConnectTimeout` bei Requests | VPN oder VM prüfen |
| Seltsames Verhalten nach `git pull` | alten Bytecode löschen: `find ~/theship -name __pycache__ -type d -exec rm -rf {} +` |

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
  aufgabeRaumAnomalie.py
  aufgabeScanner.py
  components/
    components.py
  helpers/
    easySteering.py
    relay.py
    stationChat.py
    communication.py
    cargoHold.py
    energyManagement.py
    vacuumEnergySensor.py
    vacuumEnergyStore.py
    scanner.py
    whatsupp.py
k8s/
  rabbitmq.yaml
docs/
  rabbitmq-setup.md
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



---

# Hausaufgaben

**Aufgabe Raumanomalie refactoring:**

**Die Leitfrage bei beiden Methoden:** Was passiert, wenn genau hier Schluss ist? Jede Zeile, die über das Netz geht, kann hängen, scheitern oder mitten im Ablauf abbrechen. Unsere erste Version hat überall den Best Case angenommen.

**`measureVacuumEnergy` — das Problem:** Die `request_id` war ein zufälliges UUID, das nur im Arbeitsspeicher existierte. Stirbt das Programm zwischen `trigger_measurement` und `DELETE` (Ctrl+C, VPN weg, Exception), bleibt beim Sensor eine Messung liegen, deren ID niemand mehr kennt. Bei jedem Lauf kommen neue dazu, und die Doku warnt ausdrücklich, dass das speicherintensiv ist.

**Die Lösung:** Feste ID statt UUID, und **vor** dem Start löschen. Dadurch kennt jeder Lauf den Schlüssel seines Vorgängers und räumt dessen Leiche weg — das System repariert sich selbst. Dazu ein `try/finally`, damit auch bei Exception und Ctrl+C gelöscht wird, und ein Timeout, damit die Polling-Schleife nicht ewig dreht, wenn der Sensor stumm bleibt.

**Der Preis:** Mit fester ID darf nur ein Client gleichzeitig messen. Das ist bei einem Schiff mit einem Sensor kein Verlust, aber eine bewusste Entscheidung — und so sollten wir es auch sagen.

**`enableShieldComponents` — das Problem:** Die Methode sollte Ausfallsicherheit nutzen, hätte sie aber selber zunichte gemacht. War Node 1 nicht erreichbar, flog beim `.json()` eine Exception und Node 2 wurde nie gefragt. Genau im Ausfallszenario, für das die zwei Nodes existieren, hätte unser Code aufgegeben.

**Die Lösung:** Fehler beim Abfragen eines Nodes abfangen und zum nächsten weitergehen. Zusätzlich das `PUT` prüfen — sonst merken wir nicht, wenn die Limits gar nicht gesetzt wurden.

**Querverbindung:** `PUT` ersetzt die komplette Ressource, deshalb lesen wir die Limits erst und schicken alle acht Werte zurück. Schickten wir nur unsere zwei, wären alle Thruster-Limits weg.

**Die drei Regeln zum Mitnehmen:**

1. Jeder Request braucht ein `timeout` — ohne hängt das Programm bei einem Netzunterbruch endlos und still.
2. Jede Warteschleife braucht eine Abbruchbedingung mit Frist.
3. Wer etwas anlegt, muss das Aufräumen auch nach einem Absturz noch zustande bringen — `finally` reicht dafür nicht, weil es bei einem harten Abbruch nicht läuft.