# =============================================================================
# json_ia.py - Generador de JSON de analisis para IA
# Escribe un unico archivo "datos_ia.json" en la ESP32.
# Cada escaneo REEMPLAZA el archivo anterior para no consumir memoria.
# El contenido esta redactado en espanol descriptivo para que una IA
# pueda analizar el estado del aula sin preprocesamiento adicional.
# Formato inspirado en Parquet: esquema fijo, un solo registro por archivo.
# =============================================================================

import json


# Ruta del archivo en el sistema de archivos de la ESP32 (LittleFS / SPIFFS)
RUTA_JSON_IA = "/datos_ia.json"


# ---------------------------------------------------------------------------
# Textos descriptivos en espanol para cada campo
# ---------------------------------------------------------------------------

def _desc_confort(confort):
    tabla = {
        "Confortable": "Las condiciones de temperatura y humedad son optimas para el trabajo academico.",
        "Seco":        "El ambiente esta seco. Puede causar incomodidad en mucosa y ojos.",
        "Humedo":      "El ambiente es demasiado humedo. Puede favorecer moho y sensacion de calor.",
        "Frio":        "La temperatura es baja. Se recomienda calefaccion o abrigar a los ocupantes.",
        "Muy frio":    "La temperatura es muy baja. Condicion inadecuada para el aprendizaje.",
        "Calido":      "El ambiente es calido. Se recomienda ventilacion para mejorar el confort.",
        "Muy calido":  "La temperatura es muy alta. El calor puede afectar la concentracion y salud.",
        "Desconocido": "No se pudo determinar el nivel de confort termico.",
        "Error":       "Error en la lectura del sensor de temperatura y humedad."
    }
    return tabla.get(confort, "Condicion no clasificada.")


def _desc_calidad_aire(condicion, ppm):
    if condicion == "Optimo":
        return ("El aire del aula esta en condicion optima. "
                "La concentracion de gases es muy baja y no representa ningun riesgo.")
    if condicion == "Aceptable":
        return ("La calidad del aire es aceptable. "
                "Los niveles de gases son normales para un aula en uso.")
    if condicion == "Regular":
        return ("La calidad del aire es regular. "
                "Se recomienda ventilar el aula abriendo ventanas o activando el ventilador.")
    if condicion == "Deficiente":
        return ("La calidad del aire es deficiente. "
                "La concentracion de gases es alta. "
                "Es necesario ventilar el aula de forma inmediata para proteger la salud de los ocupantes.")
    if condicion == "Peligroso":
        return ("La calidad del aire es PELIGROSA. "
                "La concentracion de gases supera los limites seguros. "
                "Se debe evacuar el aula y ventilar urgentemente.")
    return "No se pudo determinar la calidad del aire."


def _desc_co2(ppm):
    if ppm is None:
        return "No se pudo estimar la concentracion de CO2."
    if ppm < 400:
        return ("Concentracion de CO2 muy baja ({} ppm). "
                "Equivalente al aire exterior limpio. Excelente.").format(ppm)
    if ppm < 700:
        return ("Concentracion de CO2 normal ({} ppm). "
                "Rango tipico de un aula bien ventilada.").format(ppm)
    if ppm < 1000:
        return ("Concentracion de CO2 moderada ({} ppm). "
                "Aun dentro del limite recomendado (1000 ppm) pero se acerca al techo.").format(ppm)
    if ppm < 2000:
        return ("Concentracion de CO2 elevada ({} ppm). "
                "Supera el limite recomendado de 1000 ppm. "
                "Puede causar cansancio, falta de concentracion y dolor de cabeza.").format(ppm)
    return ("Concentracion de CO2 muy alta ({} ppm). "
            "Nivel potencialmente danino. Ventilacion urgente requerida.").format(ppm)


def _desc_indice_calor(ic, temp):
    if ic is None or temp is None:
        return "No se pudo calcular el indice de calor."
    diff = ic - temp
    if diff <= 1:
        return ("El indice de calor ({} C) es practicamente igual a la temperatura real. "
                "La humedad no agrava la sensacion termica.").format(ic)
    if diff <= 3:
        return ("El indice de calor ({} C) es ligeramente superior a la temperatura real ({} C). "
                "La humedad agrega una sensacion de calor moderada.").format(ic, temp)
    return ("El indice de calor ({} C) es notablemente mayor que la temperatura real ({} C). "
            "La humedad amplifica significativamente la sensacion de calor. "
            "Se recomienda ventilacion activa.").format(ic, temp)


