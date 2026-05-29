# =============================================================================
# sensores.py - Lectura de sensores ambientales - DATOS EXPANDIDOS
# DHT11 : temperatura, humedad, indice de calor, punto de rocio
# MQ-135: calidad del aire, voltaje ADC, estimacion ppm CO2, nivel de riesgo,
#         recomendacion de ventilacion, porcentaje de saturacion
# Todos los valores retornados son REALES leidos del hardware.
# =============================================================================

import dht
from machine import Pin, ADC
import time
from config import PIN_DHT11, PIN_MQ135_A, PIN_MQ135_D


class SensorDHT11:
    """Lee temperatura, humedad e indicadores derivados del sensor DHT11."""

    def __init__(self):
        self.sensor = dht.DHT11(Pin(PIN_DHT11))

    @staticmethod
    def _indice_calor(t, h):
        """
        Calcula el indice de calor (sensacion termica) usando la formula de Steadman
        adaptada para rangos del DHT11 (0-50 C, 20-90 %).
        Para temperaturas < 27 C simplemente retorna la temperatura real.
        """
        if t is None or h is None:
            return None
        if t < 27:
            return t
        # Formula simplificada de Rothfusz (en Celsius)
        ic = (-8.78469475556
              + 1.61139411 * t
              + 2.33854883889 * h
              - 0.14611605 * t * h
              - 0.012308094 * t * t
              - 0.0164248277778 * h * h
              + 0.002211732 * t * t * h
              + 0.00072546 * t * h * h
              - 0.000003582 * t * t * h * h)
        return round(ic, 1)

    @staticmethod
    def _punto_rocio(t, h):
        """
        Calcula el punto de rocio (°C) con la formula de Magnus simplificada.
        Valido para 0-60 C y 1-100 % HR.
        """
        if t is None or h is None:
            return None
        if h <= 0:
            return None
        # Constantes Magnus para agua liquida
        a = 17.625
        b = 243.04
        # ln(h/100) aproximado con serie de Taylor de 2 terminos para MicroPython
        # (no hay math.log en todos los puertos; usamos aproximacion segura)
        # Alternativa: importar math si esta disponible
        try:
            import math
            alpha = (a * t / (b + t)) + math.log(h / 100.0)
        except Exception:
            # Aproximacion sin math.log: ln(x) ~ 2*(x-1)/(x+1) para x~1
            x = h / 100.0
            alpha = (a * t / (b + t)) + 2.0 * (x - 1.0) / (x + 1.0)
        pr = (b * alpha) / (a - alpha)
        return round(pr, 1)

    @staticmethod
    def _confort_termico(t, h):
        """Retorna descripcion del confort termico segun temperatura y humedad."""
        if t is None or h is None:
            return "Desconocido"
        if t < 16:
            return "Muy frio"
        if t < 20:
            return "Frio"
        if t <= 26 and 40 <= h <= 70:
            return "Confortable"
        if t <= 26 and h < 40:
            return "Seco"
        if t <= 26 and h > 70:
            return "Humedo"
        if t <= 30:
            return "Calido"
        return "Muy calido"

    def leer(self) -> dict:
        """
        Realiza una lectura completa del DHT11.
        Retorna dict con temperatura, humedad, indice de calor,
        punto de rocio, confort termico y flag de error.
        """
        try:
            self.sensor.measure()
            time.sleep_ms(200)
            t = self.sensor.temperature()
            h = self.sensor.humidity()
            ic = self._indice_calor(t, h)
            pr = self._punto_rocio(t, h)
            cf = self._confort_termico(t, h)
            return {
                "temperatura":    t,
                "humedad":        h,
                "indice_calor":   ic,
                "punto_rocio":    pr,
                "confort":        cf,
                "error":          False
            }
        except Exception as e:
            print("[DHT11] Error de lectura:", e)
            return {
                "temperatura":    None,
                "humedad":        None,
                "indice_calor":   None,
                "punto_rocio":    None,
                "confort":        "Error",
                "error":          True
            }


