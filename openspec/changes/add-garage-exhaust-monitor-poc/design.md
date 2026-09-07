## Context

See `proposal.md` for motivation. The system runs on a Waveshare RP2350-PiZero microcontroller using MicroPython. Key hardware interfaces include analog gas sensors (MQ-7 and MQ-135), an SSD1306 128x64 OLED display over I2C, an onboard TF/MicroSD slot over SPI, and a momentary tactile push button on a GPIO pin.

## Goals / Non-Goals

**Goals:**
- Implement a decoupled, modular MicroPython firmware structure (`config.py`, `sensors.py`, `storage.py`, `display.py`, `button.py`, `main.py`).
- Read analog gas sensor levels via RP2350 ADC channels with min/max tracking.
- Provide real-time status and metric rendering on an 8-row OLED interface.
- Provide session-based CSV logging with auto-incrementing filenames (`log_001.csv`, `log_002.csv`, etc.) and safe buffer flushing.
- Filter push-button mechanical chatter with non-blocking debounce logic using `time.ticks_ms()`.

**Non-Goals:**
- Network connectivity (Wi-Fi, MQTT, Bluetooth) — offline logging only for this PoC.
- Factory calibration or PPM conversion curves for the MQ sensors (raw ADC and relative voltage/ratio values are sufficient for baseline detection).
- MicroPython `uasyncio` framework overhead — state and timing are managed with predictable `ticks_ms()` timestamp polling.

## Decisions

### Decision: Voltage dividers for 5V analog sensor signals
- **Choice:** Use 10kΩ and 20kΩ resistor dividers to scale 0–5V analog outputs down to 0–3.3V for RP2350 ADC inputs `GP26` and `GP27`.
- **Rationale:** Protects RP2350 3.3V-tolerant GPIOs while avoiding extra external ICs (e.g., ADS1115 ADC).
- **Alternatives considered:** Dedicated external I2C ADC module; rejected to keep hardware complexity and component count minimal.

### Decision: Flat modular architecture
- **Choice:** Separate concerns into root-level modules (`config.py`, `sensors.py`, `storage.py`, `display.py`, `button.py`, `main.py`).
- **Rationale:** Avoids package hierarchy import overhead and keeps memory footprint low in embedded MicroPython.
- **Alternatives considered:** Single monolithic `main.py`; rejected due to lack of modularity and testability.

### Decision: Non-blocking time polling loop
- **Choice:** Use `time.ticks_ms()` / `time.ticks_diff()` in a non-blocking loop rather than hardware interrupts or `uasyncio`.
- **Rationale:** Mechanical switch bounce in GPIO interrupts often triggers spurious ISR executions; non-blocking polling easily filters bounce and has minimal RAM overhead compared to `uasyncio`.
- **Alternatives considered:** Hardware ISR with software timer debounce; rejected as unnecessarily complex for a single button and 1Hz sensor polling.

## Risks / Trade-offs

- **[Risk]** Abrupt power loss corrupting SD card file tables.
  - **Mitigation:** Explicit `file.flush()` after writes, clean `file.close()` on session stop, and sequential file naming (`log_NNN.csv`) to isolate session logs.
- **[Risk]** Memory fragmentation during prolonged continuous logging.
  - **Mitigation:** Avoid string interpolation allocations inside tight loops; reuse fixed formatting buffers where possible and trigger garbage collection during state transitions.
- **[Risk]** Sensor heater power draw causing voltage dips on RP2350 logic rails.
  - **Mitigation:** Power sensor heater circuits from the dedicated 5V power supply rail, keeping 3.3V rail clean for logic, display, and ADC reference.
