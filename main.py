# =============================================================================
# main.py - Punto de entrada del Aula Inteligente
# Flujo:
#   1. Inicializar sistema (LCD, sensores, actuadores)
#   2. Intentar conectar a WiFi
#      -> Exito: modo MANUAL con servidor web activo
#      -> Fallo:  escaneo inicial y modo AUTOMATICO sin web
#   3. Loop principal: atender peticiones HTTP y/o ejecutar ticks automaticos
# =============================================================================

import time
import gc
from sistema      import SistemaAula
from wifi_manager import conectar_wifi
from servidor_http import ServidorHTTP

# =============================================================================
# INICIO
# =============================================================================

print("=" * 50)
print("  AULA INTELIGENTE - CUCEI UDEG")
print("  Programacion Para Internet")
print("=" * 50)

# Inicializar el sistema central
aula = SistemaAula()

# Intentar conexion WiFi
wifi_ok, ip = conectar_wifi()

if wifi_ok:
    # -----------------------------------------------------------
    # MODO MANUAL CON SERVIDOR WEB
    # -----------------------------------------------------------
    aula.cambiar_modo("manual")
    aula.lcd.mostrar_lineas("Modo: MANUAL", "IP:" + ip)

    servidor = ServidorHTTP(aula, puerto=80)
    servidor.iniciar()

    print("\n[MAIN] Sistema listo. Accede desde: http://{}".format(ip))
    print("[MAIN] Loop principal activo. Esperando peticiones...\n")

    while True:
        try:
            # Atender peticiones HTTP (no bloquea mas de 0.5s por timeout)
            servidor.atender_peticion()

            # Si el usuario cambio a modo automatico desde la web,
            # el tick_automatico se encarga del escaneo periodico
            aula.tick_automatico()

            gc.collect()
            time.sleep_ms(10)

        except KeyboardInterrupt:
            print("\n[MAIN] Interrupcion de teclado. Apagando sistema de forma segura.")
            aula.actuadores.paro_emergencia()
            aula.lcd.mostrar_lineas("Sistema", "Detenido")
            break
        except Exception as e:
            print("[MAIN] Error en loop:", e)
            time.sleep(1)

else:
    # -----------------------------------------------------------
    # MODO AUTOMATICO SIN WIFI
    # -----------------------------------------------------------
    print("\n[MAIN] Sin WiFi. Iniciando MODO AUTOMATICO.")
    aula.cambiar_modo("automatico")
    aula.lcd.mostrar_lineas("MODO AUTOMATICO", "Sin WiFi")

    # Escaneo inicial inmediato antes de entrar al loop
    print("[MAIN] Ejecutando escaneo inicial...")
    aula.ejecutar_escaneo_automatico()

    print("[MAIN] Loop automatico activo. Escaneo cada 60 segundos.\n")

    while True:
        try:
            aula.tick_automatico()
            gc.collect()
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[MAIN] Interrupcion. Apagando sistema de forma segura.")
            aula.actuadores.paro_emergencia()
            aula.lcd.mostrar_lineas("Sistema", "Detenido")
            break
        except Exception as e:
            print("[MAIN] Error en loop automatico:", e)
            time.sleep(2)
