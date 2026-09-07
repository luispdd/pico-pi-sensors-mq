## Why

A mechanism is needed to measure and record the accumulation of carbon monoxide and general exhaust pollutants in the garage when a vehicle enters and exits. This proof-of-concept (PoC) will validate the hardware layout—specifically the gas sensors, local storage, and physical UI—without the complexity of network transmission, serving as the foundational offline data logger before a future network upgrade.

## What Changes

* **Hardware Assembly:** Wire a Waveshare RP2350-PiZero to an MQ-7 (CO) sensor, a 128x64 SSD1306 OLED display, and a push button.
* **MicroPython Firmware:** Implement a decoupled, object-oriented MicroPython application to poll sensors, update the display, and manage state transitions.
* **Local SD Logging:** Implement a file management system to write timestamped CSV records to the board's onboard Micro SD slot, generating a new file for each logging session.
* **State Machine:** Add push-button debounce logic to toggle the system between `IDLE/STOPPED` and `LOGGING` states.

## Capabilities

### New Capabilities
- `garage-monitor`: Exhaust gas monitoring, real-time OLED metric display, and push-button session logging to local SD card.

### Modified Capabilities
<!-- None -->

## Impact

* **MicroPython Codebase:** Introduces new modular files (`config.py`, `sensors.py`, `storage.py`, `display.py`, `button.py`, `main.py`).
* **Hardware & Pin Mappings:** RP2350 ADC pin GP26 for analog MQ-7 sensor readings (via a 10k/10k voltage divider scaling to 2.5V max), I2C for OLED display, internal SPI for TF/MicroSD slot, and GPIO with pull-up for button.
* **Dependencies:** MicroPython standard drivers `ssd1306.py` and `sdcard.py`.
