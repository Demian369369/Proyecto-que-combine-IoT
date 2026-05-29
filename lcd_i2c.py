# =============================================================================
# lcd_i2c.py - Driver LCD 16x2 con adaptador I2C PCF8574
# Compatible 100% con MicroPython nativo para ESP32
# Direccion por defecto: 0x3F (configurable desde config.py)
# =============================================================================

from machine import I2C, Pin
import time

# Comandos estandar del controlador HD44780
LCD_CLEAR       = 0x01
LCD_HOME        = 0x02
LCD_ENTRY_MODE  = 0x06
LCD_DISPLAY_ON  = 0x0C
LCD_FUNCTION_4B = 0x28   # Modo 4 bits, 2 lineas, fuente 5x8

# Bits del PCF8574 que mapean al bus de datos del LCD
BIT_RS  = 0x01   # Register Select (0=comando, 1=datos)
BIT_EN  = 0x04   # Enable
BIT_BL  = 0x08   # Backlight


class LCD:
    """Controlador para LCD 16x2 conectado via modulo I2C PCF8574."""

    def __init__(self, i2c: I2C, direccion: int = 0x3F):
        self.i2c        = i2c
        self.direccion  = direccion
        self.backlight  = BIT_BL
        self._inicializar()

    # ------------------------------------------------------------------
    # Metodos internos de comunicacion I2C / HD44780
    # ------------------------------------------------------------------

    def _escribir_i2c(self, byte: int):
        """Envia un byte al expansor PCF8574 via I2C."""
        self.i2c.writeto(self.direccion, bytes([byte | self.backlight]))

    def _pulso_enable(self, byte: int):
        """Genera el pulso de Enable necesario para que el LCD procese el nibble."""
        self._escribir_i2c(byte | BIT_EN)
        time.sleep_us(1)
        self._escribir_i2c(byte & ~BIT_EN)
        time.sleep_us(50)

    def _enviar_nibble(self, nibble: int, modo: int):
        """Envia 4 bits (nibble) al LCD en modo comando o datos."""
        byte = (nibble & 0xF0) | modo
        self._pulso_enable(byte)

    def _enviar_byte(self, byte: int, modo: int):
        """Envia un byte completo al LCD en dos nibbles (modo 4 bits)."""
        self._enviar_nibble(byte & 0xF0, modo)
        self._enviar_nibble((byte << 4) & 0xF0, modo)

    def _comando(self, cmd: int):
        """Envia un comando al LCD."""
        self._enviar_byte(cmd, 0)

    def _dato(self, caracter: int):
        """Envia un caracter al LCD."""
        self._enviar_byte(caracter, BIT_RS)

    # ------------------------------------------------------------------
    # Inicializacion segun secuencia especificada por Hitachi HD44780
    # ------------------------------------------------------------------

    def _inicializar(self):
        time.sleep_ms(50)
        # Secuencia de inicializacion en modo 4 bits
        for _ in range(3):
            self._enviar_nibble(0x30, 0)
            time.sleep_ms(5)
        self._enviar_nibble(0x20, 0)
        time.sleep_ms(1)
        self._comando(LCD_FUNCTION_4B)
        self._comando(LCD_DISPLAY_ON)
        self._comando(LCD_CLEAR)
        time.sleep_ms(2)
        self._comando(LCD_ENTRY_MODE)

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def limpiar(self):
        """Borra todo el contenido de la pantalla."""
        self._comando(LCD_CLEAR)
        time.sleep_ms(2)

    def mover_cursor(self, fila: int, columna: int):
        """Posiciona el cursor en fila (0-1) y columna (0-15)."""
        direcciones_fila = [0x00, 0x40]
        self._comando(0x80 | (direcciones_fila[fila] + columna))

    def escribir(self, texto: str):
        """Escribe una cadena de texto en la posicion actual del cursor."""
        for caracter in texto:
            self._dato(ord(caracter))

    @staticmethod
    def _rellenar(texto: str, ancho: int) -> str:
        """Rellena texto con espacios hasta el ancho indicado (ljust no existe en MicroPython)."""
        texto = texto[:ancho]
        while len(texto) < ancho:
            texto = texto + " "
        return texto

    def mostrar_lineas(self, linea1: str, linea2: str = ""):
        """Muestra dos lineas de texto, rellenando con espacios hasta 16 caracteres."""
        self.limpiar()
        self.mover_cursor(0, 0)
        self.escribir(self._rellenar(linea1, 16))
        self.mover_cursor(1, 0)
        self.escribir(self._rellenar(linea2, 16))