## Context

See `proposal.md` for motivation. The system runs on a Raspberry Pi Pico 2 microcontroller using official Raspberry Pi Pico 2 MicroPython firmware. Key hardware interfaces include an analog gas sensor (MQ-7 Carbon Monoxide sensor on ADC0/GP26 via 10k/10k divider), an SSD1306 128x64 OLED display over I2C (GP2/GP3), and a momentary tactile push button on GP14. Note that the MQ-7 requires a preheating period (3 to 5 minutes) to operate properly, which is handled externally.

## Goals / Non-Goals

**Goals:**
- Implement a decoupled, modular MicroPython firmware structure (`config.py`, `sensors.py`, `display.py`, `button.py`, `main.py`).
- Read analog gas sensor levels via RP2350 ADC channel GP26 and convert to Carbon Monoxide PPM and mass concentration ($\text{mg/m}^3$).
- Provide real-time status and metric rendering on an 8-row OLED interface titled `SENSOR MONITOR` without divider lines (refreshed at 250ms / 4 Hz).
- Sample sensor readings at 1-second intervals (1 Hz).
- Track Current, Min, and Max PPM statistics, with instant reset via GP14 push button.
- Filter push-button mechanical chatter with non-blocking debounce logic using `time.ticks_ms()`.

**Non-Goals:**
- MicroSD card storage — removed to ensure 100% compatibility with standard RP2350 MicroPython firmware builds.
- Network connectivity (Wi-Fi, MQTT, Bluetooth) — offline real-time monitor for this PoC.
- Automated MQ-7 heater duty-cycle / preheat control — the MQ-7 sensor heater is powered continuously or externally; preheat management is not implemented in firmware.
- MicroPython `uasyncio` framework overhead — state and timing are managed with predictable `ticks_ms()` timestamp polling.

## Decisions

### Decision: Voltage dividers for 5V analog sensor signals
- **Choice:** Use a 10kΩ and 10kΩ resistor divider (ratio 2.0) to scale the 0–5V analog output down to 0–2.5V max for RP2350 ADC input `GP26`.
- **Rationale:** Protects RP2350 3.3V-tolerant GPIOs with standard matching resistors (max sensor Vin = 5.0V scales to max ADC Vout = 2.5V, safely within 3.3V limits).

### Decision: Gas Concentration Units (PPM and mg/m³)
- **Choice:** Map analog sensor output voltage through the empirical MQ-7 power-law curve:
  $$\text{PPM} = 98.322 \times \left(\frac{R_s}{R_0}\right)^{-1.458}$$
  where $R_s = \frac{V_c - V}{V} \times R_L$, and calculate mass concentration as $\text{mg/m}^3 = \text{PPM} \times 1.146$.
- **Rationale:** Raw voltage is unintuitive for users; PPM and $\text{mg/m}^3$ provide standard occupational air-quality metrics for Carbon Monoxide detection.

### Decision: OLED Display Layout (8 Rows x 16 Chars)
- **Choice:** Format display with:
  - Line 0: `SENSOR MONITOR`
  - Line 1: `[MONITORING]` (or temporary `[STATS RESET]`)
  - Line 2: `MQ-7 CO Sensor`
  - Line 3: `Cur:  XX.X PPM`
  - Line 4: `Min:  XX.X PPM`
  - Line 5: `Max:  XX.X PPM`
  - Line 6: `Mass: XX.X mg/m3`
  - Line 7: `Press to reset`
- **Rationale:** Fits cleanly within 16-character width of the 8x8 font on 128x64 SSD1306 without cutoffs or divider clutter.

### Decision: Flat modular architecture
- **Choice:** Separate concerns into root-level modules (`config.py`, `sensors.py`, `display.py`, `button.py`, `main.py`).
- **Rationale:** Avoids package hierarchy import overhead and keeps memory footprint low in embedded MicroPython.

### Decision: Non-blocking time polling loop
- **Choice:** Use `time.ticks_ms()` / `time.ticks_diff()` in a non-blocking loop rather than hardware interrupts or `uasyncio`.
- **Rationale:** Mechanical switch bounce in GPIO interrupts often triggers spurious ISR executions; non-blocking polling easily filters bounce and has minimal RAM overhead.

## Risks / Trade-offs

- **[Risk]** Sensor heater power draw causing voltage dips on RP2350 logic rails.
  - **Mitigation:** Power sensor heater circuits from the dedicated 5V power supply rail, keeping 3.3V rail clean for logic, display, and ADC reference.
