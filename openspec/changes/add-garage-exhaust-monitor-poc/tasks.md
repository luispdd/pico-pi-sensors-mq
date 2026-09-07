## 1. Hardware Configuration & Driver Setup

- [x] 1.1 Create `config.py` defining GPIO and ADC pin constants (ADC0/GP26 for MQ-7 with 10k/10k divider ratio, I2C bus pins, SPI bus pins for SD slot, button pin) and timing intervals (5s sample, 500ms display refresh, 60s flush), verifying configuration loads cleanly.
- [x] 1.2 Vendor or provide standard MicroPython driver `ssd1306.py` and verify module imports without syntax errors.
- [x] 1.3 Vendor or provide standard MicroPython driver `sdcard.py` and verify module imports without syntax errors.

## 2. Core Hardware Abstractions

- [ ] 2.1 Implement `button.py` with `DebouncedButton` class using `time.ticks_ms()` non-blocking edge filtering, verifying button press edge detection.
- [ ] 2.2 Implement `sensors.py` with `GasSensor` and `SensorManager` classes to read the MQ-7 ADC channel, calculate scaled voltage values using the divider ratio, and track min/max/current statistics.
- [ ] 2.3 Implement `display.py` with `OLEDView` class to format and render the 8-line layout on the 128x64 display, verifying metric string layout.
- [ ] 2.4 Implement `storage.py` with `SDLogger` class handling SPI SD card mounting, scanning for existing session logs, auto-incrementing filenames (`log_NNN.csv`), and writing CSV headers and rows.

## 3. Application Orchestration & Verification

- [ ] 3.1 Implement `main.py` with state machine handling transitions between `STOPPED` and `LOGGING` states triggered by button press.
- [ ] 3.2 Implement the non-blocking execution loop in `main.py` coordinating sensor sampling, OLED rendering, and CSV logging.
- [ ] 3.3 Verify safe buffer flush (`file.flush()`) and file closure (`file.close()`) upon session stop to ensure no SD filesystem corruption.
