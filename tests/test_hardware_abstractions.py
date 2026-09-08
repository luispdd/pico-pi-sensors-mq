"""Unit tests for SENSOR MONITOR core hardware abstractions.

Tests cover:
- button.py (DebouncedButton edge detection and timing)
- sensors.py (GasSensor and SensorManager ADC conversion, PPM calculation, and statistics)
- display.py (OLEDView 8-line layout formatting and constraints)
"""

import os
import sys
import unittest

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from button import DebouncedButton
from display import OLEDView
from sensors import GasSensor, SensorManager


class MockPin:
    def __init__(self, value=1):
        self._value = value

    def value(self, val=None):
        if val is not None:
            self._value = val
        return self._value


class MockADC:
    def __init__(self, value=0):
        self._value = value

    def read_u16(self):
        return self._value

    def set_value(self, value):
        self._value = value


class MockDisplay:
    def __init__(self):
        self.texts = []
        self.cleared = False
        self.shown = False

    def fill(self, color):
        self.cleared = True
        self.texts = []

    def text(self, msg, x, y):
        self.texts.append((msg, x, y))

    def show(self):
        self.shown = True


class TestDebouncedButton(unittest.TestCase):
    def setUp(self):
        import time

        self.current_time = 1000
        time.ticks_ms = lambda: self.current_time
        time.ticks_diff = lambda a, b: a - b
        self.pin = MockPin(1)  # Released by default (pull-up = 1)
        self.button = DebouncedButton(pin=self.pin, debounce_ms=50)

    def test_initial_state(self):
        self.assertFalse(self.button.is_pressed())
        self.assertFalse(self.button.was_pressed())

    def test_bouncing_does_not_trigger_press(self):
        # Contact bounce: goes 0 briefly, then back to 1 before 50ms
        self.pin.value(0)
        self.button.update()
        self.current_time += 20
        self.pin.value(1)
        self.button.update()
        self.current_time += 60
        self.button.update()

        self.assertFalse(self.button.was_pressed())
        self.assertFalse(self.button.is_pressed())

    def test_valid_press_after_debounce(self):
        # Stable transition to 0 (pressed)
        self.pin.value(0)
        self.button.update()

        # Before debounce window elapses
        self.current_time += 30
        self.button.update()
        self.assertFalse(self.button.was_pressed())

        # After debounce window elapses
        self.current_time += 25  # Total 55ms
        self.button.update()
        self.assertTrue(self.button.was_pressed())
        # was_pressed clears event latch
        self.assertFalse(self.button.was_pressed())
        self.assertTrue(self.button.is_pressed())

    def test_release_after_press(self):
        # Press
        self.pin.value(0)
        self.button.update()
        self.current_time += 60
        self.button.update()
        self.assertTrue(self.button.was_pressed())

        # Release
        self.pin.value(1)
        self.button.update()
        self.current_time += 60
        self.button.update()
        self.assertFalse(self.button.is_pressed())
        self.assertFalse(self.button.was_pressed())