def _desc_punto_rocio(pr, temp):
    if pr is None or temp is None:
        return "No se pudo calcular el punto de rocio."
    margen = temp - pr
    if margen < 3:
        return ("El punto de rocio ({} C) esta muy cerca de la temperatura actual ({} C). "
                "Existe riesgo de condensacion en superficies. "
                "Humedad relativa muy alta.").format(pr, temp)
    if margen < 8:
        return ("El punto de rocio es de {} C con temperatura actual de {} C. "
                "Margen moderado, sin riesgo inmediato de condensacion.").format(pr, temp)
    return ("El punto de rocio ({} C) esta bien por debajo de la temperatura actual ({} C). "
            "No hay riesgo de condensacion.").format(pr, temp)


def _desc_alarma(alarma):
    if alarma:
        return ("La salida digital DO del sensor MQ-135 esta ACTIVA. "
                "El modulo hardware detecto que la concentracion de gases supera "
                "el umbral configurado en su potenciometro. "
                "Accion inmediata requerida.")
    return ("La salida digital DO del sensor MQ-135 esta en estado normal. "
            "La concentracion de gases no supera el umbral hardware del modulo.")


def _desc_ventilador(encendido, paro):
    if paro:
        return "El ventilador esta detenido por PARO DE EMERGENCIA."
    if encendido:
        return ("El ventilador de 12V esta ENCENDIDO. "
                "El relay 1 (pin 26) conduce corriente al motor DC. "
                "Se esta renovando el aire del aula activamente.")
    return ("El ventilador esta APAGADO. "
            "El relay 1 (pin 26) esta en estado de reposo (circuito abierto).")


def _desc_ventanas(abiertas, paro):
    if paro:
        return "Las ventanas estan cerradas por PARO DE EMERGENCIA."
    if abiertas:
        return ("Las ventanas estan ABIERTAS. "
                "El servo motor SG90 (pin 18) se posiciono a 30 grados. "
                "Se permite la entrada de aire exterior para ventilar el aula.")
    return ("Las ventanas estan CERRADAS. "
            "El servo motor SG90 (pin 18) esta en posicion de reposo (0 grados).")


def _desc_modo(modo):
    if modo == "automatico":
        return ("El sistema opera en MODO AUTOMATICO. "
                "Los actuadores se controlan solos segun los datos de los sensores: "
                "ventilador encendido si temperatura supera 28 C, "
                "ventanas abiertas si el ADC del MQ-135 supera 2500 o la alarma DO esta activa.")
    return ("El sistema opera en MODO MANUAL. "
            "Los actuadores son controlados directamente por el usuario desde la interfaz web.")


def _desc_riesgo_global(nivel_riesgo, gas_alarma, temp, hum):
    """Genera una evaluacion global del estado del aula."""
    problemas = []
    if nivel_riesgo >= 4:
        problemas.append("calidad del aire deficiente o peligrosa")
    if gas_alarma:
        problemas.append("alarma hardware de gases activa")
    if temp is not None and temp > 28:
        problemas.append("temperatura por encima del limite de confort (28 C)")
    if hum is not None and hum > 80:
        problemas.append("humedad relativa muy alta (mayor a 80%)")
    if hum is not None and hum < 25:
        problemas.append("humedad relativa muy baja (menor a 25%)")

    if not problemas:
        return ("ESTADO GENERAL: NORMAL. "
                "Todos los parametros ambientales del aula estan dentro de rangos aceptables. "
                "No se requiere ninguna accion.")
    return ("ESTADO GENERAL: ATENCION REQUERIDA. "
            "Se detectaron los siguientes problemas: {}. "
            "Revisar actuadores y considerar intervencion manual o automatica.").format(
        ", ".join(problemas))


# ---------------------------------------------------------------------------
# Generador principal del JSON de IA
# ---------------------------------------------------------------------------

