# =====================================================================
# main.py - Programa principal (se ejecuta después de boot.py)
# Ciclo: leer sensores -> decidir -> actuar -> enviar a Ubidots.
# El control local corre cada INTERVALO_CONTROL_S y la transmisión a la
# nube cada INTERVALO_ENVIO_S, de forma independiente.
# =====================================================================
import time
import gc
import config
from sensor_data import SensorData
from actuator_controller import ActuatorController, NOMBRE_ESTADO
from ubidots_client import UbidotsClient


def main():
    sensores = SensorData()
    actuadores = ActuatorController()
    nube = UbidotsClient()
    ultimo_envio = time.ticks_ms()

    print("[main] Sistema iniciado")
    while True:
        try:
            # 1) Captura de variables físicas
            sensores.leer_todo()

            # 2) Decisión y actuación local (no depende de la red)
            actuadores.evaluar_temperatura(sensores.temperatura,
                                           sensores.sensor_temp_en_falla())
            actuadores.controlar_nivel(sensores.nivel_pct)
            actuadores.controlar_iluminacion(sensores.luz_pct)

            print("T={} °C | Nivel={} % | Luz={} % | Estado={} | Bomba={} | Vent={}"
                  .format(sensores.temperatura, sensores.nivel_pct,
                          sensores.luz_pct, NOMBRE_ESTADO[actuadores.estado],
                          actuadores.bomba_encendida,
                          actuadores.ventilador_encendido))

            # 3) Ingesta en la nube cada INTERVALO_ENVIO_S
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, ultimo_envio) >= config.INTERVALO_ENVIO_S * 1000:
                paquete = sensores.a_diccionario()
                paquete.update(actuadores.a_diccionario())
                if nube.enviar(paquete):
                    print("[main] Datos enviados a Ubidots")
                ultimo_envio = ahora

            gc.collect()        # Libera memoria tras cada ciclo
        except Exception as e:
            # Ningún error detiene el ciclo de control
            print("[main] Error en el ciclo:", e)

        time.sleep(config.INTERVALO_CONTROL_S)


main()
