import src.game.inputs as inputs
import src.game.spriteref as spriteref


class Dialog:
    """Represents one panel of dialog"""

    def __init__(self, text, sprites=None, left_side=True):
        """
        text: str to display
        sprites: sprites to represent the speaker
        left_side: bool alignment of the speaker sprites
        """
        self.text = text
        self.sprites = sprites
        self.next = None
        self.left_side = left_side

        self.scroll_pos = 0

    def set_next(self, next):
        self.next = next

    def get_next(self):
        return self.next

    def get_text(self):
        return self.text

    def get_sprite_side(self):
        return self.left_side

    def is_done_scrolling(self):
        return self.scroll_pos >= len(self.get_text())

    def get_visible_sprite(self, gs):
        if self.sprites is not None and len(self.sprites) > 0:
            return self.sprites[(gs.anim_tick // 2) % len(self.sprites)]
        else:
            return None

    def get_visible_text(self, invisible_sub=''):
        all_text = self.get_text()
        if self.scroll_pos >= len(all_text):
            return all_text
        else:
            if len(invisible_sub) == 0:
                return all_text[0:self.scroll_pos]
            else:
                visible_text = all_text[0:self.scroll_pos]
                invisible_text = all_text[self.scroll_pos:]
                subbed_invis_text = "".join(x if (x == " " or x == "\n") else invisible_sub for x in invisible_text)
                return visible_text + subbed_invis_text

    @staticmethod
    def link_em_up(dialog_list):
        for i in range(0, len(dialog_list) - 1):
            d1 = dialog_list[i]
            d2 = dialog_list[i + 1]
            d1.set_next(d2)
        return dialog_list[0]


class PlayerDialog(Dialog):

    def __init__(self, text):
        Dialog.__init__(self, text, sprites=spriteref.player_faces, left_side=True)


class NpcDialog(Dialog):

    def __init__(self, text, sprites):
        Dialog.__init__(self, text, sprites=sprites, left_side=False)


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
            if dialog.scroll_pos > 0 and input_state.was_pressed(inputs.ENTER):
                if dialog.is_done_scrolling():
                    self.set_dialog(dialog.get_next())
                else:
                    dialog.scroll_pos = len(dialog.get_text())
            elif not dialog.is_done_scrolling() and gs.tick_counter % self._scroll_freq == 0:
                dialog.scroll_pos += 1



