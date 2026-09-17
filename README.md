# The Ship

Steuerung des Schiffs über die REST und WebSocket Schnittstellen der Bordkomponenten.

Team: Stutz Michael (VM 192.168.100.50), Eggerschwiler Marvin (VM 192.168.100.51)

Aufgabe 1 läuft lokal auf dem Laptop, Aufgabe 2 auf der VM. Warum, steht weiter unten.

---

## Setup lokal

**Einmalig:**

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Starten**, beides aus dem Projektordner.

Direkt, ohne venv zu aktivieren:

```powershell
.\.venv\Scripts\python.exe src\aufgabe1.py
```

Oder venv aktivieren und dann normal starten:

```powershell
.\.venv\Scripts\Activate.ps1
python src\aufgabe1.py
```

Nach dem Aktivieren steht `(.venv)` vor dem Prompt. Gilt nur für dieses
Terminal, mit `deactivate` oder beim Schliessen ist es weg.

> `python -m venv .venv` erwischt den Microsoft Store Stub und legt ein venv
> ohne pip an ("No module named pip"). Darum den vollen Pfad zu Python 3.13
> verwenden. Bei pip im Zweifel immer `.\.venv\Scripts\python.exe -m pip`
> schreiben, sonst installiert es am venv vorbei.

---

## Aufgabe 1: Einleitung

Schiff vollbeladen mit Eisen (12/12) bei Vesta Station andocken.

- Bei Azura Station Eisen kaufen (5/Stück), bei Core Station verkaufen (10/Stück)
- Geld verdoppelt sich pro Runde, aus 20 Credits werden so in 3 Runden 12 Eisen
- Danach Kurs auf 7000/7000

---

## Aufgabe 2: Kommunikation

Elyse Terminal (-70565/72811) und Shangris Station (4446/4340) wollen
miteinander kommunizieren. Ein Comm-Modul funktioniert nur, wenn ein Schiff in
Reichweite der Station ist, und die Stationen liegen rund 100'000 Einheiten
auseinander. Also parkt ein Schiff bei Elyse, das andere bei Shangris, und
zwischen den VMs läuft ein eigener Kanal.

Anforderung: mindestens alle 3s eine Nachricht weiterleiten, mindestens 20s
lang, in beide Richtungen.

### Warum der Code auf der VM läuft

Vom Laptop aus ist nur die eigene VM auf den Bordports erreichbar. Auf die
fremde VM kommen nur Ports ab 5000 durch:

```powershell
Test-NetConnection 192.168.100.50 -Port 2000   # TcpTestSucceeded : True
Test-NetConnection 192.168.100.51 -Port 2000   # PingSucceeded True, TCP False
```

Shangris ist damit vom Laptop aus grundsätzlich nicht ansprechbar. Der Relay
muss auf den VMs selbst laufen, weil nur die sich gegenseitig erreichen.

### Setup auf der VM

Auf der VM liegt Debian 13 mit Python 3.13.5, aber ohne pip.

```bash
ssh ship@192.168.100.50
mkdir -p ~/theship
cd ~/theship
sudo apt update && sudo apt install -y python3-pip python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Deployment

```powershell
scp -r src requirements.txt ship@192.168.100.50:~/theship/
```

Marvin nimmt seine eigene VM als Ziel (.51). Bei jeder Codeänderung neu
kopieren, die VM merkt nichts von lokalen Änderungen.

Die `__pycache__` Ordner kommen beim scp mit und stören:

```bash
find ~/theship -name __pycache__ -type d -exec rm -rf {} +
```

### Starten

Beide Seiten starten dasselbe Skript, nur mit anderem Argument, und **zur
gleichen Zeit**, damit sich die 60 Sekunden überlappen.

```bash
tmux new -s ship
cd ~/theship
.venv/bin/python src/aufgabe2.py elyse       # auf .50
.venv/bin/python src/aufgabe2.py shangris    # auf .51
```

tmux, weil der Prozess sonst mit der SSH Verbindung stirbt. `Ctrl+B` dann `D`
löst ab, `tmux attach -t ship` kehrt zurück.

Kontrolle im Cockpit unter http://192.168.100.50:2000, im WhatsUpp-Widget
laufen die beiden Zähler hoch.

### Aufbau

```
src/
  components/components.py   IP, Ports, Stations-Dict, Relay-Port
  helpers/
    stationChat.py           WebSocket zum Comm-Modul, mit Reconnect
    relay.py                 eigener Kanal zwischen den VMs
  aufgabe2.py                Einstieg, nimmt "elyse" oder "shangris"
```

- **Ein WebSocket-Modul für beide Stationen.** Der Unterschied zwischen Elyse
  und Shangris steckt komplett im Stations-Dict, nicht im Code
- **Neutrales Format auf dem Kanal:** `{"from": ..., "payload": [...]}`. Der
  Relay kennt weder `msg` noch `data` und muss nichts über die Stationen wissen
- **Übersetzung nur an den Endpunkten**, in `stationChat.py`
- **Relay über HTTP** auf Port 5000, POST auf `/message`. Beide Seiten lauschen
  und senden, darum keine Server/Client Rollen und keine Startreihenfolge
- **Zwei Richtungen laufen parallel**, Station zu Partner-VM und zurück
- **Seed am Anfang:** eine Startnachricht anstossen, danach schickt das
  Comm-Modul von allein weiter und der 3s-Takt ergibt sich

---

## Notizen

- **Ports:** Easy Steering 2009, Communication 2011, Cargo Hold 2012
- **Comm-Module:** Elyse `ws://127.0.0.1:2026/api`, Shangris `ws://127.0.0.1:2025/ws`
- **Stationsnamen** als Ziel funktionieren nur für Core Station und Azura
  Station. Alle anderen Ziele, zB: Vesta Station, müssen als Koordinaten
  gesetzt werden. Sonst antwortet die API mit "success", das Schiff bewegt
  sich aber nicht
- **Andocken** heisst: in Reichweite der Station sein
- **Nach der Ankunft** `setTarget("stop")`, sonst driftet das Schiff während
  des Tests aus der Reichweite

Zu Aufgabe 2 speziell:

- **Nutzlastfeld unterschiedlich:** Elyse verwendet `msg`, Shangris `data`.
  Eine unveränderte Nachricht von Elyse hat für Shangris kein `data` Feld und
  wird ignoriert. Das ist der eigentliche Kern der Aufgabe
- **Shangris Port:** die Doku widerspricht sich, Prosa sagt 2024, Beispielcode
  2025. Richtig ist 2025. Lauschende Ports auf der VM prüfen mit
  `ss -ltnp | grep 202`
- **Payload nicht anfassen.** Die Zahlenliste ist XOR mit `0xAA` verschlüsselt
  und enthält `source`, `destination`, `data`, `ts` und eine `signature`. Kein
  Neu-Serialisieren, kein Umsortieren, byte-für-byte durchreichen
- **`destination` ist echt** und zeigt auf die Partnerstation, blindes
  Weiterleiten ist darum korrekt
- **`source` beim Senden** ist die Herkunftsstation, nicht die eigene. Man ist
  der Postbote
- **Reconnect nötig.** Die WebSocket Verbindung bricht im Betrieb ab und wird
  neu aufgebaut, ohne Reconnect-Loop ist der Lauf danach vorbei
- **"Connection refused"** auf Port 5000 heisst, auf der anderen Seite läuft
  kein Prozess. Ein Timeout wäre die Firewall
