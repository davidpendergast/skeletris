import re
import random

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.events as events
import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
from src.game.inputs import InputState

import src.game.globalstate as gs


class Dialog:

    NEXT_UID = 0

    @staticmethod
    def _gen_uid():
        Dialog.NEXT_UID += 1
        return Dialog.NEXT_UID - 1

    """Represents one panel of dialog"""

    def __init__(self, text, sprites=None, left_side=True):
        """
        text: str to display.
        sprites: sprites to represent the speaker
        left_side: bool alignment of the speaker sprites
        """
        self.text = text
        self.sprites = sprites
        self.left_side = left_side

        self.next = None    # next Dialog after this one
        self.prev = None    # the Dialog that comes before this one

        self.scroll_pos = 0
        self.uid = Dialog._gen_uid()

    def reset(self):
        self.scroll_pos = 0

    def set_next(self, next_dialog):
        self.next = next_dialog

    def set_prev(self, prev_dialog):
        self.prev = prev_dialog

    def get_uid(self):
        return self.uid

    def get_speaker_id(self):
        return None

    def get_next(self):
        return self.next

    def get_prev(self):
        return self.prev

    def get_text(self):
        return self.text

    def get_sprite_side(self):
        return self.left_side

    def is_done_scrolling(self):
        return self.scroll_pos >= len(self.get_text())

    def get_visible_sprite(self):
        if self.sprites is not None and len(self.sprites) > 0:
            return self.sprites[(gs.get_instance().anim_tick // 4) % len(self.sprites)]
        else:
            return None

    def is_cutscene(self):
        return False

    def get_visible_text(self, invisible_sub=''):
        all_text = self.get_text()
        if self.scroll_pos >= len(all_text):
            return all_text
        else:
            if len(invisible_sub) == 0:
                return all_text[0:self.scroll_pos]
            else:
                visible_text = all_text[0:self.scroll_pos]
                invis_text = all_text[self.scroll_pos:]
                subbed_invis_text = Utils.replace_all_except(invis_text, invisible_sub, except_for=(" ", "\n"))
                return visible_text + subbed_invis_text

    @staticmethod
    def link_em_up(dialog_list):
        for i in range(0, len(dialog_list) - 1):
            d1 = dialog_list[i]
            d2 = dialog_list[i + 1]
            d1.set_next(d2)
            d2.set_prev(d1)
        return dialog_list[0]


class PlayerDialog(Dialog):

    PLAYER_ID = "PLAYER"

    def __init__(self, text):
        Dialog.__init__(self, text, sprites=spriteref.player_faces, left_side=True)

    def get_speaker_id(self):
        return PlayerDialog.PLAYER_ID


class NpcDialog(Dialog):

    def __init__(self, text, sprites=None, npc_id=None):
        if sprites is None and npc_id is not None:
            import src.game.npc as npc
            sprites = npc.get_sprites(npc_id)

        Dialog.__init__(self, text, sprites=sprites, left_side=False)
        self.npc_id = npc_id

    def get_speaker_id(self):
        return self.npc_id


class DialogManager:

    def __init__(self):
        self._active_dialog = None
        self._scroll_freq = 2  # ticks per character
        self._long_freq = {
            ".": 12,
            ",": 6,
            "!": 12,
            "?": 12
        }
        self.last_scroll_time = 0
        self.noise_freq = 6
        self.did_interact_this_tick = False

    def is_active(self):
        return self._active_dialog is not None

    def get_dialog(self):
        return self._active_dialog

    def set_dialog(self, dialog):
        if self._active_dialog is not None:
            uid = self._active_dialog.get_uid()
            gs.get_instance().add_event(events.DialogExitEvent(uid))

        if dialog is not None:
            dialog.reset()
            gs.get_instance().add_event(events.DialogStartEvent(dialog.get_uid()))

        self._active_dialog = dialog

    def interact(self):
        if self.is_active():
            self.did_interact_this_tick = True

    def update(self, world):
        if self.is_active():
            dialog = self._active_dialog

            if (dialog.scroll_pos > 0 or len(dialog.get_text()) == 0) and self.did_interact_this_tick:
                if dialog.is_done_scrolling():
                    self.set_dialog(dialog.get_next())
                    sound_effects.play_sound(soundref.dialog_next)
                else:
                    dialog.scroll_pos = len(dialog.get_text())
                    sound_effects.play_sound(soundref.dialog_skip)

            elif not dialog.is_done_scrolling():
                cur_delay = gs.get_instance().tick_counter - self.last_scroll_time

                d_text = dialog.get_text()
                pos = dialog.scroll_pos
                delay = self._scroll_freq

                # it's trendy to pause longer on punctuation
                if 0 <= pos-1 < len(d_text):
                    last_char = d_text[pos-1]

                    # but not when it's in the middle of an acronym
                    if not self._is_part_of_an_acronym(d_text, pos) and last_char in self._long_freq:
                        delay = self._long_freq[last_char]

                if cur_delay >= delay:
                    dialog.scroll_pos += 1
                    self.last_scroll_time = gs.get_instance().tick_counter

                if gs.get_instance().tick_counter % self.noise_freq == 0:
                    sound_effects.play_sound(soundref.dialog_click)

        self.did_interact_this_tick = False

    def _is_part_of_an_acronym(self, text, index):
        """
            returns: True if index is contained by a substring of text whose form is: 'X.X.'
        """
        for offset in (-3, -2, -1, 0):
            if self._is_part_of_an_acronym_helper(text, index + offset):
                return True

        return False

    def _is_part_of_an_acronym_helper(self, text, start_index):
        if start_index < 0 or start_index + 3 >= len(text):
            return False

        for i in (start_index, start_index + 2):
            char_at = text[i]
            if not char_at.isalpha():
                return False

        for i in (start_index + 1, start_index + 3):
            char_at = text[i]
            if char_at != ".":
                return False

        return True


# TODO cutscenes aren't used, delete?

class Cutscene(Dialog):

    def __init__(self, action_list):
        Dialog.__init__(self, "...")
        self.action_list = action_list
        self._action_idx = 0
        self.scroll_pos = len(self.text)

    def update(self, world):
        if self.is_finished():
            return
        else:
            input_state = InputState.get_instance()
            current_action = self.action_list[self._action_idx]

            sttgs = gs.get_instance().settings()
            pressed_skip = input_state.was_pressed(sttgs.all_dialog_dismiss_keys())

            if current_action.is_finished() or (pressed_skip and current_action.is_skippable()):
                current_action.finalize(world)
                self._action_idx += 1
            else:
                current_action.update(world)

    def is_finished(self):
        return self._action_idx >= len(self.action_list)

    def is_cutscene(self):
        return True

    def reset(self):
        self._action_idx = 0


class CutSceneAction:

    def __init__(self):
        pass

    def is_finished(self):
        return True

    def update(self, world):
        pass

    def is_skippable(self):
        return True

    def finalize(self, world):
        pass


class PauseCutSceneAction(CutSceneAction):

    def __init__(self, duration):
        CutSceneAction.__init__(self)
        self.tick_count = 0
        self.duration = duration

    def is_finished(self):
        return self.tick_count >= self.duration

    def update(self, world):
        self.tick_count += 1


class NpcWalkCutSceneAction(CutSceneAction):

    def __init__(self, npc_id, grid_xy, move_speed=1):
        CutSceneAction.__init__(self)
        self.npc_id = npc_id
        self.target_cell = grid_xy
        self.move_speed = move_speed
        self.finished = False

    def is_finished(self):
        return self.finished

    def finalize(self, world):
        npc_entity = world.get_npc(self.npc_id)
        target_pos = ((self.target_cell[0] + 0.5) * world.cellsize(),
                      (self.target_cell[1] + 0.5) * world.cellsize())

        if npc_entity is not None:
            npc_entity.set_center(*target_pos)

    def update(self, world):
        npc_entity = world.get_npc(self.npc_id)

        if npc_entity is None:
            print("ERROR: NPC {} is missing from cutscene".format(self.npc_id))
            self.finished = True
            return

        center = npc_entity.center()
        target_pos = ((self.target_cell[0] + 0.5) * world.cellsize(),
                      (self.target_cell[1] + 0.5) * world.cellsize())

        dist = Utils.dist(center, target_pos)
        if dist <= self.move_speed:
            npc_entity.set_center(*target_pos)
            self.finished = True
        else:
            step = Utils.set_length(Utils.sub(target_pos, center), self.move_speed)
            npc_entity.move(*step)


class CustomCutsceneAction(CutSceneAction):

    def __init__(self, name):
        CutSceneAction.__init__(self)
        self.name = name

    def is_finished(self):
        return True

    def update(self, world):
        pass

    def finalize(self, world):
        pass

    def __str__(self):
        return "CustomCutsceneAction[{}]".format(self.name)



