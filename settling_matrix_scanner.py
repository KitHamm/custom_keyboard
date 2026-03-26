import time
import digitalio
import keypad
from kmk.scanners import Scanner


class SettlingMatrixScanner(Scanner):
    """
    Custom matrix scanner that drives each row/column pin and waits
    settle_time_us before reading, eliminating ghost keypresses caused
    by capacitive coupling on long PCB traces.
    """

    def __init__(self, row_pins, column_pins, columns_to_anodes=False, settle_time_us=50):
        self._settle_time_us = settle_time_us
        self._columns_to_anodes = columns_to_anodes
        self._num_rows = len(row_pins)
        self._num_cols = len(column_pins)
        self._key_count = self._num_rows * self._num_cols
        self._state = bytearray(self._key_count)
        self._pending = []

        if columns_to_anodes:
            # Rows are driven, columns are sensed
            driven_pins = row_pins
            sensed_pins = column_pins
        else:
            # Columns are driven, rows are sensed
            driven_pins = column_pins
            sensed_pins = row_pins

        self._driven = []
        for pin in driven_pins:
            dio = digitalio.DigitalInOut(pin)
            dio.direction = digitalio.Direction.OUTPUT
            dio.value = True  # idle high
            self._driven.append(dio)

        self._sensed = []
        for pin in sensed_pins:
            dio = digitalio.DigitalInOut(pin)
            dio.direction = digitalio.Direction.INPUT
            dio.pull = digitalio.Pull.UP
            self._sensed.append(dio)

        super().__init__()

    @property
    def key_count(self):
        return self._key_count

    def scan_for_changes(self):
        if self._pending:
            return self._pending.pop(0)

        num_driven = len(self._driven)
        num_sensed = len(self._sensed)

        for d_idx, driven_pin in enumerate(self._driven):
            driven_pin.value = False  # drive active low
            time.sleep(self._settle_time_us / 1_000_000)

            for s_idx in range(num_sensed):
                pressed = not self._sensed[s_idx].value  # active low = pressed

                if self._columns_to_anodes:
                    # driven=rows, sensed=cols
                    key_num = d_idx * num_sensed + s_idx
                else:
                    # driven=cols, sensed=rows: key_num = row * num_cols + col
                    key_num = s_idx * num_driven + d_idx

                if bool(pressed) != bool(self._state[key_num]):
                    self._state[key_num] = pressed
                    self._pending.append(keypad.Event(key_num + self.offset, bool(pressed)))

            driven_pin.value = True  # deactivate

        if self._pending:
            return self._pending.pop(0)
        return None
