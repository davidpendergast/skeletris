import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
import src.game.globalstate as gs
import src.game.events as events
import src.game.gameengine as gameengine
import src.game.settings as settings
from src.utils.util import Utils
from src.items.item import ItemTags
import src.game.constants as constants


_ALL_TUTORIAL_IDS = []


def _make_tut_id(tut_id):
    if tut_id is not None:
        _ALL_TUTORIAL_IDS.append(tut_id)
    return tut_id


class TutorialID:
    HOW_TO_MOVE = _make_tut_id("how_to_move")
    HOW_TO_EQUIP = _make_tut_id("how_to_equip")
    HOW_TO_SKIP = _make_tut_id("how_to_skip_turn")
    HOW_TO_OPEN_INVENTORY = _make_tut_id("how_to_open_inv")
    HOW_TO_USE_POTIONS = _make_tut_id("how_to_use_potions")
    HOW_TO_THROW_ITEMS = None  # _make_tut_id("how_to_throw_items")
    HOW_TO_ROTATE = _make_tut_id("how_to_rotate")
    HOW_TO_OPEN_MAP = _make_tut_id("how_to_open_map")

    @staticmethod
    def all_ids():
        for t in _ALL_TUTORIAL_IDS:
            yield t


class TutorialPlugin:
    """
        Basically a thing you can 'plug into' a world that creates a series of
        popups that guide the player through some sequence of actions.
    """

    def __init__(self, tut_id, min_level, stages):
        self.tut_id = tut_id
        self.min_level = min_level
        self.stages = stages

    def __repr__(self):
        return self.tut_id

    def get_id(self):
        return self.tut_id

    def get_min_level(self):
        return self.min_level

    def get_active_stage(self):
        for s in self.stages:
            if not s.is_complete():
                return s
        return None

    def is_ready(self):
        a = self.get_active_stage()
        if a is None or a.is_ready() or a.is_started():
            return True

    def is_complete(self):
        return self.get_active_stage() is None

    def update(self):
        active_stage = self.get_active_stage()
        if active_stage is not None:
            has_started = active_stage.is_started()
            active_stage.update()

            if active_stage.is_complete():
                active_stage.cleanup()

                if has_started:
                    sound_effects.play_sound(soundref.tutorial_stage_complete)
                else:
                    i = 0
                    next_stage = self.get_active_stage()
                    while next_stage is not None and next_stage.should_complete_silently_if_prev_stage_did():
                        next_stage.complete()
                        next_stage = self.get_active_stage()

                        # while loops scare me i'm sorry
                        i += 1
                        if i > 999:
                            raise ValueError("infinite loop in tutorial silently-complete loop")

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

    def is_ready(self):
        return True

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

    def should_complete_silently_if_prev_stage_did(self):
        return False


def make_action_predicate(action_type, actor_uid=None):
    def _is_item_action(act_evt):
        if act_evt is not None and act_evt.get_type() == events.EventType.ACTION_STARTED:
            if act_evt.get_action_type() == action_type:
                if actor_uid is None or act_evt.get_uid() == actor_uid:
                    return True
        return False
    return _is_item_action


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
                height = entity.get_sprite_height()
                hover_entity = entities.HoverTextEntity(message, entity, z_offset=-(height + constants.CELLSIZE // 2))
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

    def is_ready(self):
        return self.get_target_entity() is not None

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

        cond = make_action_predicate(gameengine.ActionType.MOVE_TO, p.get_uid())
        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED,
                                                         predicate=cond)

    def get_message(self):
        sttgs = gs.get_instance().settings()
        move_keybindings = [sttgs.up_key(), sttgs.left_key(), sttgs.down_key(), sttgs.right_key()]

        keystr = ""
        for keys in move_keybindings:
            if len(keys) > 0:
                keystr = keystr + Utils.stringify_key(keys[0])

        return "Use [{}] to move.".format(keystr)


class MessageOnlyStage(HowToMoveStage):

    def __init__(self, message, min_sustain=30, delay=10):
        super().__init__(delay=delay)
        self._message = message
        self._sustain = min_sustain

        self._did_move = False

    def test_completed(self):
        if not self._did_move:
            self._did_move = super().test_completed()

        return self.get_ticks_started() >= self._sustain and self._did_move

    def get_message(self):
        return self._message

    def should_complete_silently_if_prev_stage_did(self):
        return True


class HowToPickUpItemStage(EntityNotificationTutorialStage):

    def __init__(self, delay=60, item_tag=None, message="Use mouse to pick up items."):
        super().__init__(delay=delay)
        self.item_tag = item_tag
        self._message = message

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if w is None or p is None:
            return None
        else:
            for it in w.entities_in_circle(p.center(), w.cellsize() * 1.5, onscreen=True,
                                           cond=lambda e: e.is_item()):
                if self.item_tag is None or it.get_item().get_type().has_tag(self.item_tag):
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
            # player could left-click or right-click the item
            pickup_actions = (gameengine.ActionType.PICKUP_ITEM, gameengine.ActionType.ADD_ITEM_TO_GRID)
            if act_evt.get_action_type() in pickup_actions:
                if act_evt.get_uid() != p.get_uid():
                    return False

                act_item = act_evt.get_item()
                if act_item is not None:
                    if self.item_tag is None or act_item.get_type().has_tag(self.item_tag):
                        return True

            return False

        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_FINISHED,
                                                         predicate=is_item_pickup_action)

    def get_message(self):
        return self._message


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
        return "Press [{}] to open Equipment panel.".format(inv_key)


class HowToOpenMapPanelStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        return p

    def test_completed(self):
        from src.ui.ui import SidePanelTypes
        if gs.get_instance().get_active_sidepanel() == SidePanelTypes.MAP:
            return True
        elif gs.get_instance().get_run_statistic(gs.RunStatisticTypes.OPENED_MAP_COUNT) > 0:
            # if you've ever opened the map this run, skip the tutorial.
            return True

        return False

    def get_message(self):
        map_keys = gs.get_instance().settings().map_key()
        if len(map_keys) > 0:
            map_key = Utils.stringify_key(map_keys[0])
        else:
            map_key = "None"
        return "Press [{}] to open Map.".format(map_key)


class HowToPutItemInGridStage(EntityNotificationTutorialStage):

    def __init__(self, delay=60, item_tag=None, grid_type=None):
        super().__init__(delay=delay)
        self.item_tag = item_tag
        self.grid_type = grid_type

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is not None:
            held_item = gs.get_instance().held_item()
            if held_item is not None:
                if self.item_tag is None or held_item.get_type().has_tag(self.item_tag):
                    return p
        return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        from src.game.inventory import ItemGridType

        if self.grid_type is None or self.grid_type == ItemGridType.EQUIPMENT:
            all_equipped = [e for e in p.get_actor_state().inventory().all_equipped_items()]
            if len(all_equipped) > 0:
                return True

        if self.grid_type is None or self.grid_type == ItemGridType.INVENTORY:
            all_inv = [e for e in p.get_actor_state().inventory().all_inv_items()]
            if len(all_inv) > 0:
                return True

        return False

    def get_message(self):
        from src.game.inventory import ItemGridType
        if self.grid_type == ItemGridType.EQUIPMENT:
            return "Place the item into the Equipment grid."
        else:
            return "Place the item into the Inventory grid."


class HowToRotateItemStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is not None:
            held_item = gs.get_instance().held_item()
            if held_item is not None and held_item.can_rotate():
                return p
        return None

    def test_completed(self):
        if gs.get_instance().get_run_statistic(gs.RunStatisticTypes.ROTATED_ITEM_COUNT) > 0:
            return True

        if gs.get_instance().event_queue().has_event(types=events.EventType.ROTATED_ITEM):
            return True  # just in case the run statistic didn't work...?

        if len(gs.get_instance().settings().rotate_cw_key()) == 0:
            return True  # so you can't trap yourself in the tutorial by unbinding the key...

        return False

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
        return gs.get_instance().get_run_statistic(gs.RunStatisticTypes.TURNS_SKIPPED_COUNT) > 0

    def get_message(self):
        skip_keys = gs.get_instance().settings().skip_turn_key()
        if len(skip_keys) > 0:
            skip_key = Utils.stringify_key(skip_keys[0])
        else:
            skip_key = "None"

        return "Press [{}] to skip turn.".format(skip_key)


class HowToConsumeItemStage(EntityNotificationTutorialStage):

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is not None:
            held_item = gs.get_instance().held_item()
            if held_item is not None and held_item.can_consume():
                return p
        return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        cond = make_action_predicate(gameengine.ActionType.CONSUME_ITEM, p.get_uid())
        if gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED, predicate=cond):
            return True

        # storing the item in a grid counts as a dismissal
        cond = make_action_predicate(gameengine.ActionType.ADD_ITEM_TO_GRID, p.get_uid())
        for evt in gs.get_instance().event_queue().all_events(predicate=cond):
            if evt.get_item() is not None and evt.get_item().can_consume():
                return True

        # and dropping it too...
        cond = make_action_predicate(gameengine.ActionType.DROP_ITEM, p.get_uid())
        for evt in gs.get_instance().event_queue().all_events(predicate=cond):
            if evt.get_item() is not None and evt.get_item().can_consume():
                return True

    def get_message(self):
        return "Click yourself to consume."


