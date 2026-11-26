# Bitcraze and sensor sources (stage 3, sensors)

Copied from public GitHub repositories. Bitcraze designs are open (schematics are CC-BY-NC-SA 4.0
per their title blocks); the files here are reference excerpts, not part of this design.

| File | From | What it gives |
|---|---|---|
| flow-deck-v2-mechanics.png, flow_deck_v2_585px.jpg | bitcraze/hardware @ 8207400, src/products/flow-deck-2/datasheet | Flow deck v2: 27.940 x 21.079 mm, 4 mm overall, 1.6 g; FRONT along the connector rows, pin 1 at the front; sensors on the underside |
| (link) flow-deck-v2-reva.pdf | same, electronics/ | Pin use: PMW3901 SPI on right 3-5, CS = IO_3 (left 8); VL53L1x I2C left 4-5; VCC left 1; VCOM right 9 -> TLV70218 1.8 V; GND left 10; DS28E05 on OW (right 8); RESET/MOTION/GPIO1 not fitted |
| female-connector-mechanics.png | bitcraze/hardware, female-deck-connector | Female deck connector: SMD, 20.5 x 2.0 x 2.1 mm, 2.00 mm pitch, pads 0.89 x 2, 5.4 mm overall |
| short-and-medium-pins-mechanics.png | bitcraze/hardware, short-and-medium-pins | Pins 0.5 mm sq, 2.00 mm pitch: short 9-2-2 mm, medium 15-2-2 mm (long: 15-4-6, 19-2-4) |
| flow-breakout-mechanics.png | bitcraze/hardware, flow-breakout | PMW3901 (U4) as a 28-pad 6 x 6 mm COB with exposed pad |
| (link) crazyflie_bolt_1_1_revh.pdf | bitcraze/hardware, crazyflie-bolt-1_1/electronics | IMU sheet: BMI088 on SPI (PS=GND), INT1->INT_ACC, INT2+INT3->INT_GYR, 100n; BMP388 on I2C (CSB, SDO to VDD), 100n; IMU supply VCCA = LP2985-30 + 1 uH + 4.7 uF |
| (link) template.kicad_pcb | bitcraze/crazyflie2-exp-template-electronics @ c8f9a2e | Deck rows 22.0 mm apart, 1x10 2.00 mm |

Sensor packages (Bosch site blocked from the build container; cross-checked):

| Part | Body | Source |
|---|---|---|
| BMI088 | 4.50 x 3.00 x 1.00 mm, LGA-16, 0.5 mm | Bosch STEP model BMI088.STEP (bit-bots/bitbots_imu_dxl electronics/imu_module/lib); pads: ../sensor_footprints/ardupilot_bmi088.kicad_mod (ArduPilot/Schematics HKUST NxtPX4v2) = bit-bots |
| BMP388 | 2.00 x 2.00 x 0.75 mm, LGA-10, 0.5 mm | STEP model SENSORM-SMD_BMP388.STEP (atopile/packages, LCSC); pads: ../sensor_footprints/openaxes_bmp388.kicad_mod (OpenAXES-IMU/OpenAXES), numbering = atopile (LCSC) |
| VL53L1x | 4.90 x 2.50 mm | KiCad library Sensor_Distance:ST_VL53L1x (F.Fab) |
| PMW3901 | 6 x 6 mm COB | Flow breakout layout (above); cbraissant/KiCad_Library COB-28_EP_6x6 |

Still to check against the manufacturer datasheets: BMI088 pin 1 / numbering, PMW3901 and VL53L1x
heights, supply ranges at 3.3 V, and the fields of view (42 / 27 deg used in the model).
