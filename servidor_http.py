# =============================================================================
# servidor_http.py - Servidor HTTP embebido para la ESP32
# Estrategia de memoria: el HTML se envia por fragmentos directamente al socket.
# Las respuestas JSON se construyen en memoria solo (son pequenas, < 1 KB).
# Nunca se carga el HTML completo en RAM.
# =============================================================================

import socket
import json
import gc


# Tamano del fragmento al enviar HTML (bytes).
# 512 bytes es seguro para la heap de la ESP32 bajo carga.
TAMANO_FRAGMENTO = 512


def _enviar_cabecera_html(cliente, longitud_total: int):
    """Envia la cabecera HTTP para una respuesta HTML de tamano conocido."""
    cab = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n"
    ).format(longitud_total)
    cliente.sendall(cab.encode("utf-8"))


def _enviar_fragmentos(cliente, texto: str):
    """
    Envia una cadena de texto al socket en fragmentos de TAMANO_FRAGMENTO bytes.
    Nunca tiene mas de un fragmento en memoria a la vez.
    """
    datos = texto.encode("utf-8")
    vista = memoryview(datos)
    offset = 0
    total  = len(datos)
    while offset < total:
        fin = min(offset + TAMANO_FRAGMENTO, total)
        cliente.sendall(vista[offset:fin])
        offset = fin


def _respuesta_json(datos: dict) -> bytes:
    """Construye y retorna una respuesta JSON completa (siempre pequena)."""
    cuerpo = json.dumps(datos).encode("utf-8")
    cab = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n"
    ).format(len(cuerpo)).encode("utf-8")
    return cab + cuerpo


def _respuesta_texto(codigo: int, texto: str) -> bytes:
    """Respuesta de texto plano pequena (errores, 404, etc.)."""
    cuerpo = texto.encode("utf-8")
    cab = (
        "HTTP/1.1 {} OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n"
    ).format(codigo, len(cuerpo)).encode("utf-8")
    return cab + cuerpo


def _parsear_longitud(peticion_raw: str) -> int:
    """Extrae el Content-Length de la cabecera HTTP."""
    for linea in peticion_raw.split("\r\n"):
        if linea.lower().startswith("content-length:"):
            try:
                return int(linea.split(":")[1].strip())
            except Exception:
                return 0
    return 0


def _leer_cuerpo(cliente, longitud: int) -> str:
    """Lee el cuerpo de la peticion POST."""
    if longitud <= 0:
        return ""
    try:
        return cliente.read(longitud).decode("utf-8")
    except Exception:
        return ""


