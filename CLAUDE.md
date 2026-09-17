# The Ship

Schulprojekt, verteilte Systeme. Steuerung eines Raumschiffs uber REST und
WebSocket. Team: Michi (VM 192.168.100.50), Marvin (VM 192.168.100.51).

Details zu Setup und Architektur: @README.md

## Stil

- Flache Skripte ohne main(), linearer Ablauf von oben nach unten
- camelCase bei Helfern, passend zu aufgabe1.py
- Kein unnotiger Abstraktions-Overhead, das ist Schulcode

## Fallstricke

- Aufgabe 1 lauft lokal auf Windows, Aufgabe 2 auf der VM (Firewall lasst
  zwischen den VMs nur Ports ab 5000 durch)
- Shangris Comm-Modul: Port 2025, nicht 2024 wie in der Doku
- Nutzlastfeld heisst bei Elyse "msg", bei Shangris "data"
- Payload ist signiert, darf nicht neu serialisiert werden