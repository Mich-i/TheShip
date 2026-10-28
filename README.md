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

## Aufgabe Analyzer Alpha (Mission 05)

Ziel: Bei **Uran Stone (-2100/3600)** bleiben und den Analyzer Alpha laufen lassen, bis der
Fortschritt 100 % erreicht. Das gilt für beide Teammitglieder **gleichzeitig**.

**Konzept:** Zum ersten Mal sind wir **gRPC-Server** und nicht Client. Das Schiffsmodul
(Analyzer) baut die Verbindung zu uns auf und holt Daten ab. Dazu kommt **Resource Owner / Data
Management**: Unser Server besitzt die Messungen beim Sensor. Er legt sie an, liest sie aus und
räumt sie wieder weg, auch nach einem Absturz des Vorgängers.

### Wer ruft wen auf

```
Analyzer-Pod (gRPC-Client)
   │ read_sensor_data(), etwa 1 s nach jeder Antwort
   ▼
unser Server  0.0.0.0:2102 auf der eigenen VM   (gRPC-Server, aufgabeAnalyzerAlpha.py)
   │ HTTP: trigger_measurement → measurements/<id> → DELETE
   ▼
Vakuumenergie-Sensor :2037
```

Der Analyzer gibt `hexdata` als Token an die Simulation weiter. Die Simulation zählt nur, wenn das
Schiff bei Uran Stone steht. Bei 0/0 bleibt der Fortschritt trotz Daten auf 0 %.
Voraussetzung ist Strom: `analyzer_alpha` und `sensor_void_energy` stehen im Energy Management
anfangs auf 0.0.

**Der Code muss auf der VM laufen.** Der Analyzer verbindet sich fest mit `<eigene VM-IP>:2102`.
Ein Server auf dem Laptop wäre für ihn nicht erreichbar.

### Neue und geänderte Dateien

| Datei | Inhalt |
|---|---|
| `src/api/sensorVoidEnergy.proto` | 1:1 aus der Doku des Analyzers. Package, Service und Methodenname dürfen sich nicht ändern |
| `src/api/sensorVoidEnergy_pb2.py`, `..._pb2_grpc.py` | Daraus generiert. Sie liegen im Repo, damit auf der VM `git pull` reicht. Neu erzeugen: `python -m grpc_tools.protoc -I src --python_out=src --grpc_python_out=src src/api/sensorVoidEnergy.proto` |
| `src/helpers/analyzerServer.py` | `SensorVoidEnergyServer.read_sensor_data`: misst pro Anfrage frisch und gibt `hexdata` zurück. Scheitert die Messung, bekommt nur diese Anfrage `UNAVAILABLE`. `startAnalyzerServer()`: Server mit **einem** Worker auf Port 2102 starten |
| `src/helpers/vacuumEnergySensor.py` | `measureVacuumEnergy()`: feste ID `vacuum-energy-reading`, vorher und im `finally` löschen, Frist 10 s. **Neu:** `trigger_measurement` wiederholen, solange der Sensor `duplicated request_id found` meldet |
| `src/helpers/energyManagement.py` | `enableComponents(componentNames)` (früher `enableShieldComponents`): aktiven Node suchen (nicht erreichbare überspringen), Limits lesen, ergänzen und komplett zurückschicken |
| `src/aufgabeAnalyzerAlpha.py` | Ablauf: Strom freigeben → Server starten → Uran Stone anfliegen und halten → Daten liefern, bis die Mission für beide abgeschlossen ist → `finally`: Server stoppen |
| `src/components/components.py` | `ANALYZER_SERVER_PORT = 2102` |

### Gemessen

- Eine Messung dauert etwa 1–2 s. Nach einem `DELETE` lehnt der Sensor dieselbe ID noch bis
  etwa 1 s lang ab.
- **Fortschritt: etwa 2.5 % pro Sekunde, 100 % rund 45 s nach der Ankunft.** Ein Takt ist
  Messung + 1 s.
- Der Fortschritt **fällt sofort auf 0**, wenn der Analyzer keine Daten mehr bekommt. `done`
  gilt nur, solange er läuft. Abgeschlossen (`is_finished`) ist die Mission erst, wenn
  **beide gleichzeitig** 100 % haben. Darum liefert das Skript nach eigenen 100 % weiter Daten.
- Frist: `ANALYSIS_TIMEOUT_SECONDS = 600`. Das sind 45 s Analyse plus Zeit, bis der Partner
  auch auf 100 % ist. **Beide müssen innerhalb dieser 10 min starten.**

### Start (beide VMs, ungefähr gleichzeitig)

Einmalig pro VM die Messung mit der alten ID löschen (auf .50 schon erledigt):

