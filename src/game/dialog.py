import src.game.inputs as inputs


class Dialog:
    """Represents one panel of dialog"""

    def __init__(self, text, sprites=None):
        self.text = text
        self.sprites = sprites
        self.next = None

        self.scroll_pos = 0

    def set_next(self, next):
        self.next = next

    def get_next(self):
        return self.next

    def get_text(self):
        return self.text

    def is_done_scrolling(self):
        return self.scroll_pos >= len(self.get_text())

    def get_visible_sprite(self, gs):
        if self.sprites is not None and len(self.sprites) > 0:
            return self.sprites[(gs.anim_tick // 2) % len(self.sprites)]
        else:
            return None

    def get_visible_text(self):
        all_text = self.get_text()
        if self.scroll_pos >= len(all_text):
            return all_text
        else:
            return all_text[0:self.scroll_pos]


class DialogManager:

    def __init__(self):
        self._active_dialog = None
        self._scroll_freq = 2  # ticks per character

    def is_active(self):
        return self._active_dialog is not None

    def get_dialog(self):
        return self._active_dialog

    def set_dialog(self, dialog):
        if dialog is not None:
            print("setting dialog to: {}".format(dialog.get_text()))
        self._active_dialog = dialog

    def update(self, world, gs, input_state):
        if self.is_active():
            dialog = self._active_dialog
            if input_state.was_pressed(inputs.ENTER):
                if dialog.is_done_scrolling():
                    self.set_dialog(dialog.get_next())
                else:
                    dialog.scroll_pos = len(dialog.get_text())
            elif not dialog.is_done_scrolling() and gs.tick_counter % self._scroll_freq == 0:
                dialog.scroll_pos += 1



