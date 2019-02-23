import re

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.events as events
import src.game.sound_effects as sound_effects

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
        text: str to display. options
        options: list of strings
        sprites: sprites to represent the speaker
        left_side: bool alignment of the speaker sprites
        """
        self.text = text
        self.sprites = sprites
        self.next = None
        self.left_side = left_side

        self.selected_opt_idx = 0
        self.nexts = {}  # int opt_idx -> Dialog

        self.scroll_pos = 0
        self.uid = Dialog._gen_uid()

    def reset(self):
        self.scroll_pos = 0
        self.selected_opt_idx = 0

    def build_listener(self, action, single_use=True):
        return events.EventListener(action,
                                    events.EventType.DIALOG_EXIT,
                                    lambda e: e.get_uid() == self.get_uid(),
                                    single_use=single_use)

    def get_options(self, mangled_text=None):
        text = self.text if mangled_text is None else mangled_text
        res = re.findall("\{[^\{]*\}", self.text)
        return list(res)

    def set_next(self, next_dialog, opt_idx=0):
        self.nexts[opt_idx] = next_dialog

    def get_uid(self):
        return self.uid

    def get_next(self, opt_idx=None):
        idx = opt_idx if opt_idx is not None else self.selected_opt_idx
        if idx in self.nexts:
            return self.nexts[idx]
        else:
            return None

    def get_text(self):
        return self.text

    def get_selected_opt_idx(self):
        return self.selected_opt_idx

    def set_selected_opt_idx(self, val):
        self.selected_opt_idx = val

    def get_sprite_side(self):
        return self.left_side

    def is_done_scrolling(self):
        return self.scroll_pos >= len(self.get_text())

    def get_visible_sprite(self):
        if self.sprites is not None and len(self.sprites) > 0:
            return self.sprites[(gs.get_instance().anim_tick // 2) % len(self.sprites)]
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
        self._long_freq = {
            ".": 12,
            ",": 6,
            "!": 12,
            "?": 12
        }
        self.last_scroll_time = 0
        self.noise_freq = 6

    def is_active(self):
        return self._active_dialog is not None

    def get_dialog(self):
        return self._active_dialog

    def set_dialog(self, dialog):
        print("INFO: setting dialog to" + str(dialog))
        if self._active_dialog is not None:
            opt_idx = self._active_dialog.get_selected_opt_idx()
            uid = self._active_dialog.get_uid()
            gs.get_instance().event_queue().add(events.DialogExitEvent(uid, opt_idx))

        if dialog is not None:
            dialog.reset()

        self._active_dialog = dialog

    def update(self, world, input_state):
        if self.is_active():
            dialog = self._active_dialog
            if dialog.is_cutscene():
                cutscene = dialog
                if cutscene.is_finished():
                    self.set_dialog(cutscene.get_next())
                else:
                    cutscene.update(world, input_state)
            else:
                if dialog.scroll_pos > 0 and input_state.was_pressed(gs.get_instance().settings().interact_key()):
                    if dialog.is_done_scrolling():
                        self.set_dialog(dialog.get_next())
                    else:
                        dialog.scroll_pos = len(dialog.get_text())

                elif not dialog.is_done_scrolling():
                    cur_delay = gs.get_instance().tick_counter - self.last_scroll_time

                    # it's trendy to pause longer on punctuation
                    d_text = dialog.get_text()
                    pos = dialog.scroll_pos
                    delay = self._scroll_freq
                    if 0 <= pos-1 < len(d_text):
                        last_char = d_text[pos-1]
                        if last_char in self._long_freq:
                            delay = self._long_freq[last_char]

                    if cur_delay >= delay:
                        dialog.scroll_pos += 1
                        self.last_scroll_time = gs.get_instance().tick_counter

                    if gs.get_instance().tick_counter % self.noise_freq == 0:
                        sound_effects.play_sound(sound_effects.Effects.CLICK2)

                    # when we uncover the first option, skip to end
                    if not dialog.is_done_scrolling() and dialog.get_text()[dialog.scroll_pos] == '{':
                        dialog.scroll_pos = len(dialog.get_text())
                else:
                    num_options = len(dialog.get_options())
                    if dialog.is_done_scrolling() and num_options > 1:
                        cur_option = dialog.get_selected_opt_idx()
                        if input_state.was_pressed(gs.get_instance().settings().left_key()):
                            dialog.set_selected_opt_idx((cur_option - 1) % num_options)
                        if input_state.was_pressed(gs.get_instance().settings().right_key()):
                            dialog.set_selected_opt_idx((cur_option + 1) % num_options)
                        if input_state.was_pressed(gs.get_instance().settings().up_key()):
                            dialog.set_selected_opt_idx((cur_option - 1) % num_options)
                        if input_state.was_pressed(gs.get_instance().settings().down_key()):
                            dialog.set_selected_opt_idx((cur_option + 1) % num_options)


class Cutscene(Dialog):

    def __init__(self, action_list):
        Dialog.__init__(self, "...")
        self.action_list = action_list
        self._action_idx = 0
        self.scroll_pos = len(self.text)

    def update(self, world, input_state):
        if self.is_finished():
            return
        else:
            current_action = self.action_list[self._action_idx]
            if current_action.is_finished() or input_state.was_pressed(gs.get_instance().settings().interact_key()):
                current_action.finalize(world, input_state)
                self._action_idx += 1
            else:
                current_action.update(world, input_state)

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

    def update(self, world, input_state):
        pass

    def finalize(self, world, input_state):
        pass


class PauseCutSceneAction(CutSceneAction):

    def __init__(self, duration):
        CutSceneAction.__init__(self)
        self.tick_count = 0
        self.duration = duration

    def is_finished(self):
        return self.tick_count >= self.duration

    def update(self, world, input_state):
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

    def finalize(self, world, input_state):
        npc_entity = world.get_npc(self.npc_id)
        target_pos = ((self.target_cell[0] + 0.5) * world.cellsize(),
                      (self.target_cell[1] + 0.5) * world.cellsize())

        if npc_entity is not None:
            npc_entity.set_center(*target_pos)

    def update(self, world, input_state):
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
        self.name = name

    def is_finished(self):
        return True

    def update(self, world, input_state):
        pass

    def finalize(self, world, input_state):
        pass

    def __str__(self):
        return "CustomCutsceneAction[{}]".format(self.name)


