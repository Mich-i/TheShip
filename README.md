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
$env:SHIP_IP = "192.168.100.50"; .\.venv\Scripts\python.exe src\aufgabe1.py
```

Ohne `SHIP_IP` sprechen die Skripte `127.0.0.1` an. Das passt auf der VM. Auf dem Laptop
muss die VM-IP gesetzt sein.

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
- **SHIP_IP** wählt das Schiff und den Namen im Fortschritt. Ohne Variable gilt `127.0.0.1`,
  dann bricht das Skript mit `Unknown ship IP` ab. Darum immer setzen, Marvin mit
  `SHIP_IP=192.168.100.51`.
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

Die Anleitung zum Nachmachen auf .51 steht ganz unten: [Anleitung für Marvin: Aufgabe Laser](#anleitung-für-marvin-aufgabe-laser).

### Ziel und Lösungsidee

Beide Schiffe docken **vollbeladen mit Stein (14/14)** bei **Vesta Station (7000/7000)** an. Den
Stein baut man mit dem Laser (Port 2018) beim Asteroiden **Arakrock (-18236/-11783)** ab.

Den Laser darf nur ein eingeloggter Techniker benutzen, und der Login läuft über OAuth2. Den
Login-Server stellen wir selbst: Keycloak im k3s der eigenen VM auf Port 2015. Ist der Techniker
einmal im Browser eingeloggt, erledigt `src/aufgabeLaser.py` den Rest: zu Arakrock fliegen,
abbauen, bis der Hold voll ist, und nach Vesta fliegen.

Dateien: `src/aufgabeLaser.py`, `src/helpers/laser.py`, `k8s/keycloak.yaml`.

### Architektur

```
Laptop (VPN)                    VM 192.168.100.50, k3s

Browser ──── :2018/login ─────► Laser-Pod (OAuth2-Client "laser")
   │                               │
   │                               │ Token-Tausch
   │                               ▼
   └──────── :2015 Login ──────► Keycloak-Pod (Authorization Server, Realm "theship")

aufgabeLaser.py (auf der VM) ── 127.0.0.1 ──► Laser :2018, Easy Steering :2009,
                                              Communication :2011, Cargo Hold :2012, WhatsUpp :2040
