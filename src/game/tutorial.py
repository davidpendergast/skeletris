import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
import src.game.globalstate as gs
import src.game.events as events
import src.game.gameengine as gameengine
import src.game.settings as settings
from src.utils.util import Utils


class TutorialID:
    MOVE_AND_INV = "move_and_inv"


class TutorialPlugin:
    """
        Basically a thing you can 'plug into' a world that creates a series of
        popups that guide the player through some sequence of actions.
    """

    def __init__(self, tut_id, stages):
        self.tut_id = tut_id
        self.stages = stages

    def get_id(self):
        return self.tut_id

    def get_active_stage(self):
        for s in self.stages:
            if not s.is_complete():
                return s
        return None

    def is_complete(self):
        return self.get_active_stage() is None

    def update(self):
        active_stage = self.get_active_stage()
        if active_stage is not None:
            has_started = active_stage.is_started()
            active_stage.update()

            if active_stage.is_complete():
                if self.get_active_stage() is None:
                    # we just completed the tutorial
                    # TODO - tell settings to save it
                    pass

                active_stage.cleanup()

                # don't play sound if the tutorial was silently completed
                if has_started:
                    sound_effects.play_sound(soundref.tutorial_stage_complete)

    def cleanup(self):
        active_stage = self.get_active_stage()
        if active_stage is not None:
            active_stage.cleanup()


class TutorialStage:

    def __init__(self):
        self._ticks_waiting = 0
        self._ticks_started = 0
        self._is_waiting = True
        self._is_complete = False

    def is_waiting(self):
        return self._is_waiting

    def is_started(self):
        return not self.is_waiting() and not self.is_complete()

    def is_complete(self):
        return self._is_complete

    def start(self):
        """should only be called by the stage's update method."""
        self._is_waiting = False

    def complete(self):
        """should only be called by the stage's update method."""
        self._is_complete = True

    def get_ticks_started(self):
        return self._ticks_started

    def get_ticks_waiting(self):
        return self._ticks_waiting

    def reset_ticks_waiting(self):
        self._ticks_waiting = 0

    def update(self):
        if self.is_complete():
            return
        elif self.is_started():
            self._ticks_started += 1
        else:
            self._ticks_waiting += 1

    def cleanup(self):
        pass

    def get_message(self):
        return "Do the thing! Quick!"


class EntityNotificationTutorialStage(TutorialStage):

    def __init__(self):
        TutorialStage.__init__(self)
        self._hover_text_ent_id = None

    def _destroy_text_entity(self):
        if self._hover_text_ent_id is not None:
            w = gs.get_instance().get_world()
            if w is not None:
                ent = w.get_entity(self._hover_text_ent_id, onscreen=False)
                if ent is not None:
                    w.remove(ent)
            self._hover_text_ent_id = None

    def update_hover_text(self, entity, message):
        if entity is None or message is None or len(message) == 0:
            self._destroy_text_entity()
        else:
            w = gs.get_instance().get_world()
            if w is None:
                return

            hover_entity = None
            if self._hover_text_ent_id is not None:
                hover_entity = w.get_entity(self._hover_text_ent_id, onscreen=False)

                if hover_entity is None:
                    print("WARN: looks like a tutorial text entity got deleted by accident?")
                    self._hover_text_ent_id = None

            if hover_entity is None:
                import src.world.entities as entities
                hover_entity = entities.HoverTextEntity(message, entity, offset=(0, -48))
                w.add(hover_entity)
                self._hover_text_ent_id = hover_entity.get_uid()

            hover_entity.set_target_entity(entity)
            hover_entity.set_text(message)

    def cleanup(self):
        self._destroy_text_entity()

    def get_target_entity(self):
        return None

    def update(self):
        super().update()


class HowToMoveStage(EntityNotificationTutorialStage):

    def __init__(self, delay):
        EntityNotificationTutorialStage.__init__(self)
        self.wait_delay = delay

    def update(self):
        super().update()

        p = self.get_target_entity()
        if p is None:
            return

        def is_player_move_action(act_evt):
            if act_evt.get_action_type() == gameengine.ActionType.MOVE_TO:
                if act_evt.get_uid() == p.get_uid():
                    return True
            return False

        if gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                     predicate=is_player_move_action):
            self.complete()
            return

        if not self.is_started():
            if self.get_ticks_waiting() >= self.wait_delay:
                self.start()

        if self.is_started():
            self.update_hover_text(p, self.get_message())

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        return p

    def get_message(self):
        keystr = ""
        keys = [settings.KEY_UP, settings.KEY_LEFT, settings.KEY_DOWN, settings.KEY_RIGHT]
        for k in keys:
            key_val = gs.get_instance().settings().get(k)
            if len(key_val) > 0:
                keystr = keystr + Utils.stringify_key(key_val[0])

        return "Use [{}] to move.".format(keystr)


class HowToPickUpItemStage(EntityNotificationTutorialStage):

    def __init__(self, delay=60):
        super().__init__()
        self.delay = delay

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if w is None or p is None:
            return None
        else:
            for it in w.entities_in_circle(p.center(), w.cellsize() * 1.5, onscreen=True,
                                           cond=lambda e: e.is_item()):
                it_pos = w.to_grid_coords(*it.center())
                pickup_act = gameengine.PickUpItemAction(p, it.get_item(), it_pos)
                if pickup_act.is_possible(w):
                    return it
            return None

    def get_message(self):
        return "Use mouse to pick up items."

    def update(self):
        super().update()

        w, p = gs.get_instance().get_world_and_player()
        if w is None or p is None:
            return

        def is_item_pickup_action(act_evt):
            if act_evt.get_action_type() == gameengine.ActionType.PICKUP_ITEM:
                if act_evt.get_uid() == p.get_uid():
                    return True
            return False

        if gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                     predicate=is_item_pickup_action):
            self.complete()
            return

        item_ent = self.get_target_entity()
        if item_ent is None:
            self.update_hover_text(None, "")

            if self.is_waiting():
                self.reset_ticks_waiting()

        if item_ent is not None:
            if self.is_waiting() and self.get_ticks_waiting() >= self.delay:
                self.start()

            if self.is_started():
                self.update_hover_text(p, self.get_message())
            else:
                self.update_hover_text(None, "")


class TutorialFactory:

    @staticmethod
    def get(tut_id):
        if tut_id == TutorialID.MOVE_AND_INV:
            return TutorialPlugin(tut_id, [
                HowToMoveStage(90),
                HowToPickUpItemStage()
            ])

        return None




