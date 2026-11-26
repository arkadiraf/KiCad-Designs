# Alvik MicroPython library on the Pico W (Pico Alvik Adapter)

Port kit for Arduino's [arduino-alvik-mpy](https://github.com/arduino/arduino-alvik-mpy) library,
tested against library version **1.1.4**, for a Pico W on the Pico Alvik Adapter v1.6.

| File | Purpose |
|---|---|
| `overlay/pinout_definitions.py` | Drop-in replacement: Nano pin names -> Pico GPIOs on the adapter |
| `overlay/uart.py` | Drop-in replacement: STM32 link on UART1 (GP20/GP21), 460800 baud |
| `port_alvik_to_pico.py` | Copies the two overlay files into a stock `arduino_alvik` folder and patches the rest |

## Pin mapping (adapter v1.6)

| Nano | Pico | Alvik use |
|---|---|---|
| D1/TX | GP20 (UART1 TX) | serial link -> STM32 |
| D0/RX | GP21 (UART1 RX) | serial link <- STM32 |
| D2 | GP22 | STM32 BOOT0 |
| D3 | GP26 | STM32 NRST |
| D4 | GP27 | NANO_CHK |
| A4/SDA | GP6 (I2C1 SDA) | I2C bus |
| A5/SCL | GP7 (I2C1 SCL) | I2C bus |
| A6 | GP8 | ROBOT_CHK input |
| D5 | GP28 (ADC2) | spare |
| D13, A0-A3, A7 | GP1, GP2-GP5, GP9 | spare |
| D6-D12 | not wired | - |

`tools/check_firmware.py` checks this file against the board design (`tools/design.py`).

## What the port changes

1. **`pinout_definitions.py`** gets the new GPIO numbers. It also exports `UART_ID = 1` and
   `I2C_ID = 1`, and replaces the RGB LED. The Nano's LED is active-low (`value(1)` = off), and the
   library depends on that. On the Pico, `LEDG` drives the single green LED with inverted logic, so
   the library's status blinks still read correctly. `LEDR` and `LEDB` do nothing.
2. **`uart.py`** opens UART1 on GP20/GP21. The Nano uses UART1 on GPIO43/44.
3. **`arduino_alvik.py`**: the ten `I2C(0, ...)` calls become `I2C(I2C_ID, ...)`, because GP6/GP7
   belong to the RP2040's I2C1.
4. **`stm32_flash.py`** (the STM32 firmware updater) has its own hard-coded ESP32 pins: A6=13, D2=5,
   D3=6, UART1 on 43/44. These are patched to GP8, GP22, GP26 and UART1 on GP20/GP21. Left
   unpatched, it would drive GP5 and GP6, the spare A3 pin and the Alvik's I2C SDA line.

The script applies every edit in memory and checks each one matches exactly the expected number of
times. If the upstream library has changed, it stops without modifying anything. It also refuses to
run twice on the same folder.

## Usage

```sh
git clone https://github.com/arduino/arduino-alvik-mpy
python3 Pico_Alvik_Adapter/firmware/port_alvik_to_pico.py arduino-alvik-mpy/arduino_alvik
# flash MicroPython for the Pico W, then copy the library and its ucPack dependency:
mpremote cp -r arduino-alvik-mpy/arduino_alvik :
mpremote mip install github:arduino/ucPack-mpy
```

## Known limitations

* **One extra thread only.** MicroPython on the RP2040 runs at most one extra thread, on the
  second core. The library's main update thread works. The separate event thread, used by
  `on_touch_*` / `on_move` style callbacks, can't start, and its `start_new_thread` call raises
  `OSError`. Poll the sensors from your main loop instead, or merge the event loop into the update
  thread.
* **No RGB LED.** Only green (the Pico W LED) is shown.
* **Not run on hardware yet.** The patches have been checked by inspecting the patched library. Run
  a first test on the robot with care, and check the STM32 link (`alvik.begin()`) before trying
  the firmware updater.