```

Jede VM hat ihren eigenen Keycloak. Ports unter 5000 sind zwischen den VMs gesperrt, und jeder
Laser soll nur mit dem Keycloak seines Schiffs reden.

### OAuth2 Authorization Code Flow, an unserem Fall

```
Browser ──1. GET :2018/login──────────────► Laser
Browser ◄─2. Redirect auf Keycloak ─────────  (client_id=laser, scope=use_laser,
                                               redirect_uri=http://192.168.100.50:2018/callback)
Browser ──3. Login techniker/Passwort─────► Keycloak :2015
Browser ◄─4. Redirect auf :2018/callback?code=… ─
Browser ──5. GET :2018/callback?code=…────► Laser
                                    Laser ──6. POST /token (code + client_id + client_secret)──► Keycloak
                                    Laser ◄─7. Access Token ──────────────────────────────────
```

1. **Vorbereitung:** `configure_oauth` sagt dem Laser, wo Keycloak liegt (`authorize_url`,
   `token_url`) und wie sein **Client-Secret** lautet. `client_id=laser` und `scope=use_laser`
   gibt der Laser selbst vor. Dazu passend gibt es in Keycloak den Client `laser`.
2. **Login starten (1–2):** Der Techniker öffnet `:2018/login`. Der Laser ist der **Client** und
   leitet den Browser zur `authorize_url` weiter. Mit dabei sind `client_id`, `scope` und die
   `redirect_uri`, an die Keycloak danach zurückleiten soll. Die `redirect_uri` bildet der Laser
   aus der Adresse, mit der man ihn aufruft.
3. **Anmelden (3):** Das Passwort gibt der Techniker **nur bei Keycloak** ein. Der Laser sieht es
   nie.
4. **Code (4–5):** Keycloak prüft, ob die `redirect_uri` beim Client eingetragen ist. Dann leitet
   es den Browser mit einem kurzlebigen, einmal gültigen **Code** zum Laser zurück.
5. **Token (6–7):** Der Laser tauscht den Code direkt bei Keycloak gegen ein **Access Token**.
   Dabei weist er sich mit `client_id` und **Client-Secret** aus. Das Secret läuft nie über den
   Browser, darum heisst der Client "confidential". Wer nur den Code abfängt, kann ohne Secret
   nichts damit anfangen.
6. Danach ist der Laser freigeschaltet. Das Widget zeigt "Freigeschaltet und inaktiv". Unser
   Skript braucht kein Token, es ruft nur `activate`, `angle` und `state` auf.

**Warum Browser und Laser-Pod dieselbe URL brauchen:** Beide sprechen mit Keycloak, aber von
verschiedenen Orten aus. Den Browser schickt der Laser zur `authorize_url`, der Laser-Pod ruft
die `token_url` selbst auf. Die Adresse muss deshalb von beiden aus erreichbar sein.
`127.0.0.1` zeigt im Browser auf den Laptop, ein k3s-Servicename ist im Browser nicht auflösbar.
Nur `http://<VM-IP>:2015` funktioniert für beide. Ausserdem bildet Keycloak seinen Issuer aus
der aufgerufenen Adresse. Mit derselben URL gehören Code und Token zum selben Issuer.

**Wo eine echte IP nötig ist:** nur in `configure_oauth` (Keycloak-URLs) und in der Login-URL im
Browser. Beides sind Einmal-Schritte von Hand. Das Skript selbst läuft mit `127.0.0.1` und ohne
`SHIP_IP`, auf beiden VMs mit identischem Code.

### Keycloak-Setup

Auf der VM gibt es kein Docker, auch nicht mit sudo. Darum läuft Keycloak wie RabbitMQ als
Deployment im k3s: `k8s/keycloak.yaml`, Image `quay.io/keycloak/keycloak:26.0`,
`start-dev --import-realm`, Namespace `keycloak`, Service `NodePort 2015 → 8080`.

| Was | Wert |
|---|---|
| Realm | `theship` (`sslRequired: none`, wir haben nur HTTP) |
| Client | `laser`, confidential, Secret `5LgQDb_mOYc105g2N4vH2Im1Qgw_NvWL`, nur Standard Flow (Authorization Code) |
| redirect_uris | `http://192.168.100.50:2018/callback`, `http://192.168.100.51:2018/callback`, `http://localhost:2018/callback` |
| Client-Scopes | `use_laser` (verlangt der Laser), `basic` (liefert `sub` im Token) |
| User | `techniker` / `Laser-2026` |
| Admin-Konsole | `http://<VM-IP>:2015/admin`, `admin` / `admin` |
| Authorize-URL | `http://<VM-IP>:2015/realms/theship/protocol/openid-connect/auth` |
| Token-URL | `http://<VM-IP>:2015/realms/theship/protocol/openid-connect/token` |

**Warum Realm-Import per Manifest:** Der ganze Realm steht als JSON in einer ConfigMap im
Manifest. Keycloak hat kein Volume und importiert ihn bei jedem Start neu. Damit ist das Setup
mit einem `kubectl apply` wiederholbar, auf beiden VMs gleich (keine IP drin, die redirect_uris
beider VMs sind eingetragen), und man muss nichts in der Admin-Konsole zusammenklicken. Eigene
`clientScopes` im JSON ersetzen Keycloaks Standard-Scopes. Darum ist `basic` von Hand mit drin.

Secret und Passwörter stehen bewusst im Klartext im Repo. Für ein Schulprojekt ist das in
Ordnung, produktiv nie.

### Abbau-Mechanik (gemessen)

- **Abstand:** Direkt auf dem Asteroiden baut der Laser nichts ab. Mit 300 Einheiten Abstand
  geht es. Das Skript hält östlich von Arakrock (`MINING_POSITION`).
- **Winkel:** `Laserwinkel = Weltwinkel − Schiffswinkel + 90`
  - *Weltwinkel* = Richtung vom Schiff zum Asteroiden, im Uhrzeigersinn: 0 = +x, 90 = −y,
    180 = −x. Daraus ergibt sich `−atan2(dy, dx)`.
  - *Schiffswinkel* = `angle` aus `/pos`.
  - Herleitung: Wir haben jeweils durchprobiert, bei welchem Laserwinkel `is_mining` true wird.
    Von Osten (Schiff 89°, Ziel 180°) traf 180, von Norden (Schiff 297°, Ziel 90°) traf 240.
    Beide Male ist Laser − (Ziel − Schiff) ≈ 90. Also ist der Laser relativ zum Schiff und um
    90° versetzt. Mit `aimLaserAt()` aus Südwesten kontrolliert, auch während sich das Schiff
    dreht (341° → 354°).
- **Aktivierung:** `activate` antwortet immer mit `success`. `state` zeigt `is_active` erst nach
  etwa 1 s. Nach etwa 10 s schaltet sich der Laser selbst ab und muss neu aktiviert werden.
  `is_cooling_down` war nie `true`.
- **Tempo:** etwa 1 Stein pro Sekunde, der Hold (14) ist in rund 15 s voll.
- **Fortschritt:** Der Steinzähler im WhatsUpp bleibt gespeichert. "ist bei Vesta Station" gilt
  **nur, solange das Schiff dort ist**. Vesta, Core, Azura, Illume Colony und G-Station 3-5
  kaufen keinen Stein.

### Ablauf des Skripts

`src/aufgabeLaser.py`, flach von oben nach unten:

1. `flyTo(MINING_POSITION)`: Ziel setzen und warten, bis das Schiff weniger als 50 Einheiten
   entfernt ist (Frist 300 s).
2. Abbau-Schleife, solange der Hold nicht voll ist, einmal pro Sekunde:
   `aimLaserAt(getPosition(), ARAKROCK)`, dann `getLaserState()`, und falls der Laser aus ist,
   `activateLaser()`. Frist 120 s, danach bricht das Skript mit einem Hinweis auf den Login ab.
   Im `finally` steht `deactivateLaser()`, auch bei Fehlern oder Ctrl+C.
3. `flyTo(VESTA_COORDINATES)`, dann prüfen, ob Vesta in `stations_in_reach` ist. Das Ziel bleibt
   gesetzt, damit das Schiff angedockt bleibt.
4. Den Fortschritt aus dem WhatsUpp ausgeben, dann `Mission completed` oder `Waiting for partner`.

Helper `src/helpers/laser.py`:

| Funktion | Aufruf |
|---|---|
| `getLaserState()` | `GET :2018/state` → `is_active`, `is_mining`, `is_cooling_down` |
| `activateLaser()` / `deactivateLaser()` | `POST :2018/activate` bzw. `/deactivate` |
| `aimLaserAt(shipPosition, target)` | rechnet die Winkelformel, `PUT :2018/angle` |

Dazu kommen die bestehenden Helper `setTarget`, `getPosition`, `stationsInReach`, `getInventory`
und `getMissionChat`.

### Getestet (auf .50)

| Test | Ergebnis |
|---|---|
| Browser-Login über `http://192.168.100.50:2018/login` | Widget "Freigeschaltet und inaktiv", Keycloak zeigt eine Session `techniker` → `laser` |
| Abbau von Hand von Osten, Winkel 180 | 14/14 Stein in etwa 15 s, WhatsUpp "abgebauter Stein" 14/14 |
| `aimLaserAt()` aus Südwesten | `is_mining: true`, auch während das Schiff dreht |
| `aufgabeLaser.py` auf der VM **ohne `SHIP_IP`** | Arakrock → Vesta, "Docked at Vesta Station", WhatsUpp 14/14 und "ist bei Vesta" |
| `rollout restart` von Keycloak | Laser bleibt freigeschaltet, `activate` → `is_active: true` |

**Nicht getestet:**
- Die Abbau-Schleife im Skript mit leerem Hold. Der Hold war schon durch den Handtest voll, und
  keine bekannte Station kauft Stein zurück. Die Schleife nutzt dieselben Aufrufe wie die
  Handtests.
- Ein Neustart oder Reinstall des Laser-Pods. Vermutlich ist dann `configure_oauth` und der
  Login weg (siehe Fehlertabelle bei Marvin).
- Marvins VM. .51 war beim Test nicht erreichbar.

### Einschränkungen und Gotchas

- `configure_oauth` und der Browser-Login sind **einmalige Handarbeit** und nicht im Skript.
  Ein erneuter `configure_oauth`-Aufruf könnte die Freischaltung zurücksetzen.
- `/state` zeigt nicht an, ob jemand eingeloggt ist, das sieht man nur im Widget. Ohne Login
  bleibt `is_active` false, obwohl `activate` `success` meldet.
- Die Abbauposition ist fest, das Skript sucht keinen Winkel. Trifft der Laser nicht, bricht es
  nach 120 s ab.
- Das Schiff muss bei Vesta stehen bleiben, bis auch der Partner dort ist.
- Keycloak läuft ohne Datenbank auf Disk. Nach einem Neustart sind die Sessions weg, die
  Freischaltung des Lasers bleibt aber (getestet).

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


---

# Anleitung für Marvin: Aufgabe Laser

Wie es funktioniert, steht oben im Abschnitt [Aufgabe Laser (Mission 10)](#aufgabe-laser-mission-10).
Hier nur die Schritte. Alle Befehle laufen **auf deiner VM `192.168.100.51`**, ausser dem
Browser-Login in Schritt 6. Michaels Schiff wartet schon vollbeladen bei Vesta.

**Voraussetzungen:** WireGuard-VPN ist an, `ssh ship@192.168.100.51` funktioniert, und das Repo
liegt unter `~/theship`.

1. **Einloggen und Code holen**
   ```bash
   ssh ship@192.168.100.51
   cd ~/theship
   git pull
   find ~/theship -name __pycache__ -type d -exec rm -rf {} +
   ```
   ✔ `git log --oneline -1` zeigt denselben Commit wie bei Michael.

2. **Python-Umgebung prüfen**
   ```bash
   ls .venv/bin/python || python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```
   ✔ Das pip-Ergebnis endet ohne Fehler. Fehlt `python3 -m venv`:
   `sudo apt install -y python3-pip python3-venv git`.

3. **Prüfen, ob der Laser installiert ist**
   ```bash
   curl -s http://127.0.0.1:2018/state
   ```
   ✔ `{"kind": "success", "is_mining": false, ...}`. Kommt nichts zurück: Im Installer
   (`http://192.168.100.51:2000`) den `laser` installieren.

4. **Keycloak starten.** `kubectl` geht nur mit `sudo k3s kubectl`. Der erste Start dauert
   1–2 min, weil das Image geladen wird.
   ```bash
   sudo k3s kubectl apply -f k8s/keycloak.yaml
   sudo k3s kubectl -n keycloak rollout status deploy/keycloak --timeout=300s
   curl -s http://192.168.100.51:2015/realms/theship | head -c 60; echo
   ```
   ✔ `deployment "keycloak" successfully rolled out` und `{"realm":"theship",...`

5. **Laser auf deinen Keycloak einstellen** (Achtung, deine IP .51 steht dreimal drin)
   ```bash
   curl -XPOST http://192.168.100.51:2018/configure_oauth --data '{"client_secret": "5LgQDb_mOYc105g2N4vH2Im1Qgw_NvWL", "authorize_url": "http://192.168.100.51:2015/realms/theship/protocol/openid-connect/auth", "token_url": "http://192.168.100.51:2015/realms/theship/protocol/openid-connect/token"}'
   ```
   ✔ `{"kind": "success"}`.

6. **Im Browser auf dem Laptop einloggen**
   - `http://192.168.100.51:2018/login` öffnen (mit IP, nicht localhost)
   - Es erscheint die Keycloak-Anmeldung "theship". Benutzer `techniker`, Passwort `Laser-2026`.

   ✔ Im Cockpit `http://192.168.100.51:2000` zeigt das Laser-Widget
   **"Aktueller Status: Freigeschaltet und inaktiv"**.

7. **Skript starten** (ohne `SHIP_IP`, das Skript nimmt 127.0.0.1)
   ```bash
   cd ~/theship
   .venv/bin/python src/aufgabeLaser.py
   ```
   ✔ Erwartete Ausgabe (dauert einige Minuten):
   ```text
   Mining stone at Arakrock
   Arakrock reached
   stone=0/14 active=False mining=False
   stone=1/14 active=True mining=True
   ...
   Laser deactivated
   Hold full (14/14), flying to Vesta Station
   Docked at Vesta Station
   ...
   Mission completed
   ```
   Steht am Ende `Waiting for partner`, ist Michaels Schiff nicht mehr bei Vesta. Melde dich bei
   ihm.

8. **Schiff bei Vesta stehen lassen.** Das Skript lässt das Ziel auf Vesta. Nichts anderes
   anfliegen, bis im WhatsUpp "10 - Laser" abgeschlossen ist. "ist bei Vesta Station" gilt nur,
   solange das Schiff dort steht.

### Fehlertabelle

| Symptom | Ursache | Lösung |
|---|---|---|
| Schritt 3: keine Antwort von `:2018` | Laser nicht installiert | Im Installer `laser` installieren |
| `rollout status` hängt, Pod `ImagePullBackOff` | VM kommt nicht an `quay.io` | `sudo k3s kubectl -n keycloak describe pod` lesen, Internet der VM prüfen |
| `curl :2015` → `Connection refused` | Keycloak läuft nicht (mehr) | Schritt 4 |
| Widget "Deaktiviert (keine oauth2 Config)" | `configure_oauth` fehlt, oder der Laser-Pod wurde neu installiert | Schritt 5 und 6 wiederholen |
| Keycloak zeigt "Invalid parameter: redirect_uri" | Login über eine andere Adresse geöffnet | Genau `http://192.168.100.51:2018/login` verwenden |
| Browser findet `:2015` nicht | In Schritt 5 eine falsche IP eingetragen (z. B. .50 oder 127.0.0.1) | Schritt 5 mit .51 wiederholen, dann Schritt 6 |
| Keycloak wurde neu gestartet (`rollout restart`, VM-Neustart) | Sessions sind weg, der Laser bleibt aber freigeschaltet (getestet) | Nichts tun. Zeigt das Widget nicht mehr "Freigeschaltet": Schritt 6, falls nötig vorher 5 |
| `Hold not full within 120s. Is the technician logged in?` und `active=False` | Nicht eingeloggt | Widget prüfen, Schritt 6 |
| Gleiche Meldung, aber `active=True mining=False` | Winkel trifft nicht | Ausgabe an Michael schicken |
| `TimeoutError ... not reached within 300s` | Schiff kam nicht an | Cockpit prüfen, Skript neu starten |
| `Waiting for partner` | Partner nicht bei Vesta | Schiff stehen lassen, Partner fliegt hin |
| `ConnectionError` auf 127.0.0.1 | Skript auf dem Laptop gestartet | Auf der VM starten (oder `$env:SHIP_IP = "192.168.100.51"`) |
