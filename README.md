# The Ship

Steuerung des Schiffs ueber die REST-Schnittstellen der Bordkomponenten.

## Aufbau

```
src/
  components/components.py   IP und Basis-URLs der Bordkomponenten
  helpers/
    cargo_hold.py            get_hold()
    communication.py         stations_in_reach(), buy(), sell()
    easy_steering.py         set_target(), wait_until_at_station(), goto()
  aufgabe1.py                Aufgabe 1
```

## Setup (nur einmal noetig)

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Hinweis: den vollen Pfad zu Python 3.13 verwenden. Ein blosses `python -m venv`
erwischt sonst den Microsoft-Store-Stub `WindowsApps\python3.9.exe` - das
ergibt ein venv ohne funktionierendes pip ("No module named pip").

## Starten

Zwei Varianten, beide aus dem Projektordner `C:\Project\TheShip`.

**Variante A - direkt, ohne venv zu aktivieren:**

```powershell
.\.venv\Scripts\python.exe src\aufgabe1.py
```

**Variante B - venv aktivieren, dann normal starten:**

```powershell
.\.venv\Scripts\Activate.ps1
python src\aufgabe1.py
```

Nach dem Aktivieren steht `(.venv)` vor dem Prompt. Das gilt nur fuer dieses
eine Terminal; mit `deactivate` oder durch Schliessen des Terminals ist es
wieder weg.

`cd src` ist nicht noetig - Python legt beim Start automatisch den Ordner des
Skripts auf den Suchpfad, darum finden die `from helpers...`-Importe alles.

## Notizen

- Ports: Easy Steering 2009, Communication 2011, Cargo Hold 2012
- Stationsnamen als Ziel funktionieren nur fuer Core Station und Azura Station.
  Alle anderen Ziele (z. B. Vesta Station) muessen als Koordinaten gesetzt
  werden - sonst antwortet die API zwar mit "success", das Schiff bewegt sich
  aber nicht.
- "Andocken" heisst einfach: in Reichweite der Station sein.
- Timeouts setzen wir pro Vorgang (`wait_until_at_station`) und nicht pro
  Request - es ist einfacher zu sagen, wie lange ein Vorgang dauern darf.
