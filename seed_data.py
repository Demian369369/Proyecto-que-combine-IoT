"""
Genera datos simulados del DHT11 para pruebas locales.
Ejecutar con el servidor Flask corriendo:
    python seed_data.py
"""

import random
import time
import math
import requests

BASE_URL  = "http://localhost:5000/api/ingest"
DEVICE_ID = "ESP32-DHT11-001"
N_RECORDS = 200      # cantidad de lecturas a generar
SLEEP_SEC = 0.05     # pausa entre cada POST


def compute_heat_index(t, h):
    if t < 27 or h < 40:
        return t
    hi = (-8.78469475556 + 1.61139411*t + 2.33854883889*h
          - 0.14611605*t*h - 0.012308094*t*t - 0.016424828*h*h
          + 0.002211732*t*t*h + 0.00072546*t*h*h - 0.000003582*t*t*h*h)
    return round(hi, 2)


def classify(t, h):
    if t < 18: return "frio"
    if t > 35: return "calor_extremo"
    if h > 80: return "humedad_alta"
    if h < 30: return "seco"
    if 18 <= t <= 26 and 40 <= h <= 60: return "confortable"
    return "moderado"


print(f"Enviando {N_RECORDS} lecturas simuladas...")

base_temp = 22.0
base_hum  = 55.0

for i in range(N_RECORDS):
    # Onda sinusoidal con ruido para simular ciclos reales
    noise_t = random.gauss(0, 0.5)
    noise_h = random.gauss(0, 1.5)
    t = round(base_temp + 4 * math.sin(i * 0.12) + noise_t, 1)
    h = round(base_hum  + 8 * math.cos(i * 0.08) + noise_h, 1)
    t = max(15.0, min(45.0, t))
    h = max(10.0, min(99.0, h))

    payload = {
        "device_id":   DEVICE_ID,
        "temperature": t,
        "humidity":    h,
        "heat_index":  compute_heat_index(t, h),
        "comfort":     classify(t, h),
    }

    try:
        r = requests.post(BASE_URL, json=payload, timeout=5)
        if r.status_code == 200:
            print(f"[{i+1:>3}/{N_RECORDS}] T={t} H={h}")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except requests.exceptions.ConnectionError:
        print("Error: asegurate de que el servidor Flask esta corriendo en localhost:5000")
        break

    time.sleep(SLEEP_SEC)

print("Datos de prueba generados correctamente.")
