# =====================================================================
# ubidots_client.py - Clase UbidotsClient
# Serializa los datos en JSON (ujson) y los envía por HTTP POST a la
# API REST de Ubidots. Si la red falla, devuelve False sin detener el
# control local (RNF-03, tolerancia a fallas).
# =====================================================================
import network
import ujson
import time
import config

try:
    import urequests as requests
except ImportError:
    import requests


class UbidotsClient:

    def __init__(self, token=config.UBIDOTS_TOKEN,
                 dispositivo=config.UBIDOTS_DEVICE):
        self._token = token
        self._url = config.UBIDOTS_URL + dispositivo + "/"
        self._wlan = network.WLAN(network.STA_IF)
        self.envios_ok = 0
        self.envios_fallidos = 0

    def conectado(self):
        return self._wlan.isconnected()

    def reconectar(self):
        """Intento corto de reconexión (no bloquea más de 5 s)."""
        if self.conectado():
            return True
        try:
            self._wlan.active(True)
            self._wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            inicio = time.time()
            while not self._wlan.isconnected() and time.time() - inicio < 5:
                time.sleep(0.2)
        except Exception as e:
            print("[Ubidots] Error al reconectar:", e)
        return self.conectado()

    @staticmethod
    def serializar(datos):
        """Diccionario Python -> cadena JSON {"variable": valor, ...}."""
        return ujson.dumps(datos)

    def enviar(self, datos):
        if not datos:
            return False
        if not self.reconectar():
            self.envios_fallidos += 1
            print("[Ubidots] Sin red: envío pospuesto")
            return False

        cabeceras = {
            "X-Auth-Token": self._token,
            "Content-Type": "application/json",
        }
        respuesta = None
        try:
            respuesta = requests.post(self._url, data=self.serializar(datos),
                                      headers=cabeceras)
            ok = 200 <= respuesta.status_code < 300
            if ok:
                self.envios_ok += 1
            else:
                self.envios_fallidos += 1
                print("[Ubidots] HTTP", respuesta.status_code, respuesta.text)
            return ok
        except Exception as e:
            self.envios_fallidos += 1
            print("[Ubidots] Error en la petición:", e)
            return False
        finally:
            if respuesta is not None:
                respuesta.close()           # Libera el socket y la memoria
