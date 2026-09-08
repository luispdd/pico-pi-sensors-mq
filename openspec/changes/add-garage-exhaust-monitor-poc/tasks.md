## 1. Hardware Configuration & Driver Setup

- [x] 1.1 Create `config.py` defining GPIO and ADC pin constants (ADC0/GP26 for MQ-7 with 10k/10k divider ratio, I2C bus pins, button pin), PPM conversion constants, and timing intervals (1s sample, 250ms display refresh), verifying configuration loads cleanly.
- [x] 1.2 Vendor or provide standard MicroPython driver `ssd1306.py` and verify module imports without syntax errors.
- [x] 1.3 Remove SD card modules and SPI configuration to eliminate hardware/firmware pin limitation issues.

## 2. Core Hardware Abstractions

- [x] 2.1 Implement `button.py` with `DebouncedButton` class using `time.ticks_ms()` non-blocking edge filtering, verifying button press edge detection.
- [x] 2.2 Implement `sensors.py` with `GasSensor` and `SensorManager` classes to read the MQ-7 ADC channel, calculate scaled voltage values, compute PPM and mg/m³ concentrations, and track min/max/current statistics.
- [x] 2.3 Implement `display.py` with `OLEDView` class to format and render the 8-line layout (`SENSOR MONITOR`, PPM metrics, mg/m³, and `"Press to reset"` button prompt) on the 128x64 display.

## 3. Application Orchestration & Verification

- [x] 3.1 Implement `main.py` sequential boot diagnostics checking Display, Button, and MQ-7 sensor.
- [x] 3.2 Implement the non-blocking execution loop in `main.py` coordinating 1s sensor sampling and 250ms OLED rendering.
- [x] 3.3 Implement button press statistics reset functionality clearing Min/Max records and rendering temporary `[STATS RESET]` notification.
- [x] 3.4 Verify complete unit test suite and syntax compilation.
