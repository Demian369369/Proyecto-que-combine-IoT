# =============================================================================
# sistema.py - Nucleo del Aula Inteligente (datos expandidos + JSON IA)
# =============================================================================

import time
import gc
from machine import I2C, Pin

from config import (
    PIN_LCD_SDA, PIN_LCD_SCL, LCD_ADDR,
    TEMP_MAX_VENTILADOR, UMBRAL_GAS_PELIGROSO,
    INTERVALO_ESCANEO, EQUIPO, ASIGNATURA, FECHA
)
from lcd_i2c    import LCD
from sensores   import SensorDHT11, SensorMQ135
from actuadores import ControladorActuadores
from historial  import HistorialEscaneos
from json_ia    import generar_y_guardar


class SistemaAula:

    def __init__(self):
        i2c = I2C(0, sda=Pin(PIN_LCD_SDA), scl=Pin(PIN_LCD_SCL), freq=400000)
        self.lcd = LCD(i2c, LCD_ADDR)

        self.dht11      = SensorDHT11()
        self.mq135      = SensorMQ135()
        self.actuadores = ControladorActuadores()
        self.historial  = HistorialEscaneos()

        self.modo_actual        = "manual"
        self.ultimo_escaneo     = {}
        self.tiempo_ultimo_scan = 0

        self.lcd.mostrar_lineas("Aula Inteligente", "Iniciando...")
        time.sleep(1)

    # ------------------------------------------------------------------
    # Escaneo de sensores
    # ------------------------------------------------------------------

    def ejecutar_escaneo(self) -> dict:
        """Lee todos los sensores, registra en FIFO, genera JSON IA y retorna datos."""
        print("\n[ESCANEO] Iniciando lectura de sensores...")

        ld = self.dht11.leer()
        lg = self.mq135.leer()

        temp      = ld["temperatura"]
        hum       = ld["humedad"]
        ic        = ld["indice_calor"]
        pr        = ld["punto_rocio"]
        confort   = ld["confort"]

        gas_adc   = lg["valor_adc"]
        gas_v     = lg["voltaje_v"]
        gas_desv  = lg["desviacion_adc"]
        gas_pct   = lg["porcentaje"]
        gas_sat   = lg["saturacion"]
        gas_ppm   = lg["ppm_co2"]
        gas_cond  = lg["condicion"]
        gas_riesgo= lg["nivel_riesgo"]
        gas_rec   = lg["recomendacion"]
        gas_alarma= lg["alarma_hw"]

        # Terminal
        print("[DHT11] Temp:{} C  Hum:{} %  IC:{} C  PR:{} C  Confort:{}".format(
            temp, hum, ic, pr, confort))
        print("[MQ135] ADC:{}  V:{}  Desv:{}  Calidad:{} %  Sat:{} %  PPM:{}"
              "  Cond:{}  Riesgo:{}  Alarma:{}".format(
            gas_adc, gas_v, gas_desv, gas_pct, gas_sat, gas_ppm,
            gas_cond, gas_riesgo, "SI" if gas_alarma else "No"))
        print("[MQ135] Recomendacion:", gas_rec)

        # LCD
        linea1 = "T:{} IC:{} C".format(
            "{}C".format(temp) if temp is not None else "Err",
            ic if ic is not None else "--"
        )
        linea2 = "CO2:{}ppm {}".format(
            gas_ppm if gas_ppm is not None else "--",
            gas_cond[:5] if gas_cond else "???"
        )
        self.lcd.mostrar_lineas(linea1, linea2)

        resultado = {
            "temperatura":    temp,
            "humedad":        hum,
            "indice_calor":   ic,
            "punto_rocio":    pr,
            "confort":        confort,
            "gas_adc":        gas_adc,
            "gas_voltaje":    gas_v,
            "gas_desviacion": gas_desv,
            "gas_pct":        gas_pct,
            "gas_saturacion": gas_sat,
            "gas_ppm_co2":    gas_ppm,
            "gas_condicion":  gas_cond,
            "gas_riesgo":     gas_riesgo,
            "gas_recomenda":  gas_rec,
            "gas_alarma":     gas_alarma
        }
        self.ultimo_escaneo = resultado

        # Registrar en FIFO si al menos un sensor funciona
        if not ld["error"] or not lg["error"]:
            self.historial.agregar(
                temp, hum, ic, pr, confort,
                gas_adc, gas_v, gas_desv,
                gas_pct, gas_sat, gas_ppm,
                gas_cond, gas_riesgo, gas_rec, gas_alarma
            )

        # Escribir JSON IA (reemplaza el archivo anterior)
        self._escribir_json_ia()

        gc.collect()
        return resultado

    def _escribir_json_ia(self):
        """Llama al generador de JSON IA con el estado actual del sistema."""
        try:
            seg = time.ticks_ms() // 1000
            generar_y_guardar(
                escaneo          = self.ultimo_escaneo,
                estado_actuadores= self.actuadores.estado(),
                modo             = self.modo_actual,
                seg_boot         = seg,
                equipo           = EQUIPO,
                asignatura       = ASIGNATURA,
                fecha            = FECHA
            )
        except Exception as e:
            print("[SISTEMA] Error al generar JSON IA:", e)

    def ejecutar_escaneo_automatico(self) -> dict:
        resultado = self.ejecutar_escaneo()

        temp       = resultado["temperatura"]
        gas_adc    = resultado["gas_adc"]
        gas_alarma = resultado["gas_alarma"]

        if self.actuadores.estado()["paro"]:
            print("[AUTO] Paro activo. Logica automatica suspendida.")
            resultado.update(self.actuadores.estado())
            return resultado

        if temp is not None:
            if temp > TEMP_MAX_VENTILADOR:
                self.actuadores.activar_ventilador()
                self.lcd.mostrar_lineas("MODO AUTO", "Ventilador ON")
            else:
                if self.actuadores.estado()["ventilador"]:
                    self.actuadores.apagar_ventilador()

        if (gas_adc is not None and gas_adc > UMBRAL_GAS_PELIGROSO) or gas_alarma:
            self.actuadores.abrir_ventanas()
            self.lcd.mostrar_lineas("ALERTA GASES", "Ventanas abiertas")
        else:
            if self.actuadores.estado()["ventanas"]:
                self.actuadores.cerrar_ventanas()

        # Actualizar JSON IA con el nuevo estado de actuadores tras la logica auto
        self._escribir_json_ia()

        time.sleep_ms(500)
        est = self.actuadores.estado()
        estado_str = "Vent ON" if est["ventilador"] else "Normal"
        self.lcd.mostrar_lineas(
            "AUTO " + estado_str,
            "T:{} H:{}%".format(
                resultado["temperatura"] if resultado["temperatura"] is not None else "--",
                resultado["humedad"]     if resultado["humedad"]     is not None else "--"
            )
        )

        resultado.update(self.actuadores.estado())
        self.tiempo_ultimo_scan = time.ticks_ms()
        return resultado

    # ------------------------------------------------------------------
    def cambiar_modo(self, nuevo_modo: str):
        self.modo_actual = nuevo_modo
        if nuevo_modo == "automatico":
            self.lcd.mostrar_lineas("MODO AUTOMATICO", "Escaneo activo")
            print("[SISTEMA] Modo: AUTOMATICO")
        else:
            self.lcd.mostrar_lineas("MODO MANUAL", "Control web")
            print("[SISTEMA] Modo: MANUAL")

    def obtener_estado_completo(self) -> dict:
        est = self.actuadores.estado()
        u   = self.ultimo_escaneo
        return {
            "modo":           self.modo_actual,
            "ventilador":     est["ventilador"],
            "ventanas":       est["ventanas"],
            "paro":           est["paro"],
            "temperatura":    u.get("temperatura"),
            "humedad":        u.get("humedad"),
            "indice_calor":   u.get("indice_calor"),
            "punto_rocio":    u.get("punto_rocio"),
            "confort":        u.get("confort", "--"),
            "gas_adc":        u.get("gas_adc"),
            "gas_voltaje":    u.get("gas_voltaje"),
            "gas_desviacion": u.get("gas_desviacion"),
            "gas_pct":        u.get("gas_pct"),
            "gas_saturacion": u.get("gas_saturacion"),
            "gas_ppm_co2":    u.get("gas_ppm_co2"),
            "gas_condicion":  u.get("gas_condicion", "--"),
            "gas_riesgo":     u.get("gas_riesgo", 0),
            "gas_recomenda":  u.get("gas_recomenda", "--"),
            "gas_alarma":     u.get("gas_alarma", False),
            "historial":      self.historial.obtener_todos(),
            "equipo":         EQUIPO,
            "asignatura":     ASIGNATURA,
            "fecha":          FECHA
        }

    def tick_automatico(self):
        if self.modo_actual != "automatico":
            return
        ahora = time.ticks_ms()
        if time.ticks_diff(ahora, self.tiempo_ultimo_scan) >= INTERVALO_ESCANEO * 1000:
            self.ejecutar_escaneo_automatico()