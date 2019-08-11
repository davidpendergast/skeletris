import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
import src.game.globalstate as gs
import src.game.events as events
import src.game.gameengine as gameengine
import src.game.settings as settings
from src.utils.util import Utils


class TutorialID:
    MOVE_AND_INV = "how_to_move_and_inv"
    SKIP_TURN_AND_FIGHT = "how_to_skip_turn"
    HOW_TO_USE_POTIONS = "how_to_use_potions"
    HOW_TO_THROW_ITEMS = "how_to_throw_items"
    HOW_TO_TRADE = "how_to_trade"


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

    def __init__(self, delay=60):
        TutorialStage.__init__(self)
        self.delay = delay
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

    def update(self):
        super().update()

        if not self.is_complete() and self.test_completed():
            self.complete()
            return

        target_ent = self.get_target_entity()
        message = self.get_message()

        if target_ent is None or message is None or len(message) == 0:
            self.update_hover_text(None, "")

            if self.is_waiting():
                self.reset_ticks_waiting()

        if not self.is_started():
            if self.get_ticks_waiting() >= self.delay:
                self.start()

        if self.is_started():
            self.update_hover_text(target_ent, message)

    def get_target_entity(self):
        """Override this to return a valid target entity for the tutorial (if there is one)."""
        return None

    def test_completed(self):
        """Override this to test for a completion condition."""
        return False

    def get_message(self):
        """Override this to provide the hover text's message."""
        return super().get_message()


class HowToMoveStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        return p

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        def _is_player_move_action(act_evt):
            if act_evt.get_action_type() == gameengine.ActionType.MOVE_TO:
                if act_evt.get_uid() == p.get_uid():
                    return True
            return False

        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                         predicate=_is_player_move_action)

    def get_message(self):
        keystr = ""
        keys = [settings.KEY_UP, settings.KEY_LEFT, settings.KEY_DOWN, settings.KEY_RIGHT]
        for k in keys:
            key_val = gs.get_instance().settings().get(k)
            if len(key_val) > 0:
                keystr = keystr + Utils.stringify_key(key_val[0])

        return "Use [{}] to move.".format(keystr)


class HowToPickUpItemStage(EntityNotificationTutorialStage):

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
                    # considered putting the hover text on the item itself, but it feels kinda awkward.
                    return p
            return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        def is_item_pickup_action(act_evt):
            if act_evt.get_action_type() == gameengine.ActionType.PICKUP_ITEM:
                if act_evt.get_uid() == p.get_uid():
                    return True
            return False

        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                         predicate=is_item_pickup_action)

    def get_message(self):
        return "Use mouse to pick up items."


class HowToOpenInventoryPanelStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        return p

    def test_completed(self):
        from src.ui.ui import SidePanelTypes
        return gs.get_instance().get_active_sidepanel() == SidePanelTypes.INVENTORY

    def get_message(self):
        inv_keys = gs.get_instance().settings().inventory_key()
        if len(inv_keys) > 0:
            inv_key = Utils.stringify_key(inv_keys[0])
        else:
            inv_key = "None"
        return "Press [{}] to open Inventory.".format(inv_key)


class HowToEquipItemStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is not None:
            held_item = p.get_actor_state().held_item
            from src.items.item import ItemTags
            if held_item is not None and held_item.get_type().has_tag(ItemTags.EQUIPMENT):
                return p
        return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        all_equipped = [e for e in p.get_actor_state().inventory().all_equipped_items()]
        return len(all_equipped) > 0

    def get_message(self):
        return "Place the item into the Equipment grid."


class HowToRotateItemStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is not None:
            held_item = p.get_actor_state().held_item
            from src.items.item import ItemTags
            if held_item is not None and held_item.can_rotate():
                return p
        return None

    def test_completed(self):
        return gs.get_instance().event_queue().has_event(types=events.EventType.ROTATED_ITEM)

    def get_message(self):
        rotate_keys = gs.get_instance().settings().rotate_cw_key()
        if len(rotate_keys) > 0:
            rotate_key = Utils.stringify_key(rotate_keys[0])
        else:
            rotate_key = "None"

        return "Press [{}] to rotate the item.".format(rotate_key)


class HowToSkipTurnStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        return p

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        def _is_skip_turn_action(act_evt):
            if act_evt.get_action_type() == gameengine.ActionType.SKIP_TURN:
                if act_evt.get_uid() == p.get_uid():
                    return True
            return False

        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                         predicate=_is_skip_turn_action)

    def get_message(self):
        skip_keys = gs.get_instance().settings().skip_turn_key()
        if len(skip_keys) > 0:
            skip_key = Utils.stringify_key(skip_keys[0])
        else:
            skip_key = "None"

        return "Press [{}] to skip turn.".format(skip_key)


class TutorialFactory:

    @staticmethod
    def get(tut_id):
        if tut_id == TutorialID.MOVE_AND_INV:
            return TutorialPlugin(tut_id, [
                HowToMoveStage(delay=90),
                HowToPickUpItemStage(),
                HowToRotateItemStage(delay=30),
                HowToOpenInventoryPanelStage(),
                HowToEquipItemStage(delay=30),
            ])
        elif tut_id == TutorialID.SKIP_TURN_AND_FIGHT:
            return TutorialPlugin(tut_id, [
                HowToSkipTurnStage(delay=60)
            ])
        elif tut_id == TutorialID.HOW_TO_USE_POTIONS:
            pass
        elif tut_id == TutorialID.HOW_TO_THROW_ITEMS:
            pass


        return None




