# Pico Alvik Adapter - pin definitions for running the Arduino Alvik
# MicroPython library (arduino-alvik-mpy) on a Raspberry Pi Pico W.
#
# Drop-in replacement for arduino_alvik/pinout_definitions.py.  The adapter
# board wires the Nano-footprint pins to these Pico GPIOs (see README.md).
#
# Other changes needed in the Alvik library when porting to RP2040:
#   * uart.py : UART(0, baudrate=460800, tx=Pin(16), rx=Pin(17))
#               (Nano D1/TX -> GP16 = UART0 TX, Nano D0/RX -> GP17 = UART0 RX)
#   * I2C     : Nano A4/A5 -> GP6/GP7, which are I2C *1* on the RP2040, so use
#               I2C(1, scl=Pin(7), sda=Pin(6)) instead of I2C(0, ...).
#   * LEDs    : the Pico W has no RGB LED, only the single green LED driven by
#               the CYW43 radio chip: Pin("LED", Pin.OUT).

from machine import Pin

# Nano pin name -> Pico GPIO (via adapter board).  None = not wired.
D0 = 17      # Nano D0/RX0  -> GP17 (UART0 RX)  <- STM32 TX
D1 = 16      # Nano D1/TX1  -> GP16 (UART0 TX)  -> STM32 RX
D2 = 20      # Nano D2      -> GP20             -> STM32 BOOT0
D3 = 21      # Nano D3      -> GP21             -> STM32 NRST
D4 = 22      # Nano D4      -> GP22             -> STM32 NANO_CHK
D5 = 26      # Nano D5      -> GP26 (ADC0)  spare
D6 = 27      # Nano D6      -> GP27 (ADC1)  spare
D7 = 28      # Nano D7      -> GP28 (ADC2)  spare
D8 = D9 = D10 = D11 = D12 = None   # not wired (unused on the Alvik)
D13 = 1      # Nano D13     -> GP1   spare
A0 = 2       # Nano A0      -> GP2   spare
A1 = 3       # Nano A1      -> GP3   spare
A2 = 4       # Nano A2      -> GP4   spare
A3 = 5       # Nano A3      -> GP5   spare
A4 = 6       # Nano A4/SDA  -> GP6  (I2C1 SDA)
A5 = 7       # Nano A5/SCL  -> GP7  (I2C1 SCL)
A6 = 8       # Nano A6      -> GP8  <- STM32 ROBOT_CHK
A7 = 9       # Nano A7      -> GP9   spare

# UART to the Alvik STM32
UART_ID = 0
TX = D1
RX = D0

# NANO to STM32 control pins (same roles as the original Nano ESP32 file)
BOOT0_STM32 = Pin(D2, Pin.OUT)                  # nano D2 -> STM32 Boot0
RESET_STM32 = Pin(D3, Pin.OUT)                  # nano D3 -> STM32 NRST
NANO_CHK = Pin(D4, Pin.OUT)                     # nano D4 -> STM32 NANO_CHK
CHECK_STM32 = Pin(A6, Pin.IN, Pin.PULL_DOWN)    # nano A6 -> STM32 ROBOT_CHK

# LEDs: Pico W has a single green LED (on the wireless chip).
LED = Pin("LED", Pin.OUT)
LEDR = LED
LEDG = LED
LEDB = LED
