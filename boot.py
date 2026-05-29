# =============================================================================
# boot.py - Arranque seguro del sistema Aula Inteligente
# CUCEI - UDEG | Arquitectura de Computadoras
# Proposito: Apagar todos los actuadores al encender la ESP32 para evitar
#            estados peligrosos o indefinidos en el hardware.
# =============================================================================

from machine import Pin, PWM
import time

# --- Pines de actuadores ---
PIN_RELAY1 = 26   # Relay ventilador
PIN_SERVO  = 18   # Servo motor (ventanas)

# Inicializar relay como salida y apagarlo (HIGH = relay desactivado en modulo NC/NO)
relay1 = Pin(PIN_RELAY1, Pin.OUT)

# Los modulos relay tipicos se activan con LOW y desactivan con HIGH
relay1.value(1)

# Inicializar servo y llevarlo a posicion 0 (ventanas cerradas)
# Frecuencia estandar de servo: 50 Hz
servo_pwm = PWM(Pin(PIN_SERVO), freq=50)

# Angulo 0 grados = pulso de 0.5ms en periodo de 20ms
# duty de 16 bit: 0.5ms / 20ms * 65535 = 1638
servo_pwm.duty_u16(1638)
time.sleep(0.5)

# Detener la senal PWM del servo para no mantenerlo bajo tension innecesaria
servo_pwm.deinit()

print("[BOOT] Todos los actuadores apagados de forma segura.")
print("[BOOT] Sistema listo para iniciar main.py")