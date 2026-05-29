# =============================================================================
# actuadores.py - Control de actuadores del Aula Inteligente
# Relay1 -> Ventilador 12V (Pin 26)
# Servo  -> Ventanas       (Pin 18)
# =============================================================================

from machine import Pin, PWM
import time
from config import (PIN_RELAY1, PIN_SERVO,
                    SERVO_FREQ, SERVO_CERRADO, SERVO_ABIERTO)


class ControladorActuadores:
    """
    Gestiona todos los actuadores del sistema:
    ventilador via Relay1, ventanas via servo motor.
    """

    def __init__(self):
        # Relay1: HIGH = apagado, LOW = encendido (logica invertida del modulo)
        self._relay1 = Pin(PIN_RELAY1, Pin.OUT, value=1)

        # Servo PWM
        self._servo_pwm  = PWM(Pin(PIN_SERVO), freq=SERVO_FREQ)
        self._servo_pwm.duty_u16(SERVO_CERRADO)

        # Estado interno del sistema
        self._ventilador_on = False
        self._ventanas_open = False
        self._paro_activo   = False

    # ------------------------------------------------------------------
    # Ventilador (Relay 1)
    # ------------------------------------------------------------------

    def activar_ventilador(self) -> bool:
        """
        Enciende el ventilador via Relay1.
        Retorna False si el paro de emergencia esta activo.
        """
        if self._paro_activo:
            print("[ACTUADOR] Paro de emergencia activo. No se puede activar ventilador.")
            return False
        self._relay1.value(0)
        self._ventilador_on = True
        print("[ACTUADOR] Ventilador ENCENDIDO")
        return True

    def apagar_ventilador(self):
        """Apaga el ventilador."""
        self._apagar_relay1()
        print("[ACTUADOR] Ventilador APAGADO")

    def _apagar_relay1(self):
        self._relay1.value(1)
        self._ventilador_on = False

    # ------------------------------------------------------------------
    # Ventanas (Servo Motor)
    # ------------------------------------------------------------------

    def abrir_ventanas(self) -> bool:
        """Mueve el servo a posicion abierta (180 grados)."""
        if self._paro_activo:
            print("[ACTUADOR] Paro de emergencia activo. No se puede mover servo.")
            return False
        self._servo_pwm.duty_u16(SERVO_ABIERTO)
        self._ventanas_open = True
        print("[ACTUADOR] Ventanas ABIERTAS (servo 180)")
        return True

    def cerrar_ventanas(self):
        """Mueve el servo a posicion cerrada (0 grados)."""
        self._servo_pwm.duty_u16(SERVO_CERRADO)
        self._ventanas_open = False
        print("[ACTUADOR] Ventanas CERRADAS (servo 0)")

    # ------------------------------------------------------------------
    # Paro de emergencia
    # ------------------------------------------------------------------

    def paro_emergencia(self):
        """
        PARO DE EMERGENCIA: apaga absolutamente todo de forma inmediata.
        Relay1 y servo. El sistema queda bloqueado hasta que se llame a
        reiniciar_circuito().
        """
        self._apagar_relay1()
        self._servo_pwm.duty_u16(SERVO_CERRADO)
        self._ventanas_open = False
        self._paro_activo   = True
        print("[EMERGENCIA] PARO DE EMERGENCIA ACTIVADO - TODO APAGADO")

    def reiniciar_circuito(self):
        """
        Reinicia el circuito: apaga todo y desactiva el bloqueo de paro.
        Equivalente a volver al estado inicial seguro.
        """
        self._apagar_relay1()
        self._servo_pwm.duty_u16(SERVO_CERRADO)
        self._ventanas_open = False
        self._paro_activo   = False
        print("[CIRCUITO] Reinicio completo. Sistema listo.")

    # ------------------------------------------------------------------
    # Consulta de estado
    # ------------------------------------------------------------------

    def estado(self) -> dict:
        """Retorna el estado actual de todos los actuadores."""
        return {
            "ventilador": self._ventilador_on,
            "ventanas":   self._ventanas_open,
            "paro":       self._paro_activo
        }