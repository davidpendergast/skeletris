import src.game.inputs as inputs
import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.events as events


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

    def is_active(self):
        return self._active_dialog is not None

    def get_dialog(self):
        return self._active_dialog

    def set_dialog(self, dialog, gs):
        if self._active_dialog is not None and self._active_dialog.is_cutscene():
            gs.event_queue().add(events.CutsceneEvent.new_end_event(self._active_dialog.get_cutscene_id()))

        if dialog is not None:
            if dialog.is_cutscene():
                gs.event_queue().add(events.CutsceneEvent.new_start_event(dialog.get_cutscene_id()))

        self._active_dialog = dialog

    def update(self, world, gs, input_state):
        if self.is_active():
            dialog = self._active_dialog
            if dialog.is_cutscene():
                cutscene = dialog
                if cutscene.is_finished():
                    self.set_dialog(cutscene.get_next(), gs)
                else:
                    cutscene.update(world, gs, input_state)
            else:
                if dialog.scroll_pos > 0 and input_state.was_pressed(inputs.ENTER):
                    if dialog.is_done_scrolling():
                        self.set_dialog(dialog.get_next(), gs)
                    else:
                        dialog.scroll_pos = len(dialog.get_text())
                elif not dialog.is_done_scrolling() and gs.tick_counter % self._scroll_freq == 0:
                    dialog.scroll_pos += 1


class Cutscene(Dialog):

    def __init__(self, cutscene_id, action_list):
        Dialog.__init__(self, "...")
        self.cutscene_id = cutscene_id
        self.action_list = action_list
        self._action_idx = 0
        self.scroll_pos = len(self.text)

    def update(self, world, gs, input_state):
        if self.is_finished():
            return
        else:
            current_action = self.action_list[self._action_idx]
            if current_action.is_finished() or input_state.was_pressed(inputs.ENTER):
                current_action.finalize(world, gs, input_state)
                self._action_idx += 1
            else:
                current_action.update(world, gs, input_state)

    def is_finished(self):
        return self._action_idx >= len(self.action_list)

    def is_cutscene(self):
        return True

    def get_cutscene_id(self):
        return self.cutscene_id


class CutSceneAction:

    def __init__(self):
        pass

    def is_finished(self):
        return True

    def update(self, world, gs, input_state):
        pass

    def finalize(self, world, gs, input_state):
        pass


class PauseCutSceneAction(CutSceneAction):

    def __init__(self, duration):
        CutSceneAction.__init__(self)
        self.tick_count = 0
        self.duration = duration

    def is_finished(self):
        return self.tick_count >= self.duration

    def update(self, world, gs, input_state):
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

    def finalize(self, world, gs, input_state):
        npc_entity = world.get_npc(self.npc_id)
        target_pos = ((self.target_cell[0] + 0.5) * world.cellsize(),
                      (self.target_cell[1] + 0.5) * world.cellsize())

        if npc_entity is not None:
            npc_entity.set_center(*target_pos)

    def update(self, world, gs, input_state):
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



