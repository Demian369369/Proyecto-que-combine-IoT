# =============================================================================
# historial.py - Historial de escaneos FIFO con datos expandidos
# Almacena hasta MAX_HISTORIAL escaneos reales.
# Al agregar el undecimo registro, el primero se elimina automaticamente.
# =============================================================================

import json
import time
from config import MAX_HISTORIAL


class HistorialEscaneos:
    """
    Cola FIFO de registros de escaneo ambiental con todos los campos expandidos.
    """

    def __init__(self):
        self._registros = []

    def agregar(self, temperatura, humedad, indice_calor, punto_rocio, confort,
                valor_adc, voltaje_v, desviacion_adc,
                porcentaje_gas, saturacion, ppm_co2,
                condicion_gas, nivel_riesgo, recomendacion, alarma_gas):
        """
        Agrega un registro completo al historial FIFO.

        Parametros DHT11:
          temperatura   : float  - grados Celsius
          humedad       : float  - % HR
          indice_calor  : float  - sensacion termica en C
          punto_rocio   : float  - punto de rocio en C
          confort       : str    - descripcion de confort termico

        Parametros MQ-135:
          valor_adc     : int    - lectura cruda 0-4095
          voltaje_v     : float  - voltaje real en el pin (V)
          desviacion_adc: int    - desviacion estandar de las muestras
          porcentaje_gas: int    - calidad del aire 0-100 %
          saturacion    : int    - saturacion del sensor 0-100 %
          ppm_co2       : int    - estimacion de CO2 en ppm
          condicion_gas : str    - descripcion textual
          nivel_riesgo  : int    - nivel 1-5
          recomendacion : str    - accion sugerida
          alarma_gas    : bool   - True si DO indica alarma hardware
        """
        marca = time.ticks_ms() // 1000

        registro = {
            # Marca de tiempo
            "seg_boot":       marca,
            # DHT11
            "temperatura":    temperatura,
            "humedad":        humedad,
            "indice_calor":   indice_calor,
            "punto_rocio":    punto_rocio,
            "confort":        confort,
            # MQ-135
            "gas_adc":        valor_adc,
            "gas_voltaje":    voltaje_v,
            "gas_desviacion": desviacion_adc,
            "gas_pct":        porcentaje_gas,
            "gas_saturacion": saturacion,
            "gas_ppm_co2":    ppm_co2,
            "gas_condicion":  condicion_gas,
            "gas_riesgo":     nivel_riesgo,
            "gas_recomenda":  recomendacion,
            "gas_alarma":     alarma_gas
        }

        if len(self._registros) >= MAX_HISTORIAL:
            eliminado = self._registros.pop(0)
            print("[HISTORIAL] FIFO: registro mas antiguo eliminado (seg_boot={})".format(
                eliminado["seg_boot"]))

        self._registros.append(registro)
        print("[HISTORIAL] Registro agregado. Total: {}/{}".format(
            len(self._registros), MAX_HISTORIAL))

    def obtener_todos(self) -> list:
        """Retorna copia de todos los registros en orden cronologico."""
        return list(self._registros)

    def a_json(self) -> str:
        """Serializa el historial completo a cadena JSON."""
        return json.dumps(self._registros)

    def total(self) -> int:
        return len(self._registros)

    def limpiar(self):
        self._registros = []
        print("[HISTORIAL] Historial vaciado.")