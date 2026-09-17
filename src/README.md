# The Ship

Steuerung des Schiffs über die REST und WebSocket Schnittstellen der Bordkomponenten.

Team: Stutz Michael (VM 192.168.100.50), Eggerschwiler Marvin (VM 192.168.100.51)

Aufgabe 1 läuft lokal auf dem Laptop, Aufgabe 2 auf der VM. Warum, steht weiter unten.

---

## Setup lokal

*Einmalig:*

powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt


*Starten*, beides aus dem Projektordner.

Direkt, ohne venv zu aktivieren:

powershell
.\.venv\Scripts\python.exe src\aufgabe1.py


Oder venv aktivieren und dann normal starten:

powershell
.\.venv\Scripts\Activate.ps1
python src\aufgabe1.py


Nach dem Aktivieren steht (.venv) vor dem Prompt. Gilt nur für dieses
Terminal, mit deactivate oder beim Schliessen ist es weg.

> python -m venv .venv erwischt den Microsoft Store Stub und legt ein venv
> ohne pip an ("No module named pip"). Darum den vollen Pfad zu Python 3.13
> verwenden. Bei pip im Zweifel immer .\.venv\Scripts\python.exe -m pip
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

powershell
Test-NetConnection 192.168.100.50 -Port 2000   # TcpTestSucceeded : True
Test-NetConnection 192.168.100.51 -Port 2000   # PingSucceeded True, TCP False


Shangris ist damit vom Laptop aus grundsätzlich nicht ansprechbar. Der Relay
muss auf den VMs selbst laufen, weil nur die sich gegenseitig erreichen.

### Setup auf der VM

Auf der VM liegt Debian 13 mit Python 3.13.5, aber ohne pip und ohne git.

bash
ssh ship@192.168.100.50
sudo apt update && sudo apt install -y python3-pip python3-venv git
cd ~
git clone https://github.com/Mich-i/TheShip.git theship
cd theship
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt


Marvin macht dasselbe auf seiner VM (.51) und klont dasselbe Repo. Bei
Codeänderungen danach nur noch:

bash
cd ~/theship && git pull


> Passwort-Authentifizierung für Git-Operationen unterstützt GitHub nicht mehr.
> Entweder Repo public, oder Personal Access Token statt Passwort.

### Starten

Beide Seiten starten ihr eigenes Skript, und die Laufzeiten müssen sich
überlappen.

bash
cd ~/theship
.venv/bin/python src/aufgabe2Elyse.py        # auf .50
.venv/bin/python src/aufgabe2Shangris.py     # auf .51


Ablauf, damit beide Zähler laufen:

1. Wer noch nicht an seiner Station steht, startet zuerst und fliegt hin
2. Warten bis [Elyse Terminal] connected erscheint
3. Dann startet die andere Seite
4. Im Cockpit unter http://192.168.100.50:2000 laufen beim WhatsUpp-Widget
   beide Zähler hoch

DURATION steht bewusst deutlich über den geforderten 20s, damit ein Versatz
beim Start nichts ausmacht. Sobald beide Zähler bei 20s sind, kann mit
Ctrl+C abgebrochen werden.

### Aufbau[08:53, 17.9.2026] Michi: ssh ship@192.168.100.51
sudo apt install -y git
cd ~
rm -rf theship
git clone https://github.com/Mich-i/TheShip.git theship
cd theship
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ls src/
[08:57, 17.9.2026] Michi: tmux new -s ship
cd ~/theship
.venv/bin/python src/aufgabe2Elyse.py        # du auf .50
.venv/bin/python src/aufgabe2Shangris.py     # Marvin auf .51
[10:19, 17.9.2026] Michi: # The Ship

Steuerung des Schiffs über die REST und WebSocket Schnittstellen der Bordkomponenten.

Team: Stutz Michael (VM 192.168.100.50), Eggerschwiler Marvin (VM 192.168.100.51)

Aufgabe 1 läuft lokal auf dem Laptop, Aufgabe 2 auf der VM. Warum, steht weiter unten.

---

## Setup lokal

*Einmalig:*

powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt


*Starten*, beides aus dem Projektordner.

Direkt, ohne venv zu aktivieren:

powershell
.\.venv\Scripts\python.exe src\aufgabe1.py


Oder venv aktivieren und dann normal starten:

powershell
.\.venv\Scripts\Activate.ps1
python src\aufgabe1.py


Nach dem Aktivieren steht (.venv) vor dem Prompt. Gilt nur für dieses
Terminal, mit deactivate oder beim Schliessen ist es weg.

> python -m venv .venv erwischt den Microsoft Store Stub und legt ein venv
> ohne pip an ("No module named pip"). Darum den vollen Pfad zu Python 3.13
> verwenden. Bei pip im Zweifel immer .\.venv\Scripts\python.exe -m pip
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

powershell
Test-NetConnection 192.168.100.50 -Port 2000   # TcpTestSucceeded : True
Test-NetConnection 192.168.100.51 -Port 2000   # PingSucceeded True, TCP False


Shangris ist damit vom Laptop aus grundsätzlich nicht ansprechbar. Der Relay
muss auf den VMs selbst laufen, weil nur die sich gegenseitig erreichen.

### Setup auf der VM

Auf der VM liegt Debian 13 mit Python 3.13.5, aber ohne pip und ohne git.

bash
ssh ship@192.168.100.50
sudo apt update && sudo apt install -y python3-pip python3-venv git
cd ~
git clone https://github.com/Mich-i/TheShip.git theship
cd theship
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt


Marvin macht dasselbe auf seiner VM (.51) und klont dasselbe Repo. Bei
Codeänderungen danach nur noch:

bash
cd ~/theship && git pull


> Passwort-Authentifizierung für Git-Operationen unterstützt GitHub nicht mehr.
> Entweder Repo public, oder Personal Access Token statt Passwort.

### Starten

Beide Seiten starten ihr eigenes Skript, und die Laufzeiten müssen sich
überlappen.

bash
cd ~/theship
.venv/bin/python src/aufgabe2Elyse.py        # auf .50
.venv/bin/python src/aufgabe2Shangris.py     # auf .51


Ablauf, damit beide Zähler laufen:

1. Wer noch nicht an seiner Station steht, startet zuerst und fliegt hin
2. Warten bis [Elyse Terminal] connected erscheint
3. Dann startet die andere Seite
4. Im Cockpit unter http://192.168.100.50:2000 laufen beim WhatsUpp-Widget
   beide Zähler hoch

DURATION steht bewusst deutlich über den geforderten 20s, damit ein Versatz
beim Start nichts ausmacht. Sobald beide Zähler bei 20s sind, kann mit
Ctrl+C abgebrochen werden.

### Aufbau