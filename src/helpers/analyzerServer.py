from concurrent.futures import ThreadPoolExecutor
import grpc
from api import sensorVoidEnergy_pb2, sensorVoidEnergy_pb2_grpc
from components.components import ANALYZER_SERVER_PORT
from helpers.vacuumEnergySensor import measureVacuumEnergy


# grpcio verlangt eine Klasse, die von der generierten Basisklasse erbt.
# Der Methodenname kommt aus der .proto-Datei und muss so bleiben.
class SensorVoidEnergyServer(sensorVoidEnergy_pb2_grpc.SensorVoidEnergyServerServicer):

    def read_sensor_data(self, request, context):
        # Jede Anfrage des Analyzers bekommt eine frische Messung.
        # Scheitert sie, bekommt nur diese Anfrage einen Fehler, der Server laeuft weiter.
        try:
            hexData = measureVacuumEnergy()
        except Exception as error:
            print(f"Measurement failed: {error!r}")
            context.abort(grpc.StatusCode.UNAVAILABLE, f"measurement failed: {error}")
        return sensorVoidEnergy_pb2.SensorData(hexdata=hexData)


def startAnalyzerServer():
    # Ein einziger Worker: Messungen laufen nie gleichzeitig, weil der Sensor
    # mit einer festen Mess-ID arbeitet.
    server = grpc.server(ThreadPoolExecutor(max_workers=1))
    sensorVoidEnergy_pb2_grpc.add_SensorVoidEnergyServerServicer_to_server(SensorVoidEnergyServer(), server)
    server.add_insecure_port(f"0.0.0.0:{ANALYZER_SERVER_PORT}")
    server.start()
    return server
