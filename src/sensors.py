"""Analog gas sensor driver and statistical manager for MicroPython.

Target: Raspberry Pi Pico 2
Sensor: MQ-7 Carbon Monoxide sensor on GP26 (ADC0) with 10k/10k resistor divider.
"""

try:
    import machine
except ImportError:
    machine = None

from config import (
    PIN_MQ7_ADC,
    ADC_VREF,
    ADC_MAX_U16,
    VOLTAGE_DIVIDER_RATIO,
    SENSOR_NAME,
    SENSOR_SUPPLY_VOLTAGE,
    RL_VALUE_KOHMS,
    RO_CLEAN_AIR_KOHMS,
    MQ7_PPM_A,
    MQ7_PPM_B,
    CO_MG_M3_FACTOR,
)


class GasSensor:
    """Represents an analog gas sensor with ADC reading, voltage scaling, and PPM calculation."""

    def __init__(
        self,
        pin_num=PIN_MQ7_ADC,
        name=SENSOR_NAME,
        vref=ADC_VREF,
        max_u16=ADC_MAX_U16,
        divider_ratio=VOLTAGE_DIVIDER_RATIO,
        supply_voltage=SENSOR_SUPPLY_VOLTAGE,
        rl_kohms=RL_VALUE_KOHMS,
        ro_clean_air=RO_CLEAN_AIR_KOHMS,
        ppm_a=MQ7_PPM_A,
        ppm_b=MQ7_PPM_B,
        co_mg_m3_factor=CO_MG_M3_FACTOR,
        adc=None,
    ):
        self.name = name
        self.vref = vref
        self.max_u16 = max_u16
        self.divider_ratio = divider_ratio
        self.supply_voltage = supply_voltage
        self.rl_kohms = rl_kohms
        self.ro_clean_air = ro_clean_air
        self.ppm_a = ppm_a
        self.ppm_b = ppm_b
        self.co_mg_m3_factor = co_mg_m3_factor

        self.is_digital = False
        self.digital_pin = None

        if adc is not None:
            self.adc = adc
        elif machine is not None:
            try:
                self.adc = machine.ADC(pin_num)
            except (ValueError, AttributeError):
                # Fallback to digital input for boards without ADC on this pin
                self.adc = None
                self.is_digital = True
                self.digital_pin = machine.Pin(pin_num, machine.Pin.IN)
        else:
            raise RuntimeError("machine module unavailable and no ADC object provided")

        self.current_raw = 0
        self.current_adc_voltage = 0.0
        self.current_voltage = 0.0
        self.current_ppm = 0.0
        self.current_mg_m3 = 0.0

        self.min_ppm = None
        self.max_ppm = None
        self.min_voltage = None
        self.max_voltage = None
        self.min_raw = None
        self.max_raw = None

    def calculate_ppm(self, sensor_voltage):
        """Convert analog sensor output voltage into Carbon Monoxide concentration (PPM).

        Formula based on MQ-7 datasheet sensitivity curve:
            Rs = ((Vc - Vout) / Vout) * RL
            Ratio = Rs / R0
            PPM = A * (Ratio ^ B)
        """
        if sensor_voltage <= 0.01:
            return 0.0
        # Prevent division by zero if voltage approaches or exceeds supply voltage Vc
        v = min(sensor_voltage, self.supply_voltage - 0.01)
        rs = ((self.supply_voltage - v) / v) * self.rl_kohms
        ratio = rs / self.ro_clean_air
        if ratio <= 0:
            return 0.0
        try:
            ppm = self.ppm_a * (ratio ** self.ppm_b)
            return max(0.0, ppm)
        except (ValueError, OverflowError, ZeroDivisionError):
            return 0.0

    def read(self):
        """Read the sensor (ADC or digital pin) and update statistics."""
        if self.is_digital and self.digital_pin is not None:
            val = self.digital_pin.value()
            raw = val
            adc_v = 3.3 if val else 0.0
            sensor_v = 5.0 if val else 0.0
            ppm = 100.0 if val == 0 else 0.0
            mg_m3 = ppm * self.co_mg_m3_factor
        else:
            raw = self.adc.read_u16()
            adc_v = (raw / self.max_u16) * self.vref
            sensor_v = adc_v * self.divider_ratio
            ppm = self.calculate_ppm(sensor_v)
            mg_m3 = ppm * self.co_mg_m3_factor

        self.current_raw = raw
        self.current_adc_voltage = adc_v
        self.current_voltage = sensor_v
        self.current_ppm = ppm
        self.current_mg_m3 = mg_m3

        if self.min_ppm is None or ppm < self.min_ppm:
            self.min_ppm = ppm
        if self.max_ppm is None or ppm > self.max_ppm:
            self.max_ppm = ppm

        if self.min_voltage is None or sensor_v < self.min_voltage:
            self.min_voltage = sensor_v
        if self.max_voltage is None or sensor_v > self.max_voltage:
            self.max_voltage = sensor_v

        if self.min_raw is None or raw < self.min_raw:
            self.min_raw = raw
        if self.max_raw is None or raw > self.max_raw:
            self.max_raw = raw

        return {
            "name": self.name,
            "raw": raw,
            "adc_voltage": adc_v,
            "sensor_voltage": sensor_v,
            "ppm": ppm,
            "mg_m3": mg_m3,
            "is_digital": self.is_digital,
        }

    def reset_stats(self):
        """Reset min and max tracking statistics."""
        self.min_ppm = None
        self.max_ppm = None
        self.min_voltage = None
        self.max_voltage = None
        self.min_raw = None
        self.max_raw = None


class SensorManager:
    """Manages collection of sensors and provides unified polling and statistics."""

    def __init__(self, sensors=None):
        self._sensors = {}
        if sensors is not None:
            for s in sensors:
                self.add_sensor(s)
        else:
            # Default configuration: single MQ-7 sensor
            self.add_sensor(GasSensor())

    def add_sensor(self, sensor):
        """Register a GasSensor instance."""
        self._sensors[sensor.name] = sensor

    def get_sensor(self, name="MQ-7"):
        """Retrieve a registered sensor by name."""
        return self._sensors.get(name)

    def read_all(self):
        """Poll all registered sensors and return readings keyed by name."""
        readings = {}
        for name, sensor in self._sensors.items():
            readings[name] = sensor.read()
        return readings

    def reset_all_stats(self):
        """Reset min/max statistics across all managed sensors."""
        for sensor in self._sensors.values():
            sensor.reset_stats()