class TestGasSensor(unittest.TestCase):
    def setUp(self):
        self.mock_adc = MockADC(0)
        self.sensor = GasSensor(
            name="MQ-7",
            vref=3.3,
            max_u16=65535,
            divider_ratio=2.0,
            supply_voltage=5.0,
            rl_kohms=10.0,
            ro_clean_air=10.0,
            ppm_a=98.322,
            ppm_b=-1.458,
            co_mg_m3_factor=1.146,
            adc=self.mock_adc,
        )

    def test_adc_conversion_and_voltage_scaling(self):
        # Half scale: ~32768 -> ADC voltage ~ 1.65V, Sensor voltage ~ 3.30V
        self.mock_adc.set_value(32768)
        reading = self.sensor.read()

        self.assertEqual(reading["name"], "MQ-7")
        self.assertEqual(reading["raw"], 32768)
        self.assertAlmostEqual(reading["adc_voltage"], 1.65002, places=3)
        self.assertAlmostEqual(reading["sensor_voltage"], 3.30005, places=3)

    def test_ppm_calculation_clean_air_and_high_gas(self):
        # When sensor voltage = 2.5V (half of 5V supply):
        # Rs = ((5.0 - 2.5) / 2.5) * 10 = 10k -> Rs/R0 = 1.0
        # PPM = 98.322 * (1.0 ^ -1.458) = 98.322
        ppm_2_5v = self.sensor.calculate_ppm(2.5)
        self.assertAlmostEqual(ppm_2_5v, 98.322, places=2)

        # Zero or very low voltage (clean air / disconnected) returns 0.0
        self.assertEqual(self.sensor.calculate_ppm(0.0), 0.0)

        # Higher voltage means higher gas concentration
        ppm_low_gas = self.sensor.calculate_ppm(1.5)
        ppm_high_gas = self.sensor.calculate_ppm(3.5)
        self.assertGreater(ppm_high_gas, ppm_low_gas)

    def test_statistical_tracking_and_reset(self):
        # 1st reading (medium gas)
        raw_mid = int((1.25 / 3.3) * 65535)  # 2.5V sensor
        self.mock_adc.set_value(raw_mid)
        self.sensor.read()
        ppm1 = self.sensor.current_ppm
        self.assertEqual(self.sensor.min_ppm, ppm1)
        self.assertEqual(self.sensor.max_ppm, ppm1)

        # 2nd reading (higher gas)
        raw_high = int((1.75 / 3.3) * 65535)  # 3.5V sensor
        self.mock_adc.set_value(raw_high)
        self.sensor.read()
        ppm2 = self.sensor.current_ppm
        self.assertGreater(ppm2, ppm1)
        self.assertEqual(self.sensor.min_ppm, ppm1)
        self.assertEqual(self.sensor.max_ppm, ppm2)

        # 3rd reading (lower gas)
        raw_low = int((0.75 / 3.3) * 65535)  # 1.5V sensor
        self.mock_adc.set_value(raw_low)
        self.sensor.read()
        ppm3 = self.sensor.current_ppm
        self.assertLess(ppm3, ppm1)
        self.assertEqual(self.sensor.min_ppm, ppm3)
        self.assertEqual(self.sensor.max_ppm, ppm2)

        # Reset statistics
        self.sensor.reset_stats()
        self.assertIsNone(self.sensor.min_ppm)
        self.assertIsNone(self.sensor.max_ppm)


    def test_mg_m3_conversion(self):
        raw_mid = int((1.25 / 3.3) * 65535)
        self.mock_adc.set_value(raw_mid)
        reading = self.sensor.read()
        expected_mg_m3 = reading["ppm"] * 1.146
        self.assertAlmostEqual(reading["mg_m3"], expected_mg_m3, places=2)


class TestSensorManager(unittest.TestCase):
    def test_manager_orchestration(self):
        mock_adc1 = MockADC(15000)
        s1 = GasSensor(name="MQ-7", adc=mock_adc1)

        manager = SensorManager(sensors=[s1])
        self.assertIs(manager.get_sensor("MQ-7"), s1)

        readings = manager.read_all()
        self.assertIn("MQ-7", readings)
        self.assertEqual(readings["MQ-7"]["raw"], 15000)
        self.assertIn("ppm", readings["MQ-7"])
        self.assertIn("mg_m3", readings["MQ-7"])

        # Test reset all
        manager.reset_all_stats()
        self.assertIsNone(s1.min_ppm)


class TestOLEDView(unittest.TestCase):
    def setUp(self):
        self.mock_display = MockDisplay()
        self.view = OLEDView(oled=self.mock_display)

    def test_line_count_and_width_constraints(self):
        lines = self.view.format_lines(
            state="MONITORING",
            current_ppm=24.5,
            min_ppm=10.2,
            max_ppm=88.9,
            mg_m3=28.1,
            btn_pressed=False,
            btn_prompt="Press to reset",
        )

        self.assertEqual(len(lines), 8)
        for idx, line in enumerate(lines):
            self.assertLessEqual(
                len(line),
                16,
                f"Line {idx} exceeds 16 chars: '{line}' (len={len(line)})",
            )

        # Validate line content formatting
        self.assertEqual(lines[0], "SENSOR MONITOR")
        self.assertEqual(lines[1], "[MONITORING]")
        self.assertEqual(lines[2], "MQ-7 CO Sensor")
        self.assertEqual(lines[3], "Cur:  24.5 PPM")
        self.assertEqual(lines[4], "Min:  10.2 PPM")
        self.assertEqual(lines[5], "Max:  88.9 PPM")
        self.assertEqual(lines[6], "Mass: 28.1 mg/m3")
        self.assertEqual(lines[7], "Press to reset")

    def test_button_pressed_line_prompt(self):
        lines = self.view.format_lines(btn_pressed=True)
        self.assertEqual(lines[7], "Resetting...")

    def test_render_calls_hardware(self):
        self.view.render(
            state="MONITORING",
            current_ppm=15.0,
        )
        self.assertTrue(self.mock_display.cleared)
        self.assertTrue(self.mock_display.shown)
        self.assertEqual(len(self.mock_display.texts), 8)


if __name__ == "__main__":
    unittest.main()
