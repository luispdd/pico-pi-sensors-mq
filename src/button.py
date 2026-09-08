"""Push button driver with non-blocking debounce logic for MicroPython.

Target: Raspberry Pi Pico 2 / Waveshare RP2350-PiZero (RP2350)
Hardware: Momentary tactile switch tied to GND with internal pull-up.
Pressed = 0 (Logic LOW), Released = 1 (Logic HIGH).
"""

import time

# Host Python compatibility for MicroPython timing primitives
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.time() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda a, b: a - b

try:
    import machine
except ImportError:
    machine = None

from config import PIN_BUTTON, BUTTON_DEBOUNCE_MS


class DebouncedButton:
    """Non-blocking debounced button with edge detection, release lockout, and cooldown."""

    def __init__(
        self,
        pin_num=PIN_BUTTON,
        debounce_ms=BUTTON_DEBOUNCE_MS,
        cooldown_ms=350,
        pin=None,
    ):
        """Initialize the debounced button.

        Args:
            pin_num: GPIO pin number.
            debounce_ms: Debounce window in milliseconds.
            cooldown_ms: Minimum cooldown between successive press events.
            pin: Optional custom or mock Pin instance.
        """
        self.debounce_ms = debounce_ms
        self.cooldown_ms = cooldown_ms

        if pin is not None:
            self.pin = pin
        elif machine is not None:
            self.pin = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
        else:
            raise RuntimeError("machine module unavailable and no pin object provided")

        initial_val = self.pin.value()
        self._last_raw = initial_val
        self._debounced_state = initial_val
        self._last_change_time = time.ticks_ms()
        self._last_press_time = time.ticks_ms() - self.cooldown_ms
        self._pressed_event = False

    def update(self):
        """Poll the hardware pin, filter contact bounce, and detect falling edge."""
        now = time.ticks_ms()
        raw = self.pin.value()

        if raw != self._last_raw:
            self._last_change_time = now
            self._last_raw = raw

        if time.ticks_diff(now, self._last_change_time) >= self.debounce_ms:
            if raw != self._debounced_state:
                # Falling edge (HIGH -> LOW): Button pressed
                if self._debounced_state == 1 and raw == 0:
                    # Enforce cooldown lockout to reject release bounce
                    if time.ticks_diff(now, self._last_press_time) >= self.cooldown_ms:
                        self._pressed_event = True
                        self._last_press_time = now
                self._debounced_state = raw

        return self._pressed_event

    def was_pressed(self):
        """Check if a button press edge occurred, clearing the event flag."""
        if self._pressed_event:
            self._pressed_event = False
            return True
        return False

    def is_pressed(self):
        """Check if the button is currently held down."""
        return self._debounced_state == 0

    def raw_is_pressed(self):
        """Check instantaneous pin reading (0 = pressed when pull-up)."""
        return self.pin.value() == 0

