# =====================================================================
# actuator_controller.py - Clase ActuatorController
# Contiene la lógica de decisión y el control de las salidas:
# relé + mini bomba, servomotor (ventilador), LEDs de criticidad e
# iluminación perimetral.
# =====================================================================
from machine import Pin, PWM
import time
import config

# Estados de criticidad térmica
ESTABLE = 0      # LED verde
ALERTA = 1       # LED amarillo
CRITICO = 2      # LED rojo
NOMBRE_ESTADO = {ESTABLE: "ESTABLE", ALERTA: "ALERTA", CRITICO: "CRITICO"}


class ActuatorController:

    def __init__(self):
        self._rele = Pin(config.PIN_RELE, Pin.OPEN_DRAIN, value=1)
        self._servo = PWM(Pin(config.PIN_SERVO), freq=50)
        self._led_verde = Pin(config.PIN_LED_VERDE, Pin.OUT, value=0)
        self._led_amarillo = Pin(config.PIN_LED_AMARILLO, Pin.OUT, value=0)
        self._led_rojo = Pin(config.PIN_LED_ROJO, Pin.OUT, value=0)
        self._luz = Pin(config.PIN_LUZ_PERIMETRAL, Pin.OUT, value=0)

        self.estado = ESTABLE
        self.bomba_encendida = False
        self.ventilador_encendido = False
        self.luz_encendida = False
        self.alarma_desborde = False
        self._angulo = 0
        self._sentido = 1

        self.apagar_bomba()
        self.mover_servo(0)

    # ------------------------------------------------------------------
    # Etapa de potencia: relé -> mini bomba de agua
    # ------------------------------------------------------------------
    def _escribir_rele(self, encender):
        if config.RELE_ACTIVO_EN_BAJO:
            self._rele.value(0 if encender else 1)
        else:
            self._rele.value(1 if encender else 0)

    def encender_bomba(self):
        self._escribir_rele(True)
        self.bomba_encendida = True

    def apagar_bomba(self):
        self._escribir_rele(False)
        self.bomba_encendida = False

    def controlar_nivel(self, nivel_pct):
        """Control ON/OFF con histéresis para el trasvase de leche."""
        if nivel_pct is None:
            self.apagar_bomba()             # Sin lectura confiable: seguro
            return
        self.alarma_desborde = nivel_pct >= config.NIVEL_DESBORDE_PCT
        if self.alarma_desborde or nivel_pct >= config.NIVEL_ALTO_PCT:
            self.apagar_bomba()
        elif nivel_pct <= config.NIVEL_BAJO_PCT:
            self.encender_bomba()
        # Entre los dos umbrales se mantiene el estado anterior

    # ------------------------------------------------------------------
    # Servomotor (PWM 50 Hz): pulso de 0.5 ms (0°) a 2.5 ms (180°)
    # ------------------------------------------------------------------
    def mover_servo(self, angulo):
        angulo = max(0, min(180, angulo))
        pulso_us = 500 + angulo * 2000 / 180
        self._servo.duty_u16(int(pulso_us * 65535 / 20000))
        self._angulo = angulo

    def paso_ventilador(self):
        """Barrido de 0° a 180° y regreso, simulando las aspas del enfriador."""
        nuevo = self._angulo + 45 * self._sentido
        if nuevo >= 180 or nuevo <= 0:
            self._sentido *= -1
        self.mover_servo(nuevo)

    # ------------------------------------------------------------------
    # Criticidad térmica: verde / amarillo / rojo
    # ------------------------------------------------------------------
    def evaluar_temperatura(self, temperatura, sensor_en_falla=False):
        h = config.HISTERESIS_TEMP
        if sensor_en_falla or temperatura is None:
            # Falla del sensor: se asume lo peor (enfriar y alertar)
            self.estado = CRITICO
        elif temperatura >= config.TEMP_CRITICA:
            self.estado = CRITICO
        elif temperatura >= config.TEMP_ALERTA:
            # Si venía de crítico, solo baja cuando cae bajo el umbral - h
            if self.estado == CRITICO and temperatura > config.TEMP_CRITICA - h:
                self.estado = CRITICO
            else:
                self.estado = ALERTA
        else:
            if self.estado != ESTABLE and temperatura > config.TEMP_ALERTA - h:
                self.estado = ALERTA        # Histéresis: aún no es estable
            else:
                self.estado = ESTABLE

        self._led_verde.value(1 if self.estado == ESTABLE else 0)
        self._led_amarillo.value(1 if self.estado == ALERTA else 0)
        self._led_rojo.value(1 if self.estado == CRITICO else 0)

        # El enfriamiento se activa en ALERTA y en CRITICO
        self.ventilador_encendido = self.estado != ESTABLE
        if self.ventilador_encendido:
            self.paso_ventilador()
        else:
            self.mover_servo(0)
        return self.estado

    # ------------------------------------------------------------------
    # Iluminación perimetral: oscuridad (LDR) u horario nocturno
    # ------------------------------------------------------------------
    @staticmethod
    def es_horario_nocturno():
        anio = time.localtime()[0]
        if anio < 2024:                     # Reloj sin sincronizar
            return False
        hora = (time.localtime()[3] + config.ZONA_HORARIA) % 24
        return hora >= config.HORA_INICIO_NOCHE or hora < config.HORA_FIN_NOCHE

    def controlar_iluminacion(self, luz_pct):
        oscuro = luz_pct is not None and luz_pct < config.LUZ_OSCURO_PCT
        noche = config.USAR_HORARIO_NOCTURNO and self.es_horario_nocturno()
        self.luz_encendida = oscuro or noche
        self._luz.value(1 if self.luz_encendida else 0)

    # ------------------------------------------------------------------
    def a_diccionario(self):
        return {
            "estado": self.estado,
            "bomba": 1 if self.bomba_encendida else 0,
            "ventilador": 1 if self.ventilador_encendido else 0,
            "iluminacion": 1 if self.luz_encendida else 0,
            "desborde": 1 if self.alarma_desborde else 0,
        }
