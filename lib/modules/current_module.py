import time
from kmk.modules import Module


class CurrentMonitor(Module):
    def __init__(self, ina=None):
        self.ina = ina
        self.current = 0.0
        self._last_poll = 0

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        now = time.monotonic()
        if self.ina and now - self._last_poll >= 0.25:
            self._last_poll = now
            try:
                self.current = self.ina.current
            except Exception as e:
                print(f"[CurrentMonitor] INA219 read error: {e}")

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass
