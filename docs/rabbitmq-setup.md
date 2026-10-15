# RabbitMQ für den Scanner (Aufgabe Scanner)

Der Scanner (`theship-vendor/scanner`) veröffentlicht seine Messungen über AMQP. Er verbindet sich
mit `<K8S_HOST>:2014` und den Standard-Credentials `guest/guest`. `K8S_HOST` ist die IP der eigenen
VM (Michael `192.168.100.50`, Marvin `192.168.100.51`). Ohne Broker zeigt das Scanner-Widget
`Status: rabbitmq: could not connect to <IP>:2014`.

Wir betreiben RabbitMQ im bestehenden k3s der VM ([k8s/rabbitmq.yaml](../k8s/rabbitmq.yaml)):

- offizielles Image `rabbitmq:4`, dort ist `loopback_users.guest = false` bereits gesetzt
- eigener Namespace `rabbitmq`, damit ein "reinstall" im Installer (`theship-vendor`) nichts löscht
- `NodePort` 2014 → 5672, gleich wie die Schiffsmodule (k3s erlaubt NodePorts ab 2000)
- kein Volume, die Nachrichten sind flüchtig

Das Manifest enthält keine IP und ist auf beiden VMs identisch.

## Setup auf der VM

```bash
ssh ship@192.168.100.51
cd ~/theship
git pull
sudo k3s kubectl apply -f k8s/rabbitmq.yaml
sudo k3s kubectl -n rabbitmq rollout status deploy/rabbitmq --timeout=180s
```

`kubectl` gibt es auf der VM nur als `sudo k3s kubectl` (die Kubeconfig gehört root).

## Kurzer Check

```bash
# Pod läuft, Service hat Port 2014
sudo k3s kubectl -n rabbitmq get pods,svc

# Port ist offen
timeout 3 bash -c "</dev/tcp/127.0.0.1/2014" && echo "2014 open"

# Scanner ist als guest verbunden und hat seine Exchanges angelegt
sudo k3s kubectl -n rabbitmq exec deploy/rabbitmq -- rabbitmqctl -q list_connections user peer_host state
sudo k3s kubectl -n rabbitmq exec deploy/rabbitmq -- rabbitmqctl -q list_exchanges name type | grep scanner
```

Erwartet: eine Verbindung `guest ... running` und die Exchanges `scanner/status` und
`scanner/detected_objects` (beide `fanout`). Im Cockpit (`http://<IP>:2000`) zeigt das
Scanner-Widget `Status: scanning`, und die Tabelle name/pos füllt sich.

Der Scanner versucht alle 2 s neu zu verbinden und braucht keinen Neustart. Falls er trotzdem
hängt: im Installer bei `scanner` auf "reinstall" klicken und die Logs prüfen:

```bash
sudo k3s kubectl -n theship-vendor logs deploy/scanner --tail=20
```

## Entfernen

```bash
sudo k3s kubectl delete -f k8s/rabbitmq.yaml
```
