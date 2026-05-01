"""
AirSense IoT - ESP32 Firmware
Sensor: DHT11 (GPIO23)
Protocolo: WiFi -> HTTP POST -> Backend Flask
"""

import time
import json
import network
import urequests
from machine import Pin
from dht import DHT11

# ── Configuracion WiFi ──────────────────────────────────────────────────────
WIFI_SSID     = "TU_RED_WIFI"
WIFI_PASSWORD = "TU_CONTRASENA"

# ── Endpoint del backend ────────────────────────────────────────────────────
# Cambia a la IP local de tu servidor o a tu dominio desplegado
BACKEND_URL   = "http://192.168.1.100:5000/api/ingest"
DEVICE_ID     = "ESP32-DHT11-001"

# ── Pin del DHT11 ───────────────────────────────────────────────────────────
DHT_PIN       = 23
READ_INTERVAL = 10        # segundos entre lecturas

# ── LED integrado ───────────────────────────────────────────────────────────
led = Pin(2, Pin.OUT)

sensor = DHT11(Pin(DHT_PIN))


def connect_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Conectando a WiFi...")
        sta.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 15
        while not sta.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".")
    if sta.isconnected():
        print("WiFi OK:", sta.ifconfig()[0])
        return True
    print("Error: no se pudo conectar a WiFi")
    return False


def read_sensor():
    """Lee temperatura y humedad del DHT11. Devuelve dict o None."""
    try:
        sensor.measure()
        return {
            "temperature": sensor.temperature(),
            "humidity": sensor.humidity(),
        }
    except OSError as e:
        print("Error DHT11:", e)
        return None


def compute_heat_index(t, h):
    """
    Indice de calor simplificado (Steadman).
    Solo valido para T >= 27 C y H >= 40%.
    """
    if t < 27 or h < 40:
        return t
    hi = (-8.78469475556
          + 1.61139411   * t
          + 2.33854883889 * h
          - 0.14611605   * t * h
          - 0.012308094  * t * t
          - 0.016424828  * h * h
          + 0.002211732  * t * t * h
          + 0.00072546   * t * h * h
          - 0.000003582  * t * t * h * h)
    return round(hi, 2)


def classify_comfort(t, h):
    """Clasifica el nivel de confort termico/humedad."""
    if t < 18:
        return "frio"
    if t > 35:
        return "calor_extremo"
    if h > 80:
        return "humedad_alta"
    if h < 30:
        return "seco"
    if 18 <= t <= 26 and 40 <= h <= 60:
        return "confortable"
    return "moderado"


def send_payload(data):
    """Envia lectura al backend via HTTP POST."""
    headers = {"Content-Type": "application/json"}
    try:
        r = urequests.post(BACKEND_URL, data=json.dumps(data), headers=headers, timeout=8)
        status = r.status_code
        r.close()
        return status == 200
    except Exception as e:
        print("Error HTTP:", e)
        return False


def blink(times=1, ms=100):
    for _ in range(times):
        led.on()
        time.sleep_ms(ms)
        led.off()
        time.sleep_ms(ms)


# ── Bucle principal ─────────────────────────────────────────────────────────
def main():
    if not connect_wifi():
        # Sin WiFi: parpadeo rapido de error
        while True:
            blink(5, 80)
            time.sleep(5)

    blink(3, 150)       # seal de inicio exitoso

    while True:
        reading = read_sensor()
        if reading is None:
            blink(2, 500)
            time.sleep(READ_INTERVAL)
            continue

        t = reading["temperature"]
        h = reading["humidity"]
        hi = compute_heat_index(t, h)
        comfort = classify_comfort(t, h)

        payload = {
            "device_id":   DEVICE_ID,
            "temperature": t,
            "humidity":    h,
            "heat_index":  hi,
            "comfort":     comfort,
            "timestamp":   None,   # el backend asigna el timestamp UTC real
        }

        print(f"T={t}C  H={h}%  HI={hi}  comfort={comfort}")

        ok = send_payload(payload)
        if ok:
            blink(1, 100)
        else:
            blink(3, 200)

        time.sleep(READ_INTERVAL)


main()
