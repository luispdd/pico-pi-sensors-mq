"""Unit tests for SENSOR MONITOR application orchestration (main.py).

Tests cover:
- Boot sequence diagnostics and graceful component failure handling
- Real-time MONITORING state operation
- Button press triggering statistics reset and temporary status notification
- Periodic non-blocking polling (1s sensor sample, 250ms display refresh)
- Safe shutdown
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from main import GarageMonitorApp, DummyDisplay
from sensors import GasSensor, SensorManager


class MockButton:
    def __init__(self):
        self._was_pressed = False
        self._is_pressed = False

    def trigger_press(self):
        self._was_pressed = True
        self._is_pressed = True

    def release(self):
        self._is_pressed = False

    def update(self):
        pass

    def was_pressed(self):
        if self._was_pressed:
            self._was_pressed = False
            return True
        return False

    def is_pressed(self):
        return self._is_pressed

    def raw_is_pressed(self):
        return self._is_pressed


class MockDisplay:
    def __init__(self):
        self.render_calls = []
        self.rendered_lines = []
        self.error_calls = []

    def clear(self):
        pass

    def show(self):
        pass

    def render(self, state, current_ppm=0.0, min_ppm=None, max_ppm=None, mg_m3=None, btn_pressed=False, **kwargs):
        self.render_calls.append({
            "state": state,
            "current_ppm": current_ppm,
            "min_ppm": min_ppm,
            "max_ppm": max_ppm,
            "mg_m3": mg_m3,
            "btn_pressed": btn_pressed,
            "kwargs": kwargs,
        })

    def render_lines(self, lines):
        self.rendered_lines.append(list(lines))

    def render_error(self, msg):
        self.error_calls.append(msg)


class MockADC:
    def __init__(self, value=30000):
        self.value = value

    def read_u16(self):
        return self.value


class TestGarageMonitorApp(unittest.TestCase):
    def setUp(self):
        self.mock_button = MockButton()
        self.mock_display = MockDisplay()
        self.mock_adc = MockADC(20000)
        self.sensor = GasSensor(name="MQ-7", adc=self.mock_adc)
        self.sensors = SensorManager(sensors=[self.sensor])

        self.current_time = 1000
        time.ticks_ms = lambda: self.current_time
        time.ticks_diff = lambda a, b: a - b
        time.sleep_ms = lambda ms: None  # Fast sleep during tests

        self.app = GarageMonitorApp(
            button=self.mock_button,
            sensor_manager=self.sensors,
            display=self.mock_display,
        )

    def tearDown(self):
        self.app.shutdown()

    def test_boot_sequence_renders_progress_to_display(self):
        fresh_app = GarageMonitorApp(
            button=self.mock_button,
            sensor_manager=self.sensors,
            display=self.mock_display,
        )
        fresh_app.boot()

        # Check that display received lines during boot
        self.assertGreater(len(self.mock_display.rendered_lines), 0)
        last_boot_screen = self.mock_display.rendered_lines[-1]
        self.assertTrue(any("Display: OK" in line for line in last_boot_screen))
        self.assertTrue(any("Button:  OK" in line for line in last_boot_screen))
        self.assertTrue(any("MQ-7:" in line for line in last_boot_screen))

    def test_initial_state_is_monitoring(self):
        self.assertEqual(self.app.state, GarageMonitorApp.STATE_MONITORING)

    def test_button_press_resets_sensor_stats(self):
        # 1. Establish some min and max stats
        self.sensor.read()
        self.assertIsNotNone(self.sensor.min_ppm)
        self.assertIsNotNone(self.sensor.max_ppm)

        # 2. Trigger button press
        self.mock_button.trigger_press()
        self.app.tick()

        # 3. Stats should be cleared
        self.assertIsNone(self.sensor.min_ppm)
        self.assertIsNone(self.sensor.max_ppm)

        # 4. Display state shows [STATS RESET]
        latest_display = self.mock_display.render_calls[-1]
        self.assertEqual(latest_display["state"], "[STATS RESET]")

        # 5. After 2000ms duration, state reverts to MONITORING
        self.current_time += 2500
        self.app.update_display()
        latest_display = self.mock_display.render_calls[-1]
        self.assertEqual(latest_display["state"], "MONITORING")

    def test_periodic_sensor_sampling_and_display_refresh(self):
        self.app.boot()
        initial_renders = len(self.mock_display.render_calls)

        # Advance by 250ms: display should refresh (DISPLAY_REFRESH_INTERVAL_MS = 250)
        self.current_time += 250
        self.app.tick()
        self.assertGreater(len(self.mock_display.render_calls), initial_renders)

        # Change ADC value and advance by 1000ms: sensor should sample (SENSOR_SAMPLE_INTERVAL_MS = 1000)
        self.mock_adc.value = 45000
        self.current_time += 1000
        self.app.tick()

        self.assertEqual(self.app.latest_reading["raw"], 45000)
        self.assertGreater(self.app.latest_reading["ppm"], 0.0)

    def test_shutdown_renders_stopped_screen(self):
        self.app.shutdown()
        self.assertFalse(self.app.running)
        last_rendered = self.mock_display.rendered_lines[-1]
        self.assertTrue(any("STOPPED" in line for line in last_rendered))


if __name__ == "__main__":
    unittest.main()
