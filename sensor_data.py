# =====================================================================
# sensor_data.py - Clase SensorData
# Encapsula la lectura de todos los sensores (DHT11, HC-SR04 y LDR),
# aplica filtros para descartar lecturas anómalas y empaqueta los
# resultados en un diccionario de Python listo para enviar a la nube.
# =====================================================================
from machine import Pin, ADC, time_pulse_us
import time
import dht
import config


class SensorData:

    def __init__(self):
        # --- Sensor de temperatura ---
        pin_dht = Pin(config.PIN_DHT)
        if config.TIPO_SENSOR_TEMP == "DHT22":
            self._dht = dht.DHT22(pin_dht)
        else:
            self._dht = dht.DHT11(pin_dht)

        # --- Sensor ultrasónico ---
        self._trig = Pin(config.PIN_TRIG, Pin.OUT, value=0)
        self._echo = Pin(config.PIN_ECHO, Pin.IN)

        # --- Fotorresistencia (ADC de 12 bits, rango 0-3.3 V) ---
        self._ldr = ADC(Pin(config.PIN_LDR))
        self._ldr.atten(ADC.ATTN_11DB)

        # --- Estado interno (encapsulado) ---
        self._historial_temp = []
        self._fallas_temp = 0
        self.temperatura = None
        self.humedad = None
        self.distancia_mm = None
        self.nivel_mm = None
        self.nivel_pct = None
        self.luz_pct = None

    # ------------------------------------------------------------------
    # Temperatura: lectura + validación de rango + media móvil
    # ------------------------------------------------------------------
    def leer_temperatura(self):
        try:
            self._dht.measure()
            t = self._dht.temperature()
            h = self._dht.humidity()
            # El DHT11 mide de 0 a 50 °C: lo que esté fuera es una falla
            if t is None or t < 0 or t > 50:
                raise ValueError("Lectura fuera de rango")
            self._historial_temp.append(t)
            if len(self._historial_temp) > config.MUESTRAS_FILTRO:
                self._historial_temp.pop(0)
            self.temperatura = sum(self._historial_temp) / len(self._historial_temp)
            self.humedad = h
            self._fallas_temp = 0
        except Exception as e:
            self._fallas_temp += 1
            print("[SensorData] Error DHT:", e)
        return self.temperatura

    def sensor_temp_en_falla(self):
        """True si el sensor térmico falló 3 veces seguidas."""
        return self._fallas_temp >= 3

    # ------------------------------------------------------------------
    # Nivel: pulso de 10 us en TRIG, tiempo del eco y mediana de muestras
    # distancia = (tiempo * velocidad del sonido) / 2
    # ------------------------------------------------------------------
    def _medir_distancia_una_vez(self):
        self._trig.value(0)
        time.sleep_us(2)
        self._trig.value(1)
        time.sleep_us(10)
        self._trig.value(0)
        duracion = time_pulse_us(self._echo, 1, 30000)  # 30 ms = ~5 m máx.
        if duracion < 0:
            return None                                 # Sin eco (timeout)
        return duracion * 0.343 / 2                     # 343 m/s -> mm/us

    def leer_nivel(self):
        muestras = []
        for _ in range(config.MUESTRAS_FILTRO):
            d = self._medir_distancia_una_vez()
            if d is not None and 0 < d < 4000:
                muestras.append(d)
            time.sleep_ms(60)       # Tiempo recomendado entre disparos
        if not muestras:
            self.distancia_mm = None
            self.nivel_mm = None
            self.nivel_pct = None
            return None

        muestras.sort()
        d = muestras[len(muestras) // 2]                # Mediana
        self.distancia_mm = d
        util = config.ALTURA_SILO_MM - config.DISTANCIA_MIN_MM
        nivel = config.ALTURA_SILO_MM - d
        nivel = max(0, min(nivel, util))
        self.nivel_mm = nivel
        self.nivel_pct = round(nivel * 100 / util, 1)
        return self.nivel_pct

    # ------------------------------------------------------------------
    # Luminosidad: 0 % = oscuridad total, 100 % = luz plena
    # ------------------------------------------------------------------
    def leer_luz(self):
        suma = 0
        for _ in range(config.MUESTRAS_FILTRO):
            suma += self._ldr.read()
        promedio = suma / config.MUESTRAS_FILTRO
        self.luz_pct = round(promedio * 100 / 4095, 1)
        return self.luz_pct

    # ------------------------------------------------------------------
    def leer_todo(self):
        self.leer_temperatura()
        self.leer_nivel()
        self.leer_luz()
        return self.a_diccionario()

    def a_diccionario(self):
        """Empaqueta las lecturas válidas en un diccionario Python."""
        datos = {}
        if self.temperatura is not None:
            datos["temperatura"] = round(self.temperatura, 1)
        if self.humedad is not None:
            datos["humedad"] = self.humedad
        if self.nivel_mm is not None:
            datos["nivel_mm"] = round(self.nivel_mm, 1)
            datos["nivel_pct"] = self.nivel_pct
        if self.luz_pct is not None:
            datos["luz_pct"] = self.luz_pct
        return datos
