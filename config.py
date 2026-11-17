# =====================================================================
# config.py - Parámetros de configuración del sistema
# Proyecto: Lactobytes
# Plataforma: ESP32 + MicroPython
# =====================================================================

# ---------------- Red Wi-Fi -------------------------------------
WIFI_SSID = "U-SIGLOXXI"
WIFI_PASSWORD = "UdeCsigloXXI"
WIFI_TIMEOUT_S = 10          # Tiempo máximo de espera al conectar

# ---------------- Plataforma Cloud Ubidots ---------------------------
UBIDOTS_TOKEN = "BBUS-PYeIq4aq2mDv2zGvh3mQSo8fcCddvS"   # Token de la cuenta
UBIDOTS_DEVICE = "esp32"                 # Etiqueta del dispositivo
UBIDOTS_URL = "https://industrial.api.ubidots.com/api/v1.6/devices/"
INTERVALO_ENVIO_S = 5       # Cada cuántos segundos se envían datos a la nube

# ---------------- Asignación de pines GPIO del ESP32 -----------------
PIN_DHT = 4                  # Sensor de temperatura DHT11 (DATA)
PIN_TRIG = 5                 # HC-SR04 TRIG
PIN_ECHO = 18                # HC-SR04 ECHO (con divisor de voltaje a 3.3 V)
PIN_LDR = 34                 # Fotorresistencia (ADC1, solo entrada)
PIN_RELE = 16                # Módulo relé -> mini bomba de agua
PIN_SERVO = 13               # Servomotor SG90 (PWM 50 Hz)
PIN_LED_VERDE = 25
PIN_LED_AMARILLO = 33
PIN_LED_ROJO = 32
PIN_LUZ_PERIMETRAL = 27      # LED blanco de iluminación perimetral

# Tipo de sensor térmico: "DHT11" en la maqueta física
TIPO_SENSOR_TEMP = "DHT11"

# El módulo relé de la maqueta se activa con nivel BAJO (activo en 0).
RELE_ACTIVO_EN_BAJO = True

# ---------------- Umbrales térmicos (°C) -----------------------------
# Valores de la maqueta (agua a temperatura ambiente). En una planta
# real la leche cruda debe conservarse a 4 °C +/- 2 °C.
TEMP_ALERTA = 25.0           # >= Amarillo: empieza a calentarse
TEMP_CRITICA = 30.0          # >= Rojo: fuera de lo normal
HISTERESIS_TEMP = 0.5        # Evita parpadeo en los límites

# ---------------- Geometría del silo y nivel ------------------------
ALTURA_SILO_MM = 150         # Distancia sensor -> fondo con el tanque vacío
DISTANCIA_MIN_MM = 20        # Zona ciega del HC-SR04 (tanque lleno)
NIVEL_BAJO_PCT = 30          # Por debajo: encender bomba (trasvase)
NIVEL_ALTO_PCT = 85          # Por encima: apagar bomba
NIVEL_DESBORDE_PCT = 90      # Alarma de desborde: bomba apagada siempre

# ---------------- Iluminación perimetral -----------------------------
LUZ_OSCURO_PCT = 40          # Luminosidad (%) por debajo de la cual es "oscuro"
USAR_HORARIO_NOCTURNO = True # Encender también en horario nocturno
HORA_INICIO_NOCHE = 18       # 6:00 p. m.
HORA_FIN_NOCHE = 6           # 6:00 a. m.
ZONA_HORARIA = -5            # Colombia (UTC-5)

# ---------------- Tiempos del ciclo de control -----------------------
INTERVALO_CONTROL_S = 2      # El DHT11 admite como máximo 1 lectura/segundo
MUESTRAS_FILTRO = 5          # Tamaño del filtro de media móvil / mediana
