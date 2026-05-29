# =============================================================================
# wifi_manager.py - Gestor de conexion WiFi
# Intenta conectarse a cada red de la lista REDES_WIFI en orden.
# Imprime en terminal las redes detectadas y el link de la pagina web.
# =============================================================================

import network
import time
from config import REDES_WIFI, TIEMPO_ESPERA_WIFI


def escanear_redes_disponibles() -> list:
    """
    Escanea las redes WiFi disponibles en el entorno.
    Retorna una lista de dicts con 'ssid', 'rssi' y 'seguridad'.
    """
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    print("\n[WIFI] Escaneando redes disponibles...")
    redes_raw = sta.scan()   # Lista de tuplas (ssid, bssid, canal, rssi, authmode, hidden)
    redes = []
    for r in redes_raw:
        ssid = r[0].decode("utf-8", "ignore").strip()
        if ssid:   # Ignorar redes ocultas sin nombre
            redes.append({
                "ssid":      ssid,
                "rssi":      r[3],
                "seguridad": r[4]   # 0=abierta, 1=WEP, 2-5=WPA
            })
    # Ordenar por intensidad de senal descendente
    redes.sort(key=lambda x: x["rssi"], reverse=True)
    print("[WIFI] Redes detectadas:")
    for i, r in enumerate(redes):
        seg = "Abierta" if r["seguridad"] == 0 else "Protegida"
        print("  {:>2}. {:.<30} {:>4} dBm  ({})".format(
            i + 1, r["ssid"], r["rssi"], seg))
    print()
    return redes


def conectar_wifi() -> tuple:
    """
    Intenta conectarse a las redes configuradas en REDES_WIFI en orden.
    Retorna (True, ip_address) si conecta, (False, None) si falla todo.
    """
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    # Escanear primero para mostrar redes en terminal
    escanear_redes_disponibles()

    for red in REDES_WIFI:
        ssid      = red["ssid"]
        password  = red.get("password") or ""
        print("[WIFI] Intentando conectar a: {}".format(ssid))
        try:
            sta.connect(ssid, password)
        except Exception as e:
            print("[WIFI] Error al intentar conectar:", e)
            continue

        # Esperar hasta TIEMPO_ESPERA_WIFI segundos
        inicio = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), inicio) > TIEMPO_ESPERA_WIFI * 1000:
                print("[WIFI] Tiempo agotado para red: {}".format(ssid))
                sta.disconnect()
                break
            time.sleep(0.5)
            print(".", end="")
        print()

        if sta.isconnected():
            ip = sta.ifconfig()[0]
            print("[WIFI] Conectado a: {}".format(ssid))
            print("[WIFI] Direccion IP: {}".format(ip))
            print("[WIFI] Pagina web disponible en: http://{}".format(ip))
            print("[WIFI] Comparte este link en tu navegador local.")
            return True, ip

    print("[WIFI] No se pudo conectar a ninguna red configurada.")
    print("[WIFI] El sistema operara en MODO AUTOMATICO sin web.")
    return False, None
