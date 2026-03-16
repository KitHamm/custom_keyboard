import usb_hid
from kmk.extensions import Extension
from menu_ui import _idle_state

_NUMLOCK = 0x01
_CAPSLOCK = 0x02


class LCDLockStatus(Extension):
    def __init__(self, menu):
        self.menu = menu
        self.hid = None
        self._last_caps = None
        self._last_num = None

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def during_bootup(self, keyboard):
        for device in usb_hid.devices:
            if device.usage == usb_hid.Device.KEYBOARD.usage:
                self.hid = device
                break

    def before_matrix_scan(self, sandbox):
        pass

    def after_matrix_scan(self, sandbox):
        pass

    def before_hid_send(self, sandbox):
        pass

    def after_hid_send(self, sandbox):
        if self.hid is None:
            return
        try:
            report = self.hid.get_last_received_report()
            if report is None:
                return
            leds = report[0]
            caps = bool(leds & _CAPSLOCK)
            num = bool(leds & _NUMLOCK)
            changed = False
            if caps != self._last_caps:
                self._last_caps = caps
                _idle_state['caps'] = caps
                changed = True
            if num != self._last_num:
                self._last_num = num
                _idle_state['num'] = num
                changed = True
            if changed and self.menu.get_ui_state() == 'idle':
                self.menu.return_to_idle()
        except Exception as e:
            print(f"[LCDLockStatus] HID report error: {e}")

    def on_powersave_enable(self, sandbox):
        pass

    def on_powersave_disable(self, sandbox):
        pass