```bash
curl -XDELETE http://127.0.0.1:2037/measurements/shield-generator-input
```

Danach auf jeder VM:

```bash
ssh ship@192.168.100.50          # Marvin: ship@192.168.100.51
cd ~/theship
git pull
.venv/bin/python -m pip install -r requirements.txt
SHIP_IP=192.168.100.50 .venv/bin/python src/aufgabeAnalyzerAlpha.py   # Marvin: SHIP_IP=192.168.100.51
```

Die Ausgabe bei Erfolg: `Uran Stone reached`, dann `Analysis progress: Stutz Michael 100%,
Eggerschwiler Marvin 100%`, dann `Mission completed`. Im Widget „Analyzer Alpha“ steht
`powered, active`.

| Widget / Meldung | Bedeutung |
|---|---|
| `not enough power` | Limits nicht gesetzt, das Skript erledigt das selbst beim Start |
| `powered, missing input` / `Connect call failed (…, 2102)` | Unser Server läuft nicht |
| Fortschritt bleibt bei 0 % trotz `powered, active` | Schiff nicht bei Uran Stone |
| `Mission not finished within 600s` | Partner hat nicht rechtzeitig gestartet |

### Anleitung für Marvin (.51)

Der Fortschritt zählt pro Person, und dein Analyzer holt die Daten nur bei **deinem** Server auf
`192.168.100.51:2102`. Du musst das Skript also auf deiner VM laufen lassen, **gleichzeitig mit
Michael**. Wer zuerst bei 100 % ist, liefert weiter Daten, bis der andere auch dort ist.

1. VPN an, `ssh ship@192.168.100.51`.
2. `cd ~/theship && git pull && .venv/bin/python -m pip install -r requirements.txt`
3. Einmalig: `curl -XDELETE http://127.0.0.1:2037/measurements/shield-generator-input`
4. Mit Michael absprechen, dann beide starten:
   `SHIP_IP=192.168.100.51 .venv/bin/python src/aufgabeAnalyzerAlpha.py`
5. Warten auf `Mission completed`. Das dauert etwa 1 min, wenn beide fast gleichzeitig starten.

### Bewusste Einschränkungen

- **Ein Worker, feste Mess-ID:** Es kann immer nur eine Messung gleichzeitig laufen. Eine
  zweite Anfrage wartet. Für einen Analyzer, der nacheinander fragt, ist das kein Verlust.
- **Kein Cache:** Jede Anfrage misst frisch (1–2 s). Das ist langsamer, dafür bekommt der Analyzer
  nie einen alten Token.
- **Fehler werden pro Anfrage behandelt:** Scheitert eine Messung, geht nur diese Anfrage schief.
  Der Analyzer fragt nach 2 s neu. Auch ein Fehler beim Lesen des Fortschritts beendet den Lauf
  nicht. Dafür fällt ein dauerhafter Fehler erst nach Ablauf der Frist auf. Bis dahin sieht man
  ihn im Log und im Widget.
- **Unverschlüsselt und offen auf 0.0.0.0:2102:** Das verlangt der Analyzer so (Package
  `api.unsafe…`). Jeder im VPN könnte Sensordaten abholen, solange das Skript läuft.
- **Nach dem Ende** bleiben die Limits auf 1.0, und das Schiff hält bei Uran Stone (Ziel bleibt
  gesetzt). Bei einem harten Abbruch (`kill -9`) läuft `finally` nicht. Den Port gibt das
  Betriebssystem trotzdem frei, und eine liegengebliebene Messung löscht der nächste Lauf.
- **Abschaltung der VM:** Ist die Simulation (`192.168.96.2`) 10 min lang nicht per Ping
  erreichbar, fährt `shutdown_cron` die VM herunter. Ein Abbruch mitten im Lauf hat dann diesen
  Grund. Prüfen: `sudo journalctl -n 5 _PID=$(pgrep -f shutdown_cron)`.

## Aufgabe Laser (Mission 10)

Ziel: Beide Schiffe docken **vollbeladen mit Stein (14/14)** bei **Vesta Station (7000/7000)** an.
Den Stein baut man mit dem Laser (Port 2018) beim Asteroiden **Arakrock (-18236/-11783)** ab.
Lernziel ist OAuth2: Den Laser darf nur ein eingeloggter Techniker benutzen, und den
Login-Server (Keycloak) stellen wir selbst.

Dateien: `src/aufgabeLaser.py`, Helper `src/helpers/laser.py`, Keycloak-Manifest `k8s/keycloak.yaml`.

### Keycloak

Auf der VM gibt es kein Docker. Darum läuft Keycloak wie RabbitMQ als Deployment im k3s:

