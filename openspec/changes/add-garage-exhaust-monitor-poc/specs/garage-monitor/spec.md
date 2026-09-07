## Purpose

Provides standalone garage exhaust monitoring by measuring carbon monoxide metrics, presenting them on a local display, and recording session data to an SD card.

## ADDED Requirements

### Requirement: Push Button Session Control
The system SHALL toggle between a stopped state and an active logging state when the hardware push button is pressed.

#### Scenario: Starting a new logging session
- **WHEN** the user presses the push button while in the `STOPPED` state
- **THEN** the system generates a new incremented CSV file (e.g., `log_002.csv`)
- **AND** the display status updates to indicate logging is active
- **AND** the system begins writing sensor data to the SD card at the configured interval

#### Scenario: Stopping an active session safely
- **WHEN** the user presses the push button while in the `LOGGING` state
- **THEN** the system flushes the buffer and closes the CSV file
- **AND** the display status updates to `STOPPED`
- **AND** no further data is written until the next session is initiated

### Requirement: Real-time UI Updates
The system SHALL display real-time sensor metrics and logging status on the local OLED screen.

#### Scenario: Displaying exhaust metrics
- **WHEN** a new sensor reading is polled
- **THEN** the OLED screen updates the current, minimum, and maximum values for the MQ-7 sensor
- **AND** the total count of recorded data rows is updated on the screen
