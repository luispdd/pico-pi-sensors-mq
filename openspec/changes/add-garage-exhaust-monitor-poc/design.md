## Context

See `proposal.md` for motivation. The system runs on a Waveshare RP2350-PiZero microcontroller using MicroPython. Key hardware interfaces include an analog gas sensor (MQ-7 Carbon Monoxide sensor), an SSD1306 128x64 OLED display over I2C, an onboard TF/MicroSD slot over SPI, and a momentary tactile push button on a GPIO pin. Note that the MQ-7 requires a preheating period (3 to 5 minutes) to operate properly, which is handled externally and not orchestrated by this firmware.

## Goals / Non-Goals

**Goals:**
- Implement a decoupled, modular MicroPython firmware structure (`config.py`, `sensors.py`, `storage.py`, `display.py`, `button.py`, `main.py`).
- Read analog gas sensor levels via RP2350 ADC channel GP26 with min/max tracking.
- Provide real-time status and metric rendering on an 8-row OLED interface (refreshed every 500ms).
- Provide session-based CSV logging with auto-incrementing filenames (`log_001.csv`, `log_002.csv`, etc.) and safe buffer flushing (flushed every 60s).
- Sample sensor readings at configured intervals (every 5s).
- Filter push-button mechanical chatter with non-blocking debounce logic using `time.ticks_ms()`.

**Non-Goals:**
- Network connectivity (Wi-Fi, MQTT, Bluetooth) — offline logging only for this PoC.
- Automated MQ-7 heater duty-cycle / preheat control — the MQ-7 sensor heater is powered continuously or externally; preheat management is not implemented in firmware.
- Factory calibration or PPM conversion curves for the MQ sensors (raw ADC and scaled voltage values using the voltage divider ratio are sufficient for baseline detection).
- MicroPython `uasyncio` framework overhead — state and timing are managed with predictable `ticks_ms()` timestamp polling.

## Decisions

### Decision: Voltage dividers for 5V analog sensor signals
- **Choice:** Use a 10kΩ and 10kΩ resistor divider (ratio 2.0) to scale the 0–5V analog output down to 0–2.5V max for RP2350 ADC input `GP26`.
- **Rationale:** Protects RP2350 3.3V-tolerant GPIOs with standard matching resistors (max sensor Vin = 5.0V scales to max ADC Vout = 2.5V, safely within 3.3V limits) while avoiding extra external ICs (e.g., ADS1115 ADC).
- **Alternatives considered:** 10kΩ / 20kΩ divider (1.5x multiplier, scaling up to 3.3V); dedicated external I2C ADC module; rejected to keep hardware complexity minimal with standard resistor values.

### Decision: Flat modular architecture
- **Choice:** Separate concerns into root-level modules (`config.py`, `sensors.py`, `storage.py`, `display.py`, `button.py`, `main.py`).
- **Rationale:** Avoids package hierarchy import overhead and keeps memory footprint low in embedded MicroPython.
- **Alternatives considered:** Single monolithic `main.py`; rejected due to lack of modularity and testability.

### Decision: Non-blocking time polling loop
- **Choice:** Use `time.ticks_ms()` / `time.ticks_diff()` in a non-blocking loop rather than hardware interrupts or `uasyncio`.
- **Rationale:** Mechanical switch bounce in GPIO interrupts often triggers spurious ISR executions; non-blocking polling easily filters bounce and has minimal RAM overhead compared to `uasyncio`.
- **Alternatives considered:** Hardware ISR with software timer debounce; rejected as unnecessarily complex for a single button and 5-second sensor polling.

## Risks / Trade-offs

- **[Risk]** Abrupt power loss corrupting SD card file tables.
  - **Mitigation:** Explicit `file.flush()` after periodic intervals (configured to 60 seconds) and writes, clean `file.close()` on session stop, and sequential file naming (`log_NNN.csv`) to isolate session logs.
- **[Risk]** Memory fragmentation during prolonged continuous logging.
  - **Mitigation:** Avoid string interpolation allocations inside tight loops; reuse fixed formatting buffers where possible and trigger garbage collection during state transitions.
- **[Risk]** Sensor heater power draw causing voltage dips on RP2350 logic rails.
  - **Mitigation:** Power sensor heater circuits from the dedicated 5V power supply rail, keeping 3.3V rail clean for logic, display, and ADC reference.
