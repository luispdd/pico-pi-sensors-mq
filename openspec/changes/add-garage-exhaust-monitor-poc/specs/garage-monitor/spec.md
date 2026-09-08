## Purpose

Provides standalone garage exhaust monitoring by measuring carbon monoxide metrics, calculating PPM and mass concentration ($\text{mg/m}^3$), presenting them on an OLED screen, and allowing statistics reset via a hardware button.

## ADDED Requirements

### Requirement: Push Button Statistics Reset
The system SHALL reset the minimum and maximum recorded PPM statistics when the hardware push button is pressed.

#### Scenario: Resetting peak and baseline statistics
- **WHEN** the user presses the push button on GP14
- **THEN** the system resets `min_ppm` and `max_ppm` tracking
- **AND** the display status temporarily shows `[STATS RESET]` for 2 seconds
- **AND** real-time monitoring continues seamlessly

### Requirement: Real-time UI Updates
The system SHALL display real-time sensor metrics on the local OLED screen without divider lines.

#### Scenario: Displaying exhaust metrics in PPM and mg/m³
- **WHEN** a new sensor reading is polled at 1-second intervals
- **THEN** the OLED screen displays:
  - Line 0: `SENSOR MONITOR`
  - Line 1: Current status (`[MONITORING]` or temporary alert)
  - Line 2: `MQ-7 CO Sensor`
  - Line 3: Current concentration in PPM
  - Line 4: Minimum concentration in PPM
  - Line 5: Maximum concentration in PPM
  - Line 6: Mass concentration in $\text{mg/m}^3$
  - Line 7: Button guidance (`Press to reset`)
