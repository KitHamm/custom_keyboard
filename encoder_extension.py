from kmk.modules.encoder import EncoderHandler


class EncoderHandlerWithFuncs(EncoderHandler):
    def on_move_do(self, keyboard, encoder_id, state):
        if self.map:
            layer_id = keyboard.active_layers[0]
            key_index = 0 if state['direction'] == -1 else 1
            key = self.map[layer_id][encoder_id][key_index]
            if callable(key):
                key()
            else:
                keyboard.tap_key(key)

    def on_button_do(self, keyboard, encoder_id, state):
        if state['is_pressed'] is True:
            layer_id = keyboard.active_layers[0]
            key = self.map[layer_id][encoder_id][2]
            if callable(key):
                key()
            else:
                keyboard.tap_key(key)