class _HowToGetInActionRangeOfEnemyStage(EntityNotificationTutorialStage):

    def __init__(self, delay=60):
        super().__init__(delay=delay)
        self.search_range = 500

    def get_test_action(self, world, player, enemy):
        raise ValueError("not implemented")

    def get_message(self):
        raise ValueError("not implemented")

    def _candidate_enemies(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return

        enemies_in_range = w.entities_in_circle(p.center(), self.search_range, onscreen=True,
                                                cond=lambda ent: ent.is_enemy() and ent.is_visible_in_world(w))
        for e in enemies_in_range:
            yield e

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return None

        # if there's any enemy nearby, show the tutorial
        for _ in self._candidate_enemies():
            return p

        return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        for e in self._candidate_enemies():
            act = self.get_test_action(w, p, e)
            if act is not None and act.is_possible(w):
                return True

        return False


class HowToGetInThrowRangeOfEnemyStage(_HowToGetInActionRangeOfEnemyStage):

    def get_test_action(self, world, player, enemy):
        e_pos = world.to_grid_coords(*enemy.center())
        held_item = gs.get_instance().held_item()

        return gameengine.ThrowItemAction(player, held_item, e_pos)

    def get_message(self):
        return "This item can be thrown at enemies. (too far away)"

    def get_target_entity(self):
        res = super().get_target_entity()
        if res is None:
            return None
        else:
            w, p = gs.get_instance().get_world_and_player()
            if p is None:
                return None

            held_item = gs.get_instance().held_item()
            if held_item is None or not held_item.get_type().has_tag(ItemTags.THROWABLE):
                return None
            else:
                return res


class HowToThrowItemStage(EntityNotificationTutorialStage):

    def __init__(self, delay=60):
        super().__init__(delay=delay)
        self.search_range = 500

    def get_message(self):
        return "Click enemy to throw item."

    def get_target_entity(self):
        w, p = gs.get_instance().get_world_and_player()

        if p is None:
            return None

        held_item = gs.get_instance().held_item()
        if held_item is None or not held_item.get_type().has_tag(ItemTags.THROWABLE):
            return None

        enemies_in_range = w.entities_in_circle(p.center(), self.search_range, onscreen=True,
                                                cond=lambda ent: ent.is_enemy() and ent.is_visible_in_world(w))
        for e in enemies_in_range:
            e_pos = w.to_grid_coords(*e.center())
            act = gameengine.ThrowItemAction(p, held_item, e_pos)
            if act.is_possible(w):
                return p

        return None

    def test_completed(self):
        w, p = gs.get_instance().get_world_and_player()
        if p is None:
            return False

        cond = make_action_predicate(gameengine.ActionType.THROW_ITEM, p.get_uid())
        return gs.get_instance().event_queue().has_event(types=events.EventType.ACTION_STARTED, predicate=cond)


class TutorialFactory:

    @staticmethod
    def get_tutorials_for_level(level, non_complete_only=True):
        res = []
        for t in TutorialID.all_ids():
            if non_complete_only and gs.get_instance().settings().get_tutorial_finished(t):
                continue
            else:
                tut = TutorialFactory.get(t)
                if tut is not None and tut.get_min_level() <= level:
                    res.append(tut)

        return res

    @staticmethod
    def get(tut_id):
        from src.game.inventory import ItemGridType

        if tut_id == TutorialID.HOW_TO_MOVE:
            return TutorialPlugin(tut_id, 0, [
                HowToMoveStage(delay=60)
            ])
        elif tut_id == TutorialID.HOW_TO_EQUIP:
            return TutorialPlugin(tut_id, 0, [
                HowToPickUpItemStage(delay=90, item_tag=ItemTags.EQUIPMENT, message="Use mouse to pick up equipment."),
                HowToOpenInventoryPanelStage(delay=20),
                HowToPutItemInGridStage(delay=20, item_tag=ItemTags.EQUIPMENT, grid_type=ItemGridType.EQUIPMENT),
            ])
        elif tut_id == TutorialID.HOW_TO_ROTATE:
            return TutorialPlugin(tut_id, 1, [
                HowToRotateItemStage(delay=20)
            ])
        elif tut_id == TutorialID.HOW_TO_USE_POTIONS:
            return TutorialPlugin(tut_id, 0, [
                HowToPickUpItemStage(delay=90, item_tag=ItemTags.CONSUMABLE, message="Use mouse to pick up potions."),
                HowToConsumeItemStage(delay=20)
            ])
        elif tut_id == TutorialID.HOW_TO_THROW_ITEMS:
            # TODO - this one is kinda annoying
            #return TutorialPlugin(tut_id, 3, [
            #    HowToGetInThrowRangeOfEnemyStage(delay=20),
            #    HowToThrowItemStage(delay=20),
            #    MessageOnlyStage("Potions and certain weapons can be thrown.")
            #])
            return None
        elif tut_id == TutorialID.HOW_TO_OPEN_MAP:
            return TutorialPlugin(tut_id, 2, [
                HowToOpenMapPanelStage(delay=120)
            ])
        elif tut_id == TutorialID.HOW_TO_SKIP:
            return TutorialPlugin(tut_id, 2, [
                HowToSkipTurnStage(delay=360)
            ])

        return None