class ServidorHTTP:
    """
    Servidor HTTP de un solo hilo para MicroPython.
    El HTML se sirve en fragmentos para no agotar la heap.
    Las respuestas JSON son siempre pequenas y se construyen normalmente.
    """

    def __init__(self, sistema, puerto: int = 80):
        self.sistema = sistema
        self.puerto  = puerto
        self._sock   = None

    def iniciar(self):
        """Crea el socket del servidor y lo pone en escucha."""
        addr = socket.getaddrinfo("0.0.0.0", self.puerto)[0][-1]
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(addr)
        self._sock.listen(2)
        self._sock.settimeout(0.5)
        print("[SERVIDOR] HTTP listo en puerto {}".format(self.puerto))

    def atender_peticion(self):
        """
        Intenta atender una peticion entrante.
        No bloquea si no hay peticion (timeout de 0.5 s).
        """
        if self._sock is None:
            return
        try:
            cliente, addr = self._sock.accept()
        except OSError:
            return

        try:
            peticion_raw = cliente.recv(1024).decode("utf-8", "ignore")
            if not peticion_raw:
                return

            linea_inicial = peticion_raw.split("\r\n")[0]
            partes = linea_inicial.split(" ")
            if len(partes) < 2:
                return

            metodo = partes[0]
            ruta   = partes[1]

            # Parsear cuerpo JSON en peticiones POST
            datos_post = {}
            if metodo == "POST":
                longitud = _parsear_longitud(peticion_raw)
                if longitud > 0:
                    separador = "\r\n\r\n"
                    if separador in peticion_raw:
                        cuerpo_str = peticion_raw.split(separador, 1)[1]
                        if len(cuerpo_str) < longitud:
                            cuerpo_str += _leer_cuerpo(cliente, longitud - len(cuerpo_str))
                    else:
                        cuerpo_str = _leer_cuerpo(cliente, longitud)
                    try:
                        datos_post = json.loads(cuerpo_str)
                    except Exception:
                        datos_post = {}

            self._enrutar(metodo, ruta, datos_post, cliente)

        except Exception as e:
            print("[SERVIDOR] Error al atender peticion:", e)
        finally:
            try:
                cliente.close()
            except Exception:
                pass
            gc.collect()

    def _enrutar(self, metodo: str, ruta: str, datos: dict, cliente):
        """
        Dirige la peticion al manejador correcto.
        Para HTML: envia cabecera + fragmentos directamente al socket.
        Para JSON: construye bytes y envia de una vez (siempre pequeno).
        """
        s = self.sistema

        # --- Pagina principal: envio fragmentado ---
        if ruta == "/" or ruta == "/index.html":
            self._servir_html(cliente)
            return

        # --- Rutas JSON ---
        respuesta = None

        if ruta == "/estado":
            respuesta = _respuesta_json(s.obtener_estado_completo())

        elif ruta == "/ventilador" and metodo == "POST":
            accion = datos.get("accion", "")
            if accion == "encender":
                s.actuadores.activar_ventilador()
            else:
                s.actuadores.apagar_ventilador()
            respuesta = _respuesta_json(s.actuadores.estado())

        elif ruta == "/ventanas" and metodo == "POST":
            accion = datos.get("accion", "")
            if accion == "abrir":
                s.actuadores.abrir_ventanas()
            else:
                s.actuadores.cerrar_ventanas()
            respuesta = _respuesta_json(s.actuadores.estado())

        elif ruta == "/escanear" and metodo == "POST":
            resultado = s.ejecutar_escaneo()
            resultado["historial"] = s.historial.obtener_todos()
            respuesta = _respuesta_json(resultado)

        elif ruta == "/escanear_auto" and metodo == "POST":
            resultado = s.ejecutar_escaneo_automatico()
            resultado["historial"] = s.historial.obtener_todos()
            respuesta = _respuesta_json(resultado)

        elif ruta == "/paro" and metodo == "POST":
            s.actuadores.paro_emergencia()
            respuesta = _respuesta_json({"ok": True, "paro": True})

        elif ruta == "/reiniciar" and metodo == "POST":
            s.actuadores.reiniciar_circuito()
            respuesta = _respuesta_json({"ok": True, "paro": False})

        elif ruta == "/modo" and metodo == "POST":
            nuevo_modo = datos.get("modo", "manual")
            s.cambiar_modo(nuevo_modo)
            respuesta = _respuesta_json({"ok": True, "modo": s.modo_actual})

        elif ruta == "/datos_ia":
            # Sirve el JSON de analisis IA generado en el ultimo escaneo
            from json_ia import leer_json_ia, existe_json_ia
            if existe_json_ia():
                contenido = leer_json_ia()
                if contenido:
                    cuerpo = contenido.encode("utf-8")
                    cab = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json; charset=utf-8\r\n"
                        "Content-Disposition: attachment; filename=\"datos_ia.json\"\r\n"
                        "Content-Length: {}\r\n"
                        "Connection: close\r\n\r\n"
                    ).format(len(cuerpo)).encode("utf-8")
                    cliente.sendall(cab)
                    # Enviar en fragmentos para no saturar la RAM
                    vista   = memoryview(cuerpo)
                    offset  = 0
                    total   = len(cuerpo)
                    while offset < total:
                        fin = min(offset + TAMANO_FRAGMENTO, total)
                        cliente.sendall(vista[offset:fin])
                        offset = fin
                    return
                else:
                    respuesta = _respuesta_texto(500, "Error al leer datos_ia.json")
            else:
                respuesta = _respuesta_texto(404, "Aun no hay datos. Ejecute un escaneo primero.")

        else:
            respuesta = _respuesta_texto(404, "Ruta no encontrada")

        if respuesta:
            cliente.sendall(respuesta)

    def _servir_html(self, cliente):
        """
        Envia la pagina HTML en fragmentos sin cargarla completa en RAM.
        Importa cada parte de pagina_web.py por separado y la envia de inmediato.
        """
        import pagina_web as pw

        # Calcular longitud total sin concatenar las cadenas
        longitud = len(pw.CABECERA_HTML.encode("utf-8")) + len(pw.CUERPO_HTML.encode("utf-8"))

        _enviar_cabecera_html(cliente, longitud)
        gc.collect()

        _enviar_fragmentos(cliente, pw.CABECERA_HTML)
        gc.collect()

        _enviar_fragmentos(cliente, pw.CUERPO_HTML)
        gc.collect()