- Image `quay.io/keycloak/keycloak:26.0`, Modus `start-dev --import-realm`, Namespace `keycloak`
- Service `NodePort 2015 → 8080`
- Kein Volume: Bei jedem Start importiert Keycloak den Realm `theship` neu aus der ConfigMap im
  Manifest. Das ist reproduzierbar und übersteht einen Neustart.
- Im Realm stehen der confidential Client `laser`, der Scope `use_laser` und der User `techniker`.
  Die redirect_uris enthalten die Callbacks beider VMs, darum ist das Manifest auf .50 und .51
  identisch.
- Im Manifest ist keine IP eingetragen. Keycloak bildet Issuer und Login-URLs aus der
  aufgerufenen Adresse. Browser und Laser-Pod rufen beide `http://<VM-IP>:2015` auf und bekommen
  deshalb denselben Issuer.

| Was | Wert |
|---|---|
| Techniker-Login | `techniker` / `Laser-2026` |
| Client | `laser`, Secret `5LgQDb_mOYc105g2N4vH2Im1Qgw_NvWL` |
| Admin-Konsole | `http://<VM-IP>:2015/admin`, `admin` / `admin` |
| Authorize-URL | `http://<VM-IP>:2015/realms/theship/protocol/openid-connect/auth` |
| Token-URL | `http://<VM-IP>:2015/realms/theship/protocol/openid-connect/token` |

Secret und Passwörter stehen bewusst im Klartext im Repo. Für ein Schulprojekt ist das in
Ordnung, produktiv würde man das nie so machen.

### So läuft der OAuth2-Login (Authorization Code Flow)

```
Browser ──1. GET :2018/login──────────────► Laser
Browser ◄─2. Redirect auf Keycloak ─────────  (client_id=laser, scope=use_laser,
                                               redirect_uri=http://<VM-IP>:2018/callback)
Browser ──3. Login techniker/Passwort─────► Keycloak :2015
Browser ◄─4. Redirect auf :2018/callback?code=… ─
Browser ──5. GET :2018/callback?code=…────► Laser
                                    Laser ──6. POST /token (code + client_secret)──► Keycloak
                                    Laser ◄─7. Access Token ────────────────────────
```

1. Der Techniker öffnet `:2018/login`. Der Laser (**Client**) leitet ihn zu Keycloak
   (**Authorization Server**) weiter.
2. Das Passwort gibt der Techniker **nur bei Keycloak** ein. Der Laser sieht es nie.
3. Keycloak leitet den Browser mit einem kurzlebigen **Code** zurück an die `redirect_uri` des
   Lasers. Keycloak akzeptiert nur redirect_uris, die beim Client eingetragen sind.
4. Der Laser tauscht den Code direkt bei Keycloak gegen ein **Access Token**. Dabei weist er sich
   mit dem **Client-Secret** aus. Das Secret kennen nur Laser und Keycloak, es läuft nie über den
   Browser. Darum heisst der Client "confidential".
5. Mit dem Token gilt der Laser als freigeschaltet. Das Widget zeigt dann
   "Freigeschaltet und inaktiv". Unser Skript braucht danach kein Token mehr, es ruft nur noch
   `activate`, `angle` und `state` auf.

`configure_oauth` sagt dem Laser, wo Keycloak liegt und wie sein Secret lautet. Die `client_id`
(`laser`) und den Scope (`use_laser`) gibt der Laser selbst vor.

### Abbau-Mechanik (gemessen)

- **Direkt auf dem Asteroiden trifft der Laser nicht.** Das Skript hält 300 Einheiten östlich
  von Arakrock (`MINING_POSITION`). Auf diese Distanz funktioniert es.
- **Winkel:** `PUT /angle` ist relativ zum Schiff:
  `Laserwinkel = Weltwinkel − Schiffswinkel + 90`. Weltwinkel laufen im Uhrzeigersinn
  (0 = +x, 90 = −y, 180 = −x). Gemessen aus drei Richtungen (Osten, Norden, Südwesten).
  `aimLaserAt()` rechnet das aus der aktuellen Position. Das Skript zielt jede Sekunde neu, weil
  der Schiffswinkel beim Halten leicht dreht.
- `activate` wirkt nach etwa 1 s (`state` zeigt es verzögert an). **Der Laser schaltet sich nach
  etwa 10 s selbst ab** und wird dann neu aktiviert. `is_cooling_down` war im Test nie `true`.
- **Etwa 1 Stein pro Sekunde**, der Hold ist in rund 15 s voll.
- Der Steinzähler im WhatsUpp bleibt gespeichert. **"ist bei Vesta Station" gilt nur, solange
  man dort ist.** Das Skript lässt das Ziel auf Vesta, damit das Schiff angedockt bleibt, bis
  der Partner auch da ist.

