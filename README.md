# The Ship

Steuerung des Schiffs über REST Schnittstellen der Bordkomponenten.

## Setup

**Einmalig:**

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Starten

Beides aus dem Projektordner.

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

## Notizen

- **Ports:** Easy Steering 2009, Communication 2011, Cargo Hold 2012
- **Stationsnamen** als Ziel funktionieren nur für Core Station und Azura
  Station. Alle anderen Ziele, zB: Vesta Station, müssen als Koordinaten
  gesetzt werden. Sonst antwortet die API mit "success", das Schiff bewegt
  sich aber nicht.
- **Andocken** heisst: in Reichweite der Station sein.
