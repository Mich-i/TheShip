# Aufgabe Scanner starten

Mission: Beide Schiffe bleiben je 60 s in der Nähe von G-Station 0-5. Die Mission ist erst
abgeschlossen, wenn **beide gleichzeitig** 60/60 s haben. Fällt ein Schiff aus der Reichweite,
springt sein Zähler sofort auf 0. Deshalb müssen beide Skripte **gleichzeitig** laufen.

Das Skript `src/aufgabeScanner.py` fliegt zum Treffpunkt (14148/10804), folgt der Station mit
Vorhalten und läuft so lange, bis der WhatsUpp-Chat "09 - Scanner" abgeschlossen ist (max. 10 min).
Danach stoppt es das Schiff. Neue WhatsUpp-Nachrichten im Chat erscheinen auf der Konsole.

## Voraussetzungen (pro VM)

- RabbitMQ läuft auf der VM: [rabbitmq-setup.md](rabbitmq-setup.md)
- Im Cockpit (`http://<IP>:2000`) zeigt das Scanner-Widget `Status: scanning`
- Abhängigkeiten installiert (pika ist neu):

```bash
cd ~/theship
git pull
.venv/bin/python -m pip install -r requirements.txt
```

`SHIP_IP` bestimmt das Schiff und den Namen im WhatsUpp-Fortschritt. Ohne Variable wird
`192.168.100.50` (Michael) verwendet. Eine unbekannte IP bricht mit Fehlermeldung ab.

## Variante 1: Jeder auf seiner VM

Michael (auf 192.168.100.50):

```bash
cd ~/theship
.venv/bin/python src/aufgabeScanner.py
```

Marvin (auf 192.168.100.51):

```bash
cd ~/theship
SHIP_IP=192.168.100.51 .venv/bin/python src/aufgabeScanner.py
```

## Variante 2: Beide vom Laptop (zwei Terminals)

Vom Laptop sind die Ports der VMs über das VPN erreichbar. Die zwei Prozesse teilen keine
Dateien, sie schreiben nur auf die eigene Konsole.

PowerShell, Terminal 1:

```powershell
$env:SHIP_IP = "192.168.100.50"; .\.venv\Scripts\python.exe src\aufgabeScanner.py
```

PowerShell, Terminal 2:

```powershell
$env:SHIP_IP = "192.168.100.51"; .\.venv\Scripts\python.exe src\aufgabeScanner.py
```

(Git Bash: `SHIP_IP=192.168.100.51 .venv/Scripts/python.exe src/aufgabeScanner.py`)

## Was man sieht

```
Ship 192.168.100.50 (Stutz Michael): following G-Station 0-5
[scanner] connected to 192.168.100.50:2014
Rendezvous 14148/10804 reached
Entered reach of G-Station 0-5 at distance 52
t= 34.7s ship=15361/11993 station=15346/11978 distance=21 in reach=yes progress: Stutz=27/60s Eggerschwiler=0/60s
...
Mission finished after 95s, watching WhatsUpp for 15s
Ship stopped
```

Wer zuerst 60/60 s erreicht hat, folgt weiter, bis auch der Partner fertig ist. Bricht man mit
Ctrl+C ab, stoppt das Schiff.

## Fehlersuche

- `[scanner] connection to <IP>:2014 failed`: Broker läuft nicht oder ist nicht erreichbar,
  siehe [rabbitmq-setup.md](rabbitmq-setup.md).
- `distance=unknown`: Der Scanner sieht die Station noch nicht. Vom Treffpunkt aus ist die ganze
  Bahn sichtbar.
- Timeouts auf alle Ports: VPN prüfen bzw. ob die VM läuft.
