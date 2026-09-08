## Why

A mechanism is needed to measure and monitor the accumulation of carbon monoxide (CO) in the garage when a vehicle enters and exits. This proof-of-concept (PoC) validates the hardware layout—specifically the MQ-7 gas sensor, RP2350 ADC input, and physical OLED user interface—displaying real-time CO gas concentration in user-friendly units (PPM and $\text{mg/m}^3$) with statistical tracking (Current, Min, Max), without SD card storage dependencies or network complexity.

## What Changes

* **Hardware Assembly:** Wire a Raspberry Pi Pico 2 to an MQ-7 (CO) sensor, a 128x64 SSD1306 OLED display, and a push button.
* **MicroPython Firmware:** Implement a decoupled, object-oriented MicroPython application (`SENSOR MONITOR`) to poll sensors at 1s intervals, update the display at 250ms intervals, and manage real-time statistics.
* **Gas Conversion & Units:** Map analog sensor output voltage through the MQ-7 power-law curve to calculate Carbon Monoxide concentration in PPM and mass concentration ($\text{mg/m}^3$).
* **Statistics & Physical UI:** Use the push button on `GP14` to reset Min/Max/Peak PPM statistics on demand, displaying `"Press to reset"` on the OLED display.

## Capabilities

### New Capabilities
- `garage-monitor`: Real-time CO exhaust gas monitoring (`SENSOR MONITOR`), OLED metric display with PPM and $\text{mg/m}^3$ units, and push-button statistics reset.

### Modified Capabilities
<!-- None -->

## Impact

* **MicroPython Codebase:** Introduces modular files (`config.py`, `sensors.py`, `display.py`, `button.py`, `main.py`). MicroSD storage modules (`storage.py`, `sdcard.py`) are removed.
* **Hardware & Pin Mappings:** RP2350 ADC pin GP26 for analog MQ-7 sensor readings (via a 10k/10k voltage divider scaling to 2.5V max), I2C for OLED display (GP2/GP3), and GP14 with internal pull-up for tactile push button.
* **Dependencies:** MicroPython standard driver `ssd1306.py`.
