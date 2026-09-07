"""Hardware and application configuration for Garage Exhaust Monitor PoC.

Target Microcontroller: Waveshare RP2350-PiZero
Runtime: MicroPython
"""

# ---------------------------------------------------------------------------
# Analog Gas Sensors (ADC)
# ---------------------------------------------------------------------------
# MQ-7: Carbon Monoxide (CO) sensor
# MQ-135: Air Quality / Hazardous gases sensor
# Both sensors operate on 5V with analog outputs scaled down to 3.3V max

# ---------------------------------------------------------------------------
# Option 1: 10k ohm / 20k ohm voltage divider
# ---------------------------------------------------------------------------
# using a voltage divider (e.g., 10k ohm / 20k ohm network).
#PIN_MQ7_ADC = 26       # GP26 / ADC0
#PIN_MQ135_ADC = 27     # GP27 / ADC1

#ADC_VREF = 3.3         # ADC reference voltage (Volts)
#ADC_MAX_U16 = 65535    # MicroPython read_u16() 16-bit range

# Voltage divider scaling: Vin = Vout * (R1 + R2) / R2
# With R1 = 10k, R2 = 20k: (10k + 20k) / 20k = 1.5 multiplier (3.33V * 1.5 = 5.0V)
#VOLTAGE_DIVIDER_RATIO = 1.5
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Option 2: 10k ohm / 10k ohm voltage divider
# ---------------------------------------------------------------------------
# using a voltage divider (e.g., 10k ohm / 10k ohm network).
PIN_MQ7_ADC = 26       # GP26 / ADC0
PIN_MQ135_ADC = 27     # GP27 / ADC1

ADC_VREF = 3.3         # ADC reference voltage (Volts)
ADC_MAX_U16 = 65535    # MicroPython read_u16() 16-bit range

# Voltage divider scaling: Vin = Vout * (R1 + R2) / R2
# With R1 = 10k, R2 = 10k: (10k + 10k) / 10k = 2 multiplier (3.33V * 2 = 6.66V)
VOLTAGE_DIVIDER_RATIO = 2.0


# ---------------------------------------------------------------------------
# I2C Bus & OLED Display (SSD1306)
# ---------------------------------------------------------------------------
# 0.96 inch 128x64 Monochrome OLED Display
I2C_ID = 1             # I2C peripheral ID (0 or 1)
PIN_I2C_SDA = 2        # GP2 (Pi 40-pin header pin 3)
PIN_I2C_SCL = 3        # GP3 (Pi 40-pin header pin 5)
I2C_FREQ = 400_000     # 400 kHz Fast Mode

OLED_WIDTH = 128       # Display width in pixels
OLED_HEIGHT = 64       # Display height in pixels
OLED_I2C_ADDR = 0x3C   # Default SSD1306 I2C address


# ---------------------------------------------------------------------------
# SPI Bus & Onboard TF / MicroSD Card
# ---------------------------------------------------------------------------
# Onboard TF slot routed via SPI peripheral
SPI_ID = 1             # SPI peripheral ID
PIN_SPI_SCK = 10       # GP10 / SPI1 SCK
PIN_SPI_MOSI = 11      # GP11 / SPI1 TX
PIN_SPI_MISO = 12      # GP12 / SPI1 RX
PIN_SPI_CS = 13        # GP13 / SPI1 CS

SD_MOUNT_POINT = "/sd"
LOG_FILE_PREFIX = "log_"
LOG_FILE_EXT = ".csv"


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
SENSOR_SAMPLE_INTERVAL_MS = 1000      # 1 Hz sensor polling
DISPLAY_REFRESH_INTERVAL_MS = 250     # 4 Hz display updates
STORAGE_FLUSH_INTERVAL_MS = 5000      # Safe flush interval during active logging
