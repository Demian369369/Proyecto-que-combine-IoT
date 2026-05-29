# =============================================================================
# config.py - Configuracion central del Aula Inteligente
# Aqui se definen redes WiFi, pines y parametros del sistema.
# Para agregar mas redes WiFi simplemente agrega un dict a la lista REDES_WIFI.
# =============================================================================

# --- Redes WiFi disponibles (agregar mas aqui sin problema) ---
# Dejar contrasena como None o cadena vacia si la red es abierta
REDES_WIFI = [
    {"ssid": "INFINITUM5DB2", "password": "t4UNUWMK34"},
    {"ssid": "iCUCEI",        "password": None},
    # Agrega mas redes aqui:
    # {"ssid": "OtraRed", "password": "otraContrasena"},
]

# Tiempo maximo de espera por red WiFi (segundos)
TIEMPO_ESPERA_WIFI = 8

# --- Pines fisicos de la ESP32 ---
PIN_DHT11   = 4     # Sensor temperatura y humedad
PIN_MQ135_A = 34    # MQ-135 salida analogica (calidad de aire)
PIN_MQ135_D = 35    # MQ-135 salida digital
PIN_RELAY1  = 26    # Relay 1 -> Ventilador 12V
PIN_SERVO   = 18    # Servo motor -> Ventanas
PIN_LCD_SDA = 21    # LCD I2C - Datos
PIN_LCD_SCL = 22    # LCD I2C - Reloj

# --- Direccion I2C de la pantalla LCD ---
LCD_ADDR = 0x3F

# --- Parametros del servo motor ---
# Duty cycle de 16 bits para angulos clave
# Rango tipico servo: 0.5ms (0 grados) a 2.5ms (180 grados) en periodo 20ms
SERVO_FREQ       = 50
SERVO_CERRADO    = 1638   # 0 grados  -> ventanas cerradas
SERVO_ABIERTO    = 4915   # 30 grados -> ventanas abiertas (ajustado al mecanismo fisico)

# --- Limite de temperatura para modo automatico ---
TEMP_MAX_VENTILADOR  = 28   # Grados Celsius: activar ventilador si supera esto

# --- Limite de calidad de aire para abrir ventanas ---
# El MQ-135 entrega valor analogico 0-4095 en la ESP32 (ADC 12 bits)
# Valores altos indican mayor concentracion de gases (CO2, NH3, etc.)
UMBRAL_GAS_PELIGROSO = 2500   # Valor ADC: abrir ventanas si supera esto

# --- Historial de escaneos FIFO ---
MAX_HISTORIAL = 10   # Maximo de registros en historial

# --- Intervalo de escaneo en modo automatico (segundos) ---
INTERVALO_ESCANEO = 60

# --- Informacion del equipo para el footer de la pagina web ---
EQUIPO = [
    {"nombre": "RagknosDemian", "registro": "224786978"},
]
ASIGNATURA  = "Programacion Internet"
FECHA       = "2026"