### Start (Michael, .50)

Keycloak und Login sind auf .50 schon eingerichtet. Das Schiff von .50 wartet bereits
vollbeladen bei Vesta.

```bash
cd ~/theship
SHIP_IP=192.168.100.50 .venv/bin/python src/aufgabeLaser.py
```

Ausgabe bei Erfolg: `Arakrock reached`, einige `stone=…/14`-Zeilen, `Docked at Vesta Station`,
dann der Fortschritt und `Waiting for partner` oder `Mission completed`.

### Anleitung für Marvin (.51)

Firewall: Ports unter 5000 sind zwischen den VMs gesperrt. Darum brauchst du einen **eigenen**
Keycloak auf `192.168.100.51:2015`. Alle Befehle laufen auf deiner VM.

1. VPN an, dann `ssh ship@192.168.100.51`
2. Code holen:
   ```bash
   cd ~/theship
   git pull
   find ~/theship -name __pycache__ -type d -exec rm -rf {} +
   ```
3. Keycloak starten (der erste Start dauert 1–2 min, weil das Image geladen wird):
   ```bash
   sudo k3s kubectl apply -f k8s/keycloak.yaml
   sudo k3s kubectl -n keycloak rollout status deploy/keycloak --timeout=300s
   curl -s http://192.168.100.51:2015/realms/theship | head -c 100
   ```
   Die letzte Zeile muss JSON mit `"realm":"theship"` zeigen.
4. Den Laser auf deinen Keycloak einstellen (**deine IP!**):
   ```bash
   curl -XPOST http://192.168.100.51:2018/configure_oauth --data '{"client_secret": "5LgQDb_mOYc105g2N4vH2Im1Qgw_NvWL", "authorize_url": "http://192.168.100.51:2015/realms/theship/protocol/openid-connect/auth", "token_url": "http://192.168.100.51:2015/realms/theship/protocol/openid-connect/token"}'
   ```
   Antwort: `{"kind": "success"}`
5. Im Browser auf dem Laptop `http://192.168.100.51:2018/login` öffnen und mit `techniker` /
   `Laser-2026` anmelden. Im Cockpit `http://192.168.100.51:2000` muss das Laser-Widget
   **"Freigeschaltet und inaktiv"** zeigen.
6. Skript starten:
   ```bash
   SHIP_IP=192.168.100.51 .venv/bin/python src/aufgabeLaser.py
   ```
7. Fertig, wenn `Mission completed` erscheint. Das Schiff bleibt bei Vesta stehen. Beende das
   Skript nicht mit einem Wegflug, sonst gilt "ist bei Vesta" nicht mehr.

| Meldung / Symptom | Ursache und Lösung |
|---|---|
| Widget "Deaktiviert (keine oauth2 Config)" | Schritt 4 fehlt, oder der Laser-Pod wurde neu installiert. Schritt 4 und 5 wiederholen |
| Keycloak zeigt "Invalid parameter: redirect_uri" | Login über eine andere Adresse als die VM-IP geöffnet. `http://<VM-IP>:2018/login` verwenden |
| `Hold not full within 120s. Is the technician logged in?` | Login fehlt (Widget prüfen, Schritt 5), oder `active=True mining=False`: Winkel trifft nicht, Ausgabe melden |
| `connection refused` auf Port 2015 | Keycloak läuft nicht: Schritt 3 |
| `TimeoutError ... not reached` | Schiff kam nicht an: Cockpit prüfen, neu starten |

### Bewusste Einschränkungen

- `configure_oauth` und der Browser-Login sind **einmalige Handarbeit** und nicht im Skript.
  Ein erneuter `configure_oauth`-Aufruf könnte die Freischaltung zurücksetzen.
- Keycloak hat keine Datenbank auf Disk. Nach einem Neustart ist der Realm wieder da, die
  Sessions aber nicht. Ob der Laser danach freigeschaltet bleibt, haben wir nicht getestet.
  Im Zweifel Schritt 5 wiederholen. Ohne Neustart hielt die Freischaltung im Test über 20 min.
- Feste Abbauposition östlich von Arakrock, kein Suchen des Winkels. Trifft der Laser nicht,
  bricht das Skript nach 120 s ab.

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
  aufgabeAnalyzerAlpha.py
  aufgabeLaser.py
  api/
    sensorVoidEnergy.proto
    sensorVoidEnergy_pb2.py
    sensorVoidEnergy_pb2_grpc.py
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
    analyzerServer.py
    laser.py
k8s/
  rabbitmq.yaml
  keycloak.yaml
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