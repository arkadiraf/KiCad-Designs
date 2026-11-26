#!/usr/bin/env python3
"""Port a stock copy of the Arduino Alvik MicroPython library to the Pico W
on the Pico Alvik Adapter.

usage:  python3 port_alvik_to_pico.py <path/to/arduino_alvik>

<path/to/arduino_alvik> is the package folder from
https://github.com/arduino/arduino-alvik-mpy (tested with library 1.1.4).
The folder is modified in place; copy it to the Pico afterwards
(e.g. `mpremote cp -r arduino_alvik :` plus the ucPack dependency).

What it does
  * pinout_definitions.py, uart.py  -> replaced by firmware/overlay/*
  * arduino_alvik.py   I2C(0, ...)   -> I2C(I2C_ID, ...)   (GP6/GP7 are I2C1)
  * stm32_flash.py     ESP32 pins/UART for the STM32 firmware updater
                       -> adapter pins (A6=GP8, D2=GP20, D3=GP21, UART0 GP16/17)
Every edit must match exactly; if the upstream library changed, the script
stops without touching anything.
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.join(HERE, "overlay")
TESTED_VERSION = "1.1.4"

# (file, regex, replacement, expected match count)
PATCHES = [
    ("arduino_alvik.py", r"\bI2C\(0,", "I2C(I2C_ID,", 10),
    ("stm32_flash.py", r"(?m)^A6 = 13\b.*$", "A6 = 8      # Pico Alvik Adapter: nano A6 -> GP8", 1),
    ("stm32_flash.py", r"(?m)^_D2 = 5\b.*$", "_D2 = 20    # Pico Alvik Adapter: nano D2 -> GP20", 1),
    ("stm32_flash.py", r"(?m)^_D3 = 6\b.*$", "_D3 = 21    # Pico Alvik Adapter: nano D3 -> GP21", 1),
    ("stm32_flash.py", r"(?m)^_UART_ID = 1\b.*$", "_UART_ID = 0  # Pico Alvik Adapter: UART0", 1),
    ("stm32_flash.py", r"(?m)^_TX_PIN = 43\b.*$", "_TX_PIN = 16  # Pico Alvik Adapter: GP16", 1),
    ("stm32_flash.py", r"(?m)^_RX_PIN = 44\b.*$", "_RX_PIN = 17  # Pico Alvik Adapter: GP17", 1),
]
MARKER = "# ported to Pico W by Pico_Alvik_Adapter/firmware/port_alvik_to_pico.py\n"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pkg = sys.argv[1]
    if not os.path.isfile(os.path.join(pkg, "arduino_alvik.py")):
        sys.exit(f"error: {pkg} does not look like the arduino_alvik package folder")

    init = open(os.path.join(pkg, "__init__.py")).read()
    m = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    ver = m.group(1) if m else "?"
    if ver != TESTED_VERSION:
        print(f"warning: library version {ver}, script tested with {TESTED_VERSION}")

    # apply all patches in memory first, so a mismatch leaves the folder untouched
    texts = {}
    for fname, rx, rep, count in PATCHES:
        path = os.path.join(pkg, fname)
        txt = texts.get(fname) or open(path).read()
        if MARKER in txt:
            sys.exit(f"error: {fname} is already ported")
        new, n = re.subn(rx, rep, txt)
        if n != count:
            sys.exit(f"error: {fname}: expected {count} match(es) of {rx!r}, found {n}; "
                     "upstream library changed - nothing was modified")
        texts[fname] = new

    for fname, txt in texts.items():
        with open(os.path.join(pkg, fname), "w") as f:
            f.write(MARKER + txt)
    for fname in ("pinout_definitions.py", "uart.py"):
        shutil.copyfile(os.path.join(OVERLAY, fname), os.path.join(pkg, fname))
    print(f"arduino_alvik {ver} ported to the Pico Alvik Adapter:")
    print("  replaced pinout_definitions.py, uart.py")
    print("  patched  arduino_alvik.py (I2C bus 1), stm32_flash.py (pins, UART0)")


if __name__ == "__main__":
    main()