def generar_y_guardar(escaneo: dict, estado_actuadores: dict, modo: str,
                      seg_boot: int, equipo: list, asignatura: str, fecha: str):
    """
    Genera el JSON de analisis IA y lo escribe en RUTA_JSON_IA,
    reemplazando cualquier version anterior.

    Parametros:
      escaneo           : dict con todos los campos del ultimo escaneo
      estado_actuadores : dict con ventilador, ventanas, paro
      modo              : 'manual' o 'automatico'
      seg_boot          : segundos desde el inicio del sistema
      equipo            : lista de dicts con nombre y registro
      asignatura        : nombre de la asignatura
      fecha             : fecha de entrega
    """

    t    = escaneo.get("temperatura")
    h    = escaneo.get("humedad")
    ic   = escaneo.get("indice_calor")
    pr   = escaneo.get("punto_rocio")
    cf   = escaneo.get("confort", "Desconocido")

    adc  = escaneo.get("gas_adc")
    volt = escaneo.get("gas_voltaje")
    desv = escaneo.get("gas_desviacion")
    pct  = escaneo.get("gas_pct")
    sat  = escaneo.get("gas_saturacion")
    ppm  = escaneo.get("gas_ppm_co2")
    cond = escaneo.get("gas_condicion", "Desconocido")
    ries = escaneo.get("gas_riesgo", 0)
    rec  = escaneo.get("gas_recomenda", "--")
    alar = escaneo.get("gas_alarma", False)

    vent = estado_actuadores.get("ventilador", False)
    vnt  = estado_actuadores.get("ventanas",   False)
    paro = estado_actuadores.get("paro",       False)

    # Nombres del equipo como cadena
    integrantes = ", ".join(
        m.get("nombre", "") + " (" + m.get("registro", "") + ")"
        for m in (equipo or [])
    )

    documento = {
        "descripcion_documento": (
            "Este documento JSON contiene los datos del ultimo escaneo ambiental "
            "del sistema Aula Inteligente basado en ESP32. "
            "Esta redactado en espanol para ser analizado directamente por una inteligencia artificial. "
            "Cada campo incluye el valor numerico real y una descripcion textual de su significado."
        ),
        "proyecto": {
            "nombre":     "Aula Inteligente - Control de Temperatura y Ventilacion",
            "asignatura": asignatura,
            "integrantes": integrantes,
            "fecha":      fecha,
            "hardware":   "ESP32 con MicroPython",
            "sensores":   "DHT11 (temperatura y humedad), MQ-135 (calidad del aire)",
            "actuadores": "Ventilador 12V via Relay1 (pin 26), Ventanas via Servo SG90 (pin 18)"
        },
        "marca_tiempo": {
            "segundos_desde_inicio": seg_boot,
            "descripcion": (
                "Segundos transcurridos desde que la ESP32 fue encendida. "
                "No representa fecha real ya que el dispositivo no tiene RTC externo."
            )
        },
        "modo_operacion": {
            "modo":       modo,
            "descripcion": _desc_modo(modo)
        },
        "temperatura_y_humedad": {
            "sensor": "DHT11 conectado al pin 4 de la ESP32",
            "temperatura_celsius": {
                "valor":      t,
                "descripcion": (
                    "Temperatura real del aire en el aula medida por el DHT11. "
                    "Rango del sensor: 0 a 50 grados Celsius. "
                    "El umbral para activar el ventilador automaticamente es 28 C."
                ) if t is not None else "Lectura no disponible por error en el sensor."
            },
            "humedad_relativa_porcentaje": {
                "valor":      h,
                "descripcion": (
                    "Porcentaje de humedad relativa en el aula. "
                    "Rango confortable: 40% a 70%. "
                    "Valor actual: {} %.".format(h)
                ) if h is not None else "Lectura no disponible por error en el sensor."
            },
            "indice_de_calor_celsius": {
                "valor":      ic,
                "descripcion": _desc_indice_calor(ic, t)
            },
            "punto_de_rocio_celsius": {
                "valor":      pr,
                "descripcion": _desc_punto_rocio(pr, t)
            },
            "confort_termico": {
                "clasificacion": cf,
                "descripcion":   _desc_confort(cf)
            }
        },
        "calidad_del_aire": {
            "sensor": "MQ-135 conectado al pin 34 (analogico) y pin 35 (digital) de la ESP32",
            "valor_adc_crudo": {
                "valor":      adc,
                "escala":     "0 a 4095 (ADC de 12 bits)",
                "descripcion": (
                    "Lectura cruda del convertidor analogico-digital de la ESP32. "
                    "Valores altos indican mayor concentracion de gases nocivos. "
                    "Es el promedio de 10 muestras consecutivas para reducir el ruido electrico."
                ) if adc is not None else "Lectura no disponible."
            },
            "voltaje_pin_voltios": {
                "valor":      volt,
                "descripcion": (
                    "Voltaje real medido en el pin analogico del MQ-135. "
                    "Rango: 0.0 a 3.3 V. Voltaje actual: {} V.".format(volt)
                ) if volt is not None else "No disponible."
            },
            "desviacion_estandar_adc": {
                "valor":      desv,
                "descripcion": (
                    "Desviacion estandar calculada sobre las 10 muestras del ADC. "
                    "Un valor bajo indica lectura estable. "
                    "Un valor alto indica ruido electrico o cambios rapidos en la concentracion de gases."
                ) if desv is not None else "No disponible."
            },
            "calidad_aire_porcentaje": {
                "valor":      pct,
                "descripcion": (
                    "Porcentaje de calidad del aire donde 100% es aire completamente limpio "
                    "y 0% es aire totalmente saturado de gases nocivos. "
                    "Calculado como: (1 - ADC/4095) * 100."
                ) if pct is not None else "No disponible."
            },
            "saturacion_sensor_porcentaje": {
                "valor":      sat,
                "descripcion": (
                    "Porcentaje de saturacion del sensor MQ-135. "
                    "0% indica aire limpio, 100% indica sensor completamente saturado de gases. "
                    "Es el complemento del porcentaje de calidad del aire."
                ) if sat is not None else "No disponible."
            },
            "co2_estimado_ppm": {
                "valor":      ppm,
                "unidad":     "partes por millon (ppm)",
                "descripcion": _desc_co2(ppm),
                "nota":       (
                    "Valor estimado mediante interpolacion sobre la curva tipica del MQ-135. "
                    "Para medicion precisa se requiere calibracion con gas patron certificado. "
                    "Sirve como referencia orientativa."
                )
            },
            "condicion_del_aire": {
                "clasificacion": cond,
                "descripcion":   _desc_calidad_aire(cond, ppm)
            },
            "nivel_de_riesgo": {
                "valor":      ries,
                "escala":     "1 (optimo) a 5 (peligroso)",
                "descripcion": (
                    "Nivel {} de 5. {}".format(
                        ries,
                        ["", "Sin riesgo.", "Riesgo bajo.",
                         "Riesgo moderado.", "Riesgo alto.", "Riesgo critico."
                         ][ries] if 1 <= ries <= 5 else "No determinado."
                    )
                )
            },
            "recomendacion_ventilacion": {
                "accion":      rec,
                "descripcion": (
                    "Accion recomendada basada en la lectura actual del MQ-135 "
                    "y el estado de la alarma hardware."
                )
            },
            "alarma_hardware_do": {
                "activa":      alar,
                "descripcion": _desc_alarma(alar)
            }
        },
        "estado_actuadores": {
            "ventilador_12v": {
                "encendido":   vent,
                "descripcion": _desc_ventilador(vent, paro)
            },
            "ventanas_servo": {
                "abiertas":    vnt,
                "descripcion": _desc_ventanas(vnt, paro)
            },
            "paro_de_emergencia": {
                "activo": paro,
                "descripcion": (
                    "PARO DE EMERGENCIA ACTIVO. Todos los actuadores estan deshabilitados "
                    "hasta que el operador presione REINICIAR CIRCUITO."
                ) if paro else (
                    "No hay paro de emergencia activo. "
                    "El sistema opera con normalidad."
                )
            }
        },
        "evaluacion_global": {
            "descripcion": _desc_riesgo_global(ries, alar, t, h)
        },
        "instruccion_para_ia": (
            "Eres un asistente de analisis ambiental. "
            "Analiza los datos de este JSON que corresponden al ultimo escaneo del Aula Inteligente. "
            "Identifica si existen condiciones fuera de rango, evalua el confort de los ocupantes, "
            "determina si los actuadores estan respondiendo correctamente a las condiciones detectadas, "
            "y proporciona recomendaciones concretas en espanol para mejorar el ambiente del aula."
        )
    }

    # Escribir el archivo reemplazando el anterior
    try:
        with open(RUTA_JSON_IA, "w") as f:
            json.dump(documento, f)
        print("[JSON-IA] Archivo escrito correctamente en", RUTA_JSON_IA)
        return True
    except Exception as e:
        print("[JSON-IA] Error al escribir el archivo:", e)
        return False


def leer_json_ia() -> str:
    """
    Lee el contenido del archivo JSON de IA y lo retorna como cadena.
    Retorna None si el archivo no existe o hay error.
    """
    try:
        with open(RUTA_JSON_IA, "r") as f:
            return f.read()
    except Exception as e:
        print("[JSON-IA] Error al leer el archivo:", e)
        return None


def existe_json_ia() -> bool:
    """Retorna True si el archivo JSON de IA existe en el sistema de archivos."""
    try:
        import os
        os.stat(RUTA_JSON_IA)
        return True
    except Exception:
        return False
