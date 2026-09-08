"""SSD1306 OLED display controller and 8-row metric layout view.

Target: Raspberry Pi Pico 2
Display: 128x64 Monochrome OLED via I2C (I2C1, SDA=GP2, SCL=GP3).
"""

try:
    import machine
except ImportError:
    machine = None

try:
    from lib.ssd1306 import SSD1306_I2C
except ImportError:
    try:
        from ssd1306 import SSD1306_I2C
    except ImportError:
        SSD1306_I2C = None

from config import (
    APP_TITLE,
    I2C_ID,
    PIN_I2C_SDA,
    PIN_I2C_SCL,
    I2C_FREQ,
    OLED_WIDTH,
    OLED_HEIGHT,
    OLED_I2C_ADDR,
    CO_MG_M3_FACTOR,
)


class OLEDView:
    """Formats and renders the 8-row metric layout on an SSD1306 128x64 OLED."""

    LINE_HEIGHT = 8
    MAX_CHARS_PER_LINE = 16

    def __init__(
        self,
        i2c=None,
        oled=None,
        width=OLED_WIDTH,
        height=OLED_HEIGHT,
        addr=OLED_I2C_ADDR,
    ):
        self.width = width
        self.height = height
        self.addr = addr

        if oled is not None:
            self.oled = oled
        elif SSD1306_I2C is not None:
            if i2c is None and machine is not None:
                i2c = machine.I2C(
                    I2C_ID,
                    sda=machine.Pin(PIN_I2C_SDA),
                    scl=machine.Pin(PIN_I2C_SCL),
                    freq=I2C_FREQ,
                )
            if i2c is not None:
                self.oled = SSD1306_I2C(self.width, self.height, i2c, addr=self.addr)
            else:
                raise RuntimeError("No I2C bus available to initialize SSD1306")
        else:
            raise RuntimeError("SSD1306 driver unavailable and no display object provided")

    def clear(self):
        """Clear the OLED display buffer."""
        self.oled.fill(0)

    def show(self):
        """Push display buffer contents to the physical screen."""
        self.oled.show()

    def format_lines(
        self,
        state="MONITORING",
        current_ppm=0.0,
        min_ppm=None,
        max_ppm=None,
        mg_m3=None,
        btn_pressed=False,
        is_digital=False,
        btn_prompt="Press to reset",
        # Backwards-compatibility kwargs
        current_v=None,
        min_v=None,
        max_v=None,
        record_count=None,
        session_file=None,
        interval_s=None,
    ):
        """Generate 8 formatted text lines (each max 16 characters)."""
        # If PPM is not provided but voltage is, keep a fallback
        if current_v is not None and current_ppm == 0.0:
            current_ppm = current_v

        if mg_m3 is None:
            mg_m3 = current_ppm * CO_MG_M3_FACTOR

        # Line 0: Application Title (no divider line)
        line0 = APP_TITLE[: self.MAX_CHARS_PER_LINE]

        # Line 1: State or notification override
        if state.startswith("[") or state.startswith("ERR") or state.startswith("SAVED"):
            line1 = state[: self.MAX_CHARS_PER_LINE]
        else:
            line1 = "[{}]".format(state)[: self.MAX_CHARS_PER_LINE]

        # Line 2: Sensor identification
        line2 = "MQ-7 (DIGITAL)" if is_digital else "MQ-7 CO Sensor"
        line2 = line2[: self.MAX_CHARS_PER_LINE]

        # Line 3: Current concentration / digital status
        if is_digital:
            co_status = "ALERT!" if current_ppm == 0.0 else "CLEAR"
            line3 = "CO: {}".format(co_status)[: self.MAX_CHARS_PER_LINE]
        else:
            line3 = "Cur: {:>5.1f} PPM".format(current_ppm)[: self.MAX_CHARS_PER_LINE]

        # Line 4: Minimum concentration / pin info
        if is_digital:
            line4 = "Pin: GP26 (DO)"[: self.MAX_CHARS_PER_LINE]
        else:
            if min_ppm is not None:
                line4 = "Min: {:>5.1f} PPM".format(min_ppm)[: self.MAX_CHARS_PER_LINE]
            else:
                line4 = "Min:    -- PPM"[: self.MAX_CHARS_PER_LINE]

        # Line 5: Maximum concentration / digital mode
        if is_digital:
            line5 = "Mode: Digital"[: self.MAX_CHARS_PER_LINE]
        else:
            if max_ppm is not None:
                line5 = "Max: {:>5.1f} PPM".format(max_ppm)[: self.MAX_CHARS_PER_LINE]
            else:
                line5 = "Max:    -- PPM"[: self.MAX_CHARS_PER_LINE]

        # Line 6: Mass concentration (mg/m3)
        if is_digital:
            line6 = "Threshold Alert"[: self.MAX_CHARS_PER_LINE]
        else:
            line6 = "Mass:{:>5.1f} mg/m3".format(mg_m3)[: self.MAX_CHARS_PER_LINE]

        # Line 7: Button action / prompt
        if btn_pressed:
            line7 = "Resetting..."[: self.MAX_CHARS_PER_LINE]
        else:
            line7 = btn_prompt[: self.MAX_CHARS_PER_LINE]

        return [line0, line1, line2, line3, line4, line5, line6, line7]

    def render(
        self,
        state="MONITORING",
        current_ppm=0.0,
        min_ppm=None,
        max_ppm=None,
        mg_m3=None,
        btn_pressed=False,
        is_digital=False,
        btn_prompt="Press to reset",
        **kwargs
    ):
        """Format metrics, render all 8 lines to buffer, and update screen."""
        lines = self.format_lines(
            state=state,
            current_ppm=current_ppm,
            min_ppm=min_ppm,
            max_ppm=max_ppm,
            mg_m3=mg_m3,
            btn_pressed=btn_pressed,
            is_digital=is_digital,
            btn_prompt=btn_prompt,
            **kwargs
        )

        self.clear()
        for idx, text in enumerate(lines):
            y = idx * self.LINE_HEIGHT
            self.oled.text(text, 0, y)
        self.show()

    def render_lines(self, lines):
        """Render an arbitrary list of strings (up to 8 lines, 16 chars max per line)."""
        self.clear()
        for idx, text in enumerate(lines[:8]):
            y = idx * self.LINE_HEIGHT
            self.oled.text(str(text)[: self.MAX_CHARS_PER_LINE], 0, y)
        self.show()

    def render_error(self, message):
        """Display an error banner on the screen."""
        self.clear()
        self.oled.text("!! ERROR !!", 0, 0)
        self.oled.text("-" * self.MAX_CHARS_PER_LINE, 0, 8)

        # Split message into chunks of up to 16 characters across remaining lines
        for i in range(6):
            start = i * self.MAX_CHARS_PER_LINE
            chunk = message[start : start + self.MAX_CHARS_PER_LINE]
            if chunk:
                self.oled.text(chunk, 0, 16 + (i * self.LINE_HEIGHT))
        self.show()
