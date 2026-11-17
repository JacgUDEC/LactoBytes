# =====================================================================
# boot.py - Se ejecuta automáticamente al energizar el ESP32.
# Responsabilidad: conectar el microcontrolador a la red Wi-Fi y
# sincronizar la hora antes de que se ejecute main.py (RNF-02).
# =====================================================================
import network
import time
import config


def conectar_wifi(ssid=config.WIFI_SSID, clave=config.WIFI_PASSWORD,
                  timeout_s=config.WIFI_TIMEOUT_S):
    """Conecta la interfaz STA del ESP32. Devuelve True si quedó conectada."""
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(False)
        time.sleep(1)
    wlan.active(True)
    if wlan.isconnected():
        return True

    print("[boot] Conectando a Wi-Fi:", ssid)
    wlan.connect(ssid, clave)
    inicio = time.time()
    while not wlan.isconnected():
        print(".", end="")
        if time.time() - inicio > timeout_s:
            print("[boot] No fue posible conectar. Se continúa en modo local.")
            return False
        time.sleep(0.5)

    print("[boot] Conectado. IP:", wlan.ifconfig()[0])
    return True


def sincronizar_hora():
    """Ajusta el reloj interno por NTP (necesario para el horario nocturno)."""
    try:
        import ntptime
        ntptime.settime()   # El reloj queda en UTC; main.py aplica UTC-5
        print("[boot] Hora sincronizada por NTP")
    except Exception as e:
        print("[boot] No se pudo sincronizar la hora:", e)


if conectar_wifi():
    sincronizar_hora()