class SensorMQ135:
    """
    Lee la calidad del aire del sensor MQ-135 con datos expandidos:
    - Lectura cruda ADC 0-4095 (12 bits)
    - Voltaje real en el pin (0.0 - 3.3 V)
    - Porcentaje de calidad del aire (100 = limpio)
    - Porcentaje de saturacion del sensor (0 = limpio, 100 = saturado)
    - Estimacion de ppm de CO2 equivalente (basada en curva tipica del MQ-135)
    - Condicion textual (5 niveles)
    - Nivel de riesgo numerico 1-5
    - Recomendacion de ventilacion
    - Alarma hardware (DO del modulo)
    """

    # Referencia de voltaje del ADC de la ESP32 con atenuacion 11dB
    VREF = 3.3

    # Puntos de calibracion aproximados MQ-135 en aire limpio (Rs/Ro ~ 3.6)
    # Curva CO2 del datasheet: ppm = a * (Rs/Ro)^b, donde a=116.602, b=-2.769
    # Para simplificar sin flotantes pesados usamos tabla de interpolacion lineal
    # entre valores ADC y ppm representativos medidos en condiciones normales.
    # NOTA: sin calibracion con gas patron estos valores son estimados tipicos.
    _PPM_TABLA = [
        (0,    350),    # ADC 0     -> ~350 ppm CO2 (aire exterior limpio)
        (500,  400),    # ADC 500   -> ~400 ppm
        (1000, 600),    # ADC 1000  -> ~600 ppm
        (1500, 900),    # ADC 1500  -> ~900 ppm
        (2000, 1400),   # ADC 2000  -> ~1400 ppm
        (2500, 2200),   # ADC 2500  -> ~2200 ppm
        (3000, 3500),   # ADC 3000  -> ~3500 ppm
        (3500, 5500),   # ADC 3500  -> ~5500 ppm
        (4095, 9000),   # ADC 4095  -> ~9000 ppm (saturacion)
    ]

    def __init__(self):
        self.adc = ADC(Pin(PIN_MQ135_A))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        self.pin_digital = Pin(PIN_MQ135_D, Pin.IN)

    @staticmethod
    def _interpolar_ppm(valor_adc, tabla):
        """Interpolacion lineal entre puntos de la tabla ADC -> ppm."""
        if valor_adc <= tabla[0][0]:
            return tabla[0][1]
        for i in range(1, len(tabla)):
            x0, y0 = tabla[i - 1]
            x1, y1 = tabla[i]
            if valor_adc <= x1:
                t = (valor_adc - x0) / (x1 - x0)
                return int(y0 + t * (y1 - y0))
        return tabla[-1][1]

    @staticmethod
    def _recomendacion(valor_adc, alarma):
        """Genera recomendacion de ventilacion segun lectura."""
        if alarma or valor_adc >= 3200:
            return "Evacuar y ventilar urgente"
        if valor_adc >= 2500:
            return "Abrir ventanas inmediatamente"
        if valor_adc >= 2000:
            return "Ventilar el aula"
        if valor_adc >= 1000:
            return "Ventilacion moderada recomendada"
        return "Aire en buen estado"

    def leer(self) -> dict:
        """
        Realiza una lectura expandida del MQ-135.
        Retorna dict con todos los indicadores calculados.
        """
        try:
            muestras = []
            for _ in range(10):   # 10 muestras para mayor precision
                muestras.append(self.adc.read())
                time.sleep_ms(10)
            # Media y desviacion estandar simple
            valor = sum(muestras) // len(muestras)
            # Desviacion estandar (sin math.sqrt: usamos aproximacion Newton)
            media = valor
            var = sum((m - media) ** 2 for m in muestras) // len(muestras)
            # Raiz entera de la varianza
            if var > 0:
                s = var
                for _ in range(20):
                    s = (s + var // s) // 2
                desviacion = s
            else:
                desviacion = 0

            alarma = not self.pin_digital.value()

            # Voltaje real en el pin
            voltaje = round((valor / 4095.0) * self.VREF, 3)

            # Porcentaje de calidad del aire (100 = limpio)
            porcentaje = max(0, min(100, int((1 - valor / 4095.0) * 100)))

            # Porcentaje de saturacion del sensor (0 = limpio, 100 = saturado)
            saturacion = 100 - porcentaje

            # Estimacion de ppm CO2 equivalente
            ppm_co2 = self._interpolar_ppm(valor, self._PPM_TABLA)

            # Condicion y nivel de riesgo
            if valor < 1000:
                condicion    = "Optimo"
                nivel_riesgo = 1
            elif valor < 2000:
                condicion    = "Aceptable"
                nivel_riesgo = 2
            elif valor < 2500:
                condicion    = "Regular"
                nivel_riesgo = 3
            elif valor < 3200:
                condicion    = "Deficiente"
                nivel_riesgo = 4
            else:
                condicion    = "Peligroso"
                nivel_riesgo = 5

            recomendacion = self._recomendacion(valor, alarma)

            return {
                "valor_adc":      valor,
                "voltaje_v":      voltaje,
                "desviacion_adc": desviacion,
                "porcentaje":     porcentaje,
                "saturacion":     saturacion,
                "ppm_co2":        ppm_co2,
                "alarma_hw":      alarma,
                "condicion":      condicion,
                "nivel_riesgo":   nivel_riesgo,
                "recomendacion":  recomendacion,
                "error":          False
            }
        except Exception as e:
            print("[MQ135] Error de lectura:", e)
            return {
                "valor_adc":      None,
                "voltaje_v":      None,
                "desviacion_adc": None,
                "porcentaje":     None,
                "saturacion":     None,
                "ppm_co2":        None,
                "alarma_hw":      False,
                "condicion":      "Error",
                "nivel_riesgo":   0,
                "recomendacion":  "Error de sensor",
                "error":          True
            }