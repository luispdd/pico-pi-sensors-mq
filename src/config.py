"""Hardware and application configuration for Garage Exhaust Monitor PoC.

Target Microcontroller: Raspberry Pi Pico 2
Runtime: MicroPython
"""

# ---------------------------------------------------------------------------
# Analog Gas Sensors (ADC)
# ---------------------------------------------------------------------------
# MQ-7: Carbon Monoxide (CO) sensor
# The sensor operates on 5V with analog outputs scaled down to 2.5V max
# Ideally it should use a 10k and 20k ohm voltage divider to scale the output to 3.3V
# Note: The MQ-7 sensor needs to be heated to operate (3 to 5 minutes), which is not implemented in this project

# Using a voltage divider (e.g., 10k ohm / 10k ohm network).
PIN_MQ7_ADC = 26       # GP26 / ADC0

ADC_VREF = 3.3         # ADC reference voltage (Volts)
ADC_MAX_U16 = 65535    # MicroPython read_u16() 16-bit range

# Voltage divider scaling: Vin = Vout * (R1 + R2) / R2
# With R1 = 10k, R2 = 10k: (10k + 10k) / 10k = 2.0 multiplier
# Max sensor Vin = 5.0V -> Max ADC Vout = 2.5V (safely within 3.3V limit)
VOLTAGE_DIVIDER_RATIO = 2.0


# ---------------------------------------------------------------------------
# MQ-7 Gas Sensor (CO) & PPM Conversion Constants
# ---------------------------------------------------------------------------
# The MQ-7 sensor operates on 5V with analog output scaled down via 10k/10k divider.
# Power law formula: PPM = A * (Rs / R0) ^ B
# Where Rs = ((Vc - Vout) / Vout) * RL
SENSOR_NAME = "MQ-7"
SENSOR_SUPPLY_VOLTAGE = 5.0     # Vc (Volts)
RL_VALUE_KOHMS = 10.0           # Load resistance RL in kilo-ohms
RO_CLEAN_AIR_KOHMS = 10.0       # Calibrated clean air sensor resistance in kilo-ohms
MQ7_PPM_A = 98.322              # Empirical sensitivity coefficient for CO
MQ7_PPM_B = -1.458              # Empirical sensitivity exponent for CO
CO_MG_M3_FACTOR = 1.146         # Conversion factor: 1 PPM CO = 1.146 mg/m3 at 25°C, 1 atm


# ---------------------------------------------------------------------------
# I2C Bus & OLED Display (SSD1306)
# ---------------------------------------------------------------------------
# 0.96 inch 128x64 Monochrome OLED Display
APP_TITLE = "SENSOR MONITOR"
I2C_ID = 1             # I2C peripheral ID (0 or 1)
PIN_I2C_SDA = 2        # GP2 (Pi 40-pin header pin 3)
PIN_I2C_SCL = 3        # GP3 (Pi 40-pin header pin 5)
I2C_FREQ = 400_000     # 400 kHz Fast Mode

OLED_WIDTH = 128       # Display width in pixels
OLED_HEIGHT = 64       # Display height in pixels
OLED_I2C_ADDR = 0x3C   # Default SSD1306 I2C address


# ---------------------------------------------------------------------------
# User Input (Push Button)
# ---------------------------------------------------------------------------
# Momentary tactile button tied to ground with internal pull-up resistor.
# Pressed = Logic LOW (0), Released = Logic HIGH (1).
PIN_BUTTON = 14        # GP14 (Pi 40-pin header pin 8)
BUTTON_DEBOUNCE_MS = 50  # Debounce window in milliseconds


# ---------------------------------------------------------------------------
# Sampling & Timing Intervals
# ---------------------------------------------------------------------------
SENSOR_SAMPLE_INTERVAL_MS = 1000      # 1 second sensor polling (1 Hz)
DISPLAY_REFRESH_INTERVAL_MS = 250     # 250 ms display updates (4 Hz)

