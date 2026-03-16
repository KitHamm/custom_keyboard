from kmk.modules import Module


class MenuUpdater(Module):
    def __init__(self, menu):
        self.menu = menu

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        self.menu.tick()

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
