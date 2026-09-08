"""Main entry point and orchestrator for SENSOR MONITOR.

Target Microcontroller: Raspberry Pi Pico 2
Runtime: MicroPython
"""

import sys
import time

# Host Python compatibility for MicroPython timing primitives
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.time() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda a, b: a - b
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)

from config import (
    APP_TITLE,
    SENSOR_SAMPLE_INTERVAL_MS,
    DISPLAY_REFRESH_INTERVAL_MS,
    PIN_BUTTON,
    PIN_MQ7_ADC,
)
from button import DebouncedButton
from sensors import SensorManager, GasSensor
from display import OLEDView


def print_exc(e):
    """Print exception details compatible with both MicroPython and standard Python."""
    if hasattr(sys, "print_exception"):
        sys.print_exception(e)
    else:
        import traceback
        traceback.print_exc()


class DummyDisplay:
    """Fallback no-op display when physical OLED is unavailable."""

    def clear(self):
        pass

    def show(self):
        pass

    def render(self, *args, **kwargs):
        pass

    def render_lines(self, lines):
        print("--- [OLED VIEW] ---")
        for line in lines:
            print("  ", line)

    def render_error(self, message):
        print("[OLED ERROR]", message)


class GarageMonitorApp:
    """State machine, boot diagnosis, and non-blocking real-time sensor monitor engine."""

    STATE_MONITORING = "MONITORING"

    def __init__(self, button=None, sensor_manager=None, display=None, storage=None):
        self.button = button
        self.sensors = sensor_manager
        self.display = display
        # Optional dummy/mock parameter retained for interface compatibility
        self.storage = storage

        self.state = self.STATE_MONITORING
        self.running = False
        self.status_msg_override = None
        self.status_msg_expire_time = 0

        # Debounce lockout for reset operations
        self.last_reset_time = 0

        # Periodic timing trackers
        now = time.ticks_ms()
        self.last_sensor_time = now
        self.last_display_time = now

        # Cached latest sensor reading
        self.latest_reading = {
            "name": "MQ-7",
            "raw": 0,
            "adc_voltage": 0.0,
            "sensor_voltage": 0.0,
            "ppm": 0.0,
            "mg_m3": 0.0,
            "is_digital": False,
        }

    def boot(self):
        """Execute safe sequential boot diagnostics and render progress to display and serial."""
        print("========================================")
        print(" {} - BOOT CHECK   ".format(APP_TITLE))
        print("========================================")

        boot_lines = ["== BOOT CHECK =="]

        # -------------------------------------------------------------
        # 1. Initialize Display
        # -------------------------------------------------------------
        if self.display is None:
            try:
                self.display = OLEDView()
                print("[BOOT] [OK] OLED Display (128x64 SSD1306)")
                boot_lines.append("Display: OK")
                self.display.render_lines(boot_lines)
                time.sleep_ms(300)
            except Exception as e:
                print("[BOOT] [FAIL] OLED Display init failed: {}".format(e))
                print_exc(e)
                self.display = DummyDisplay()
                boot_lines.append("Display: FAIL")
        else:
            boot_lines.append("Display: OK")
            self.display.render_lines(boot_lines)

        # -------------------------------------------------------------
        # 2. Initialize Button
        # -------------------------------------------------------------
        if self.button is None:
            try:
                self.button = DebouncedButton()
                btn_state = "DN" if self.button.raw_is_pressed() else "UP"
                print("[BOOT] [OK] Button GP{} (Initial: {})".format(PIN_BUTTON, btn_state))
                boot_lines.append("Button:  OK ({})".format(btn_state))
            except Exception as e:
                print("[BOOT] [FAIL] Button init failed: {}".format(e))
                boot_lines.append("Button:  FAIL")
        else:
            boot_lines.append("Button:  OK")

        self.display.render_lines(boot_lines)
        time.sleep_ms(200)

        # -------------------------------------------------------------
        # 3. Initialize Sensor (MQ-7)
        # -------------------------------------------------------------
        if self.sensors is None:
            try:
                self.sensors = SensorManager()
                readings = self.sensors.read_all()
                if "MQ-7" in readings:
                    self.latest_reading = readings["MQ-7"]
                    ppm = self.latest_reading.get("ppm", 0.0)
                    is_dig = self.latest_reading.get("is_digital", False)
                    if is_dig:
                        status = "ALERT" if self.latest_reading.get("sensor_voltage") == 0.0 else "CLEAR"
                        print("[BOOT] [OK] MQ-7 Digital (GP{}) state: {}".format(PIN_MQ7_ADC, status))
                        boot_lines.append("MQ-7:    OK (DIG)")
                    else:
                        print("[BOOT] [OK] MQ-7 ADC (GP{}) read: {:.1f} PPM".format(PIN_MQ7_ADC, ppm))
                        boot_lines.append("MQ-7:    OK {:.1f}PPM".format(ppm))
                else:
                    boot_lines.append("MQ-7:    NO DATA")
            except Exception as e:
                print("[BOOT] [FAIL] MQ-7 sensor init failed: {}".format(e))
                boot_lines.append("MQ-7:    FAIL")
        else:
            try:
                readings = self.sensors.read_all()
                if "MQ-7" in readings:
                    self.latest_reading = readings["MQ-7"]
                boot_lines.append("MQ-7:    OK")
            except Exception:
                boot_lines.append("MQ-7:    FAIL")

        self.display.render_lines(boot_lines)

        # Pause 2 seconds so user can read boot diagnostics on OLED screen
        time.sleep_ms(2000)
        print("========================================")
        print(" BOOT COMPLETE - Running in [{}] mode".format(self.state))
        print("========================================")

        now = time.ticks_ms()
        self.last_sensor_time = now
        self.last_display_time = now
        self.update_display()

    def set_temporary_status(self, msg, duration_ms=2000):
        """Display a temporary message on line 1 of the display."""
        self.status_msg_override = msg
        self.status_msg_expire_time = time.ticks_ms() + duration_ms
        self.update_display()

    def reset_stats(self):
        """Reset min/max statistics across all sensors on button press."""
        now = time.ticks_ms()
        # Enforce 500ms lockout between resets to prevent duplicate triggers
        if time.ticks_diff(now, self.last_reset_time) < 500:
            return

        self.last_reset_time = now
        print("[APP] User pressed button: Resetting statistics.")
        if self.sensors:
            self.sensors.reset_all_stats()

        self.set_temporary_status("[STATS RESET]", 2000)

    def update_display(self):
        """Render current metrics and status to the OLED."""
        mq7 = self.sensors.get_sensor("MQ-7") if self.sensors else None
        min_ppm = mq7.min_ppm if mq7 else None
        max_ppm = mq7.max_ppm if mq7 else None
        curr_ppm = self.latest_reading.get("ppm", 0.0)
        mg_m3 = self.latest_reading.get("mg_m3", 0.0)

        # Handle temporary status override using MicroPython ticks_diff
        now = time.ticks_ms()
        if self.status_msg_override and time.ticks_diff(self.status_msg_expire_time, now) > 0:
            display_state = self.status_msg_override
        else:
            self.status_msg_override = None
            display_state = self.state

        btn_pressed = False
        if self.button and hasattr(self.button, "raw_is_pressed"):
            btn_pressed = self.button.raw_is_pressed()

        try:
            self.display.render(
                state=display_state,
                current_ppm=curr_ppm,
                min_ppm=min_ppm,
                max_ppm=max_ppm,
                mg_m3=mg_m3,
                btn_pressed=btn_pressed,
                is_digital=self.latest_reading.get("is_digital", False),
                btn_prompt="Press to reset",
            )
        except Exception as e:
            print("[APP ERROR] Display render failed: {}".format(e))

    def tick(self):
        """Execute a single non-blocking polling cycle."""
        now = time.ticks_ms()

        # 1. Update button debounce & check edge
        if self.button:
            try:
                self.button.update()
                if self.button.was_pressed():
                    self.reset_stats()
            except Exception as e:
                print("[APP ERROR] Button update error: {}".format(e))

        # 2. Sensor sampling timer (1s interval)
        if time.ticks_diff(now, self.last_sensor_time) >= SENSOR_SAMPLE_INTERVAL_MS:
            if self.sensors:
                try:
                    readings = self.sensors.read_all()
                    if "MQ-7" in readings:
                        self.latest_reading = readings["MQ-7"]
                except Exception as e:
                    print("[APP ERROR] Sensor read error: {}".format(e))
            self.last_sensor_time = now

        # 3. Display refresh timer (250ms interval)
        if time.ticks_diff(now, self.last_display_time) >= DISPLAY_REFRESH_INTERVAL_MS:
            self.update_display()
            self.last_display_time = now

    def run(self):
        """Main non-blocking execution loop."""
        self.boot()
        self.running = True

        try:
            while self.running:
                self.tick()
                time.sleep_ms(10)
        except KeyboardInterrupt:
            print("\n[APP] Interrupted by user.")
        finally:
            self.shutdown()

    def shutdown(self):
        """Safely shut down the application."""
        self.running = False
        print("[APP] Shutting down cleanly...")
        try:
            if self.display:
                self.display.render_lines(["SENSOR MONITOR", "[STOPPED]", "Power off safe."])
        except Exception:
            pass
        print("[APP] Goodbye.")


def main():
    """Application startup entry point."""
    try:
        app = GarageMonitorApp()
        app.run()
    except Exception as e:
        print("[FATAL ERROR] Main process crashed: {}".format(e))
        print_exc(e)


if __name__ == "__main__":
    main()
