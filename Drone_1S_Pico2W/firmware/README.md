# Flight firmware: Crazyflie firmware on the Pico 2 W

The board uses the Crazyflie sensor set, so the open Crazyflie flight stack is the starting point.

## What Bitcraze publishes (checked 2026-11-26)

[bitcraze/crazyflie-firmware](https://github.com/bitcraze/crazyflie-firmware) (HEAD d794c5c,
2026-11-16), actively maintained.

* **Licence: GPL-3.0.** `LICENSE.txt` is the GPL-3.0 text and the source headers say GNU GPL; only
  the README says LGPL-3.0. Treat it as GPL-3.0. A port must stay GPL-3.0, with its source
  published if it is distributed.
* **Platforms** (`build_targets.json`): `cf2`, `bolt`, `cf21bl`, `flapper`, `tag`. All are
  STM32F405 boards running FreeRTOS.
* **Drivers for exactly our parts:**

  | Our part | Firmware |
  |---|---|
  | BMI088 (SPI) + BMP388 | `src/hal/src/sensors_bmi088_spi.c`, `sensors_bmi088_bmp3xx.c`, Bosch drivers in `src/drivers/bosch` |
  | Flow deck v2: PMW3901 + VL53L1x | `src/drivers/src/pmw3901.c`, `vl53l1x.c`, `src/deck/drivers/src/flowdeck_v1v2.c` (CS = `DECK_GPIO_IO3`, as the deck schematic) |
  | 4 × DYS XSD7A ESCs | `src/drivers/src/motors.c`: DShot, including bidirectional DShot telemetry (Bolt brushless) |

* **Flight core:**
  * Estimators: complementary, Kalman (with the flow and ToF measurement models), UKF.
  * Controllers: PID, Mellinger, INDI, Brescianini, Lee.
  * Also the supervisor / arming state machine and the quadrotor power distribution.

## Precedent: Espressif ESP-Drone

[espressif/esp-drone](https://github.com/espressif/esp-drone) (GPL-3.0) is the Crazyflie firmware
(tag 2021.01, b448553) ported off the STM32 to ESP32 SoCs. It flies over **Wi-Fi**, works with cfclient
through a fork, and uses the same flow / ToF extension for position hold. It shows the split a port
needs. No RP2040 / RP2350 port of the Crazyflie firmware turned up in a GitHub search.

## What a Pico 2 W port has to replace

| Crazyflie (STM32F405) | Pico 2 W (RP2350, 2 × Cortex-M33 + FPU, 150 MHz) |
|---|---|
| FreeRTOS on one core | FreeRTOS RP2350 port (Pico SDK); the second core is free for Wi-Fi or logging |
| STM32 SPL: SPI + DMA, I2C, GPIO EXTI | Pico SDK `hardware_spi` / `dma` / `i2c` / `gpio` IRQ (BMI088 INT_ACC / INT_GYR) |
| DShot via timer DMA | PIO: one state machine per ESC, bidirectional DShot also possible in PIO |
| Radio through the nRF51 over syslink (UART) | CYW43 Wi-Fi: CRTP over UDP as in ESP-Drone; the cflib / cfclient UDP link |
| Battery monitor through the nRF51 | ADC on GPIO29 (VSYS / 3), as in the design doc |
| Deck 1-wire ID (nRF51) | Fixed config: the Flow deck is always fitted (or read the DS28E05 from a GPIO) |
| Platform files `platform_bolt.c`, `platform_defaults_bolt.h` | new `platform_pico2w.c` + pin map, checked against `design.py` (`check_firmware.py`, AGENTS.md section 7) |

## What this means for the hardware (stage 2 pin map)

Keep the same bus split as the Bolt so its drivers carry over unchanged:
* **BMI088:** alone on SPI0, with two chip selects (accel, gyro) and two interrupts (INT_ACC; INT_GYR
  from INT2 + INT3), as the design doc and the Bolt.
* **Flow deck:** on SPI1 (PMW3901, CS on IO_3, max 2 MHz); VL53L1x and BMP388 on I2C0.
* **ESCs:** 4 DShot outputs on PIO-capable pins (every Pico GPIO is); 4 TPS22997 ON + 4 PG lines.
* **Battery sense:** GPIO29.
