# Pico Alvik Adapter - UART to the Alvik STM32 on a Raspberry Pi Pico W.
# Drop-in replacement for arduino_alvik/uart.py (Nano ESP32: UART1, GPIO43/44;
# Pico Alvik Adapter: UART1, GP20/GP21).
from machine import UART, Pin

from .pinout_definitions import UART_ID, TX, RX

# UART SETTINGS (same link parameters as the Nano ESP32 version)
_BAUDRATE = 460800
_BITS = 8
_PARITY = None
_STOP = 1

uart = UART(UART_ID, baudrate=_BAUDRATE, bits=_BITS, parity=_PARITY, stop=_STOP,
            tx=Pin(TX), rx=Pin(RX), rxbuf=1024)
