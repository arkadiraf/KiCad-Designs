# Pico Alvik Adapter - pin definitions for the Arduino Alvik MicroPython
# library (arduino-alvik-mpy) running on a Raspberry Pi Pico W.
#
# Drop-in replacement for arduino_alvik/pinout_definitions.py.
# Mapping = adapter board v1.6 (Pico_Alvik_Adapter/tools/design.py).
# Use firmware/port_alvik_to_pico.py to install it together with the other
# RP2040 changes (uart.py, I2C bus id, stm32_flash.py pins).

from machine import Pin

# ---------------------------------------------------------------------------
# Nano pin name -> Pico GPIO (through the adapter board).  None = not wired.
# ---------------------------------------------------------------------------
# Pins used by the Alvik
D0 = 21      # Nano D0/RX0  -> GP21 (UART1 RX)  <- STM32 TX
D1 = 20      # Nano D1/TX1  -> GP20 (UART1 TX)  -> STM32 RX
D2 = 22      # Nano D2      -> GP22             -> STM32 BOOT0
D3 = 26      # Nano D3      -> GP26             -> STM32 NRST
D4 = 27      # Nano D4      -> GP27             -> STM32 NANO_CHK
A4 = 6       # Nano A4/SDA  -> GP6  (I2C1 SDA)  Alvik I2C bus (Qwiic/Grove/BMS)
A5 = 7       # Nano A5/SCL  -> GP7  (I2C1 SCL)
A6 = 8       # Nano A6      -> GP8              <- STM32 ROBOT_CHK

# Spare Nano pins (not used by the Alvik, wired for convenience)
D5 = 28      # Nano D5      -> GP28 (ADC2)
D13 = 1      # Nano D13     -> GP1
A0 = 2       # Nano A0      -> GP2
A1 = 3       # Nano A1      -> GP3
A2 = 4       # Nano A2      -> GP4
A3 = 5       # Nano A3      -> GP5
A7 = 9       # Nano A7      -> GP9

# Not connected on the adapter (unused by the Alvik)
D6 = D7 = D8 = D9 = D10 = D11 = D12 = None

# ---------------------------------------------------------------------------
# Peripherals (RP2040 needs the matching hardware block for each pin pair)
# ---------------------------------------------------------------------------
UART_ID = 1        # GP20/GP21 = UART1
TX = D1
RX = D0
I2C_ID = 1         # GP6/GP7  = I2C1  (the Nano ESP32 library uses I2C(0, ...))

# ---------------------------------------------------------------------------
# NANO to STM32 control pins (same names/roles as the Nano ESP32 file)
# ---------------------------------------------------------------------------
BOOT0_STM32 = Pin(D2, Pin.OUT)                  # nano D2 -> STM32 Boot0
RESET_STM32 = Pin(D3, Pin.OUT)                  # nano D3 -> STM32 NRST
NANO_CHK = Pin(D4, Pin.OUT)                     # nano D4 -> STM32 NANO_CHK
CHECK_STM32 = Pin(A6, Pin.IN, Pin.PULL_DOWN)    # nano A6 -> STM32 ROBOT_CHK


# ---------------------------------------------------------------------------
# LEDs.  The Nano ESP32 RGB LED is active-low (value(1) = off) and the library
# relies on that.  The Pico W only has one green LED (active-high, on the
# CYW43 chip), so LEDG drives it with inverted logic and LEDR/LEDB are no-ops.
# ---------------------------------------------------------------------------
class _ActiveLowLed:
    def __init__(self, pin):
        self._pin = pin
        self._pin.value(0)

    def value(self, v=None):
        if v is None:
            return 0 if self._pin.value() else 1
        self._pin.value(0 if v else 1)

    def on(self):           # Pin.on() = high = LED off on the Nano
        self.value(1)

    def off(self):
        self.value(0)


class _NoLed:
    def value(self, v=None):
        return 1 if v is None else None

    def on(self):
        pass

    def off(self):
        pass


LEDG = _ActiveLowLed(Pin("LED", Pin.OUT))       # green = Pico W on-board LED
LEDR = _NoLed()
LEDB = _NoLed()
