import traceback
import math

import src.game.events as events
import src.game.settings as settings
from src.utils.util import Utils
import src.game.soundref as soundref
import src.game.sound_effects as sound_effects
from src.renderengine.engine import RenderEngine
import src.game.savedata as savedata
import src.items.itemencoder

_GLOBAL_STATE_INSTANCE = None


def get_instance():
    """This is how callers should obtain a global state."""
    if _GLOBAL_STATE_INSTANCE is None:
        raise ValueError("global state is None!!")
    else:
        return _GLOBAL_STATE_INSTANCE


def is_initialized():
    return _GLOBAL_STATE_INSTANCE is not None


def set_instance(new_instance):
    global _GLOBAL_STATE_INSTANCE
    _GLOBAL_STATE_INSTANCE = new_instance


class RunStatisticTypes:
    KILL_COUNT = "KILL_COUNT"
    TURN_COUNT = "TURN_COUNT"
    ELAPSED_TICKS = "ELAPSED_TIPS"
    CHECKPOINT_COUNT = "CHECKPOINTS"
    DEATH_COUNT = "DEATH_COUNT"

    # used to skip tutorials
    OPENED_INVENTORY_COUNT = "OPENED_INV_COUNT"
    OPENED_MAP_COUNT = "OPENED_MAP_COUNT"
    ROTATED_ITEM_COUNT = "ROTATED_ITEM_COUNT"
    TURNS_SKIPPED_COUNT = "TURNS_SKIPPED_COUNT"


class GlobalState:

    def __init__(self, menu_manager, dialog_manager):
        self.tick_counter = 0
        self.anim_tick = 0

        self.current_zone = None

        self._settings = settings.Settings()
        self._settings.load_from_disk()

        self._camera_center_in_world = (0, 0)
        self._camera_center_on_screen = (RenderEngine.get_instance().get_game_size()[0] // 2,
                                         RenderEngine.get_instance().get_game_size()[1] // 2)
        self._player_state = None
        self._player_controller = None
        self._held_item = None

        self._active_world = None

        self._inactive_tutorials = []
        self._active_tutorial = None

        self._world_updates_pause_timer = 0

        self._story_vars = {}

        self._menu_manager = menu_manager
        self._dialog_manager = dialog_manager

        self.active_sidepanel_id = None  # one of the SidePanelTypes

        self._cinematics_queue = []

        self._current_screenshakes = []  # list of stacks of (x, y) pairs

        self._fade_overlay_sequence = []  # list of (color, alpha) tuples

        self._event_queue = events.EventQueue(cond=lambda evt: not evt.is_global())
        self._event_triggers = {}  # EventType -> list(EventListener)

        self._global_event_queue = events.EventQueue(cond=lambda evt: evt.is_global())

        self._mapped_actions = [None for _ in range(0, 6)]
        self._action_to_target = None
        self._waiting_for_player = False

        self._targetable_coords_in_world = {}  # (x, y) -> color

        # save data stuff
        self._run_statistics = {}
        self._save_data = None
        self._loaded_from_save_id = None

    def increment_tick_counts(self):
        self.tick_counter += 1
        if self.tick_counter % self.ticks_per_anim_tick() == 0:
            self.anim_tick += 1

        if not self.menu_manager().pause_world_updates():
            self.inc_run_statistic(RunStatisticTypes.ELAPSED_TICKS)

    def set_world(self, world):
        self._active_world = world

    def get_world(self):
        return self._active_world

    def get_world_and_player(self):
        """returns: (None, None) or (World, None) or (World, PlayerEntity)"""
        w = self.get_world()
        if w is None:
            return (None, None)
        else:
            return (w, w.get_player())

    def ticks_per_anim_tick(self):
        return 8

    def settings(self):
        return self._settings

    def save_settings_to_disk(self):
        self._settings.save_to_disk()

    def get_save_data_if_present(self):
        return self._save_data

    def get_loaded_from_save_id(self):
        return self._loaded_from_save_id

    def detach_save_data_if_present(self):
        """Severs the connection between this globalstate and its save data file."""
        self._save_data = None

    def _update_save_data(self, save_id=None):
        if self._save_data is None:
            if save_id is None:
                return  # can't do a soft update with no save_id
            else:
                self._save_data = savedata.make_brand_new_blob()

        elif self._save_data.is_completed():
            print("WARN: save file is already completed, skipping update")
            return

        self._save_data.set(savedata.SaveDataTags.KILL_COUNT, self.get_run_statistic(RunStatisticTypes.KILL_COUNT))
        self._save_data.set(savedata.SaveDataTags.TURN_COUNT, self.get_run_statistic(RunStatisticTypes.TURN_COUNT))
        self._save_data.set(savedata.SaveDataTags.ELAPSED_TIME, self.get_run_statistic(RunStatisticTypes.ELAPSED_TICKS))
        self._save_data.set(savedata.SaveDataTags.DEATH_COUNT, self.get_run_statistic(RunStatisticTypes.DEATH_COUNT))
        self._save_data.set(savedata.SaveDataTags.CHECKPOINT_COUNT, self.get_run_statistic(RunStatisticTypes.CHECKPOINT_COUNT))

        if save_id is not None:
            self._save_data.set(savedata.SaveDataTags.SPAWN_ID, save_id)

            inv_items = []
            inv_item_positions = []

            inv_grid = self.player_state().inventory().get_inv_grid()
            for it in inv_grid.all_items():
                pos = inv_grid.get_pos(it)
                inv_items.append(it)
                inv_item_positions.append(pos)

            self._save_data.set(savedata.SaveDataTags.INVENTORY_ITEM_POSITIONS, inv_item_positions)
            self._save_data.set(savedata.SaveDataTags.INVENTORY_ITEMS, inv_items)

            equip_items = []
            equip_item_positions = []

            equip_grid = self.player_state().inventory().get_equip_grid()
            for it in equip_grid.all_items():
                pos = equip_grid.get_pos(it)
                equip_items.append(it)
                equip_item_positions.append(pos)

            self._save_data.set(savedata.SaveDataTags.EQUIPMENT_ITEM_POSITIONS, equip_item_positions)
            self._save_data.set(savedata.SaveDataTags.EQUIPMENT_ITEMS, equip_items)

    def pull_state_from_save_data(self, save_data):
        """Note: this should only be called once, global_state.create_new"""
        if save_data is None:
            return

        self._save_data = save_data
        self._loaded_from_save_id = save_data.get(savedata.SaveDataTags.SPAWN_ID)

        self.set_run_statistic(RunStatisticTypes.KILL_COUNT, save_data.get(savedata.SaveDataTags.KILL_COUNT))
        self.set_run_statistic(RunStatisticTypes.TURN_COUNT, save_data.get(savedata.SaveDataTags.TURN_COUNT))
        self.set_run_statistic(RunStatisticTypes.ELAPSED_TICKS, save_data.get(savedata.SaveDataTags.ELAPSED_TIME))
        self.set_run_statistic(RunStatisticTypes.DEATH_COUNT, save_data.get(savedata.SaveDataTags.DEATH_COUNT))
        self.set_run_statistic(RunStatisticTypes.CHECKPOINT_COUNT, save_data.get(savedata.SaveDataTags.CHECKPOINT_COUNT))

        inv_grid = self.player_state().inventory().get_inv_grid()
        removed_from_inv = inv_grid.remove_all()

        inv_items = save_data.get(savedata.SaveDataTags.INVENTORY_ITEMS)
        inv_item_positions = save_data.get(savedata.SaveDataTags.INVENTORY_ITEM_POSITIONS)
        for i in range(0, len(inv_items)):
            the_item = inv_items[i]
            pos = inv_item_positions[i]
            placed = inv_grid.place(the_item, pos)
            if not placed:
                print("WARN: failed to place inventory item at position {}, skipping it {}".format(pos, the_item))

        eq_grid = self.player_state().inventory().get_equip_grid()
        removed_from_eq = eq_grid.remove_all()

        eq_items = save_data.get(savedata.SaveDataTags.EQUIPMENT_ITEMS)
        eq_item_positions = save_data.get(savedata.SaveDataTags.EQUIPMENT_ITEM_POSITIONS)
        for i in range(0, len(eq_items)):
            the_item = eq_items[i]
            pos = eq_item_positions[i]
            placed = eq_grid.place(the_item, pos)
            if not placed:
                print("WARN: failed to place equipment item at position {}, skipping it {}".format(pos, the_item))

        if len(removed_from_inv) + len(removed_from_eq) > 0:
            # this would mean we're slamming over an active run or something, not good
            print("WARN: deleted {} pre-existing items while loading save file".format(
                len(removed_from_inv) + len(removed_from_eq)
            ))

    def save_current_game_to_disk(self, save_id):
        if save_id is None:
            print("ERROR: can't save game with no save_id")
            return False

        self._update_save_data(save_id=save_id)

        if self._save_data is not None:
            return savedata.write_to_disk(self._save_data)

        print("ERROR: save_data is None?")
        return False

    def get_last_save_id(self):
        if self._save_data is not None:
            return self._save_data.get(savedata.SaveDataTags.SPAWN_ID)
        else:
            return None

    def save_current_game_to_disk_softly(self):
        """
            Updates things like elapsed time, kill count, death count, etc. if
            there's existing save data for this run. Note that this does NOT
            update the items / save_location_id, or create a new save file if
            one doesn't already exist, (hence "softly").
        """
        if self._save_data is None:
            print("INFO: nothing to save, skipping")
            return False
        else:
            self._update_save_data(save_id=None)
            return savedata.write_to_disk(self._save_data)

    def event_queue(self):
        return self._event_queue

    def global_event_queue(self):
        return self._global_event_queue

    def add_event(self, event, delay=0):
        if not event.is_global():
            self.event_queue().add(event, delay=delay)
        else:
            if delay > 0:
                print("WARN: global events cannot have delay > 0: {}".format(event))
            self.global_event_queue().add(event, delay=0)

    def add_trigger(self, trigger):
        """
        trigger: EventListener
        """
        if trigger.event_type not in self._event_triggers:
            self._event_triggers[trigger.event_type] = []

        self._event_triggers[trigger.event_type].append(trigger)

    def prepare_for_new_zone(self, zone):
        self.player_controller().clear_requests()
        self.clear_triggers(events.EventListenerScope.ZONE)
        self._active_tutorial = None
        self._inactive_tutorials = []

        self.current_zone = zone

    def set_inactive_tutorials(self, tutorials):
        self._inactive_tutorials = tutorials

    def set_active_tutorial(self, tutorial):
        self._active_tutorial = tutorial

    def set_active_sidepanel(self, panel_id, play_sound=True):
        if play_sound and self.active_sidepanel_id != panel_id:
            if panel_id is None:
                sound_effects.play_sound(soundref.sidepanel_out)
            else:
                from src.ui.ui import SidePanelTypes
                if panel_id == SidePanelTypes.INVENTORY:
                    self.inc_run_statistic(RunStatisticTypes.OPENED_INVENTORY_COUNT)
                elif panel_id == SidePanelTypes.MAP:
                    self.inc_run_statistic((RunStatisticTypes.OPENED_MAP_COUNT))

                sound_effects.play_sound(soundref.sidepanel_in)

        self.active_sidepanel_id = panel_id

    def get_run_statistic(self, run_stat_type):
        if run_stat_type in self._run_statistics:
            return self._run_statistics[run_stat_type]
        else:
            return 0

    def is_peaceful_so_far(self):
        return self.get_run_statistic(RunStatisticTypes.KILL_COUNT) == 0

    def set_run_statistic(self, run_stat_type, val):
        if val is None:
            print("WARN: tried to set run statistic {} to None, setting to 0 instead".format(run_stat_type))
            self._run_statistics[run_stat_type] = 0
        else:
            self._run_statistics[run_stat_type] = val

    def inc_run_statistic(self, run_stat_type, val=1):
        cur_value = self.get_run_statistic(run_stat_type)
        self.set_run_statistic(run_stat_type, cur_value + val)
        return self.get_run_statistic(run_stat_type)

    def get_active_sidepanel(self):
        return self.active_sidepanel_id

    def toggle_sidepanel(self, panel_id, play_sound=True):
        if self.get_active_sidepanel() == panel_id:
            self.set_active_sidepanel(None, play_sound=play_sound)
            self.add_event(events.ToggledSidepanelEvent(panel_id, False))
        else:
            self.set_active_sidepanel(panel_id, play_sound=play_sound)
            self.add_event(events.ToggledSidepanelEvent(panel_id, True))

    def clear_triggers(self, scope):
        for e_type in self._event_triggers:
            self._event_triggers[e_type] = [e for e in self._event_triggers[e_type] if e.scope is not scope]

    def get_fade_overlay_state(self):
        if len(self._fade_overlay_sequence) > 0:
            return self._fade_overlay_sequence[-1]
        else:
            return None

    def do_fade_sequence(self, start_alpha, end_alpha, duration, color=(0, 0, 0), start_delay=0, end_delay=0):
        self._fade_overlay_sequence.clear()

        # it's a stack, so building it backwards
        for _ in range(0, end_delay):
            alpha = Utils.bound(end_alpha, 0, 1)
            self._fade_overlay_sequence.append((color, alpha))

        for i in range(0, duration + 1):
            alpha = end_alpha * (1 - i / duration) + start_alpha * (i / duration)
            alpha = Utils.bound(alpha, 0, 1)
            self._fade_overlay_sequence.append((color, alpha))

        for _ in range(0, start_delay):
            alpha = Utils.bound(start_alpha, 0, 1)
            self._fade_overlay_sequence.append((color, alpha))

    def menu_manager(self):
        return self._menu_manager

    def world_updates_paused(self):
        return (self.menu_manager().pause_world_updates()
                or self.dialog_manager().is_active()
                or self._world_updates_pause_timer > 0)

    def pause_world_updates(self, duration):
        self._world_updates_pause_timer = max(self._world_updates_pause_timer, duration)

    def set_targetable_coords_in_world(self, targets):
        """targets: map of (x, y) -> color"""
        self._targetable_coords_in_world.clear()
        if targets is not None:
            self._targetable_coords_in_world.update(targets)

    def get_targetable_coords_in_world(self):
        return self._targetable_coords_in_world

    def get_story_var(self, key, as_bool=False):
        if key in self._story_vars:
            return (self._story_vars[key] != 0) if as_bool else self._story_vars[key]
        else:
            return False if as_bool else 0

    def set_story_var(self, key, value):
        if value is None:
            if key in self._story_vars:
                del self._story_vars[key]
        else:
            if value is True:
                value = 1
            elif value is False:
                value = 0

            if not isinstance(value, int):
                raise ValueError("story var's value must be an int, instead got: {}".format(value))
            else:
                print("INFO: setting story var \"{}\" to {}".format(key, value))
                self._story_vars[key] = value

    def held_item(self):
        return self._held_item

    def set_held_item(self, val):
        self._held_item = val

    def dialog_manager(self):
        return self._dialog_manager

    def get_zone_level(self):
        if self.current_zone is None:
            return 0
        else:
            return self.current_zone.get_level()

    def get_zone_id(self):
        if self.current_zone is None:
            return None  # TODO - is this dangerous?
        else:
            return self.current_zone.ZONE_ID

    def is_player_turn_to_act(self):
        return not self.world_updates_paused() and self._waiting_for_player

    def set_player_turn_to_act(self, val):
        self._waiting_for_player = val
        
    def set_player_state(self, state, controller):
        self._player_state = state
        self._player_controller = controller

    def add_screenshake(self, strength, duration, falloff=3, freq=6):
        """
        int strength: max pixel offset of shake
        int duration: ticks for which the shake will remain active
        int freq: "speed" of the shake. 1 is really fast, higher is slower
        """
        shake_pts = Utils.get_shake_points(strength, duration, falloff=falloff, freq=freq)
        self._current_screenshakes.append(shake_pts)
        return [pt for pt in shake_pts]

    def get_screenshake(self):
        if len(self._current_screenshakes) == 0:
            return (0, 0)
        else:
            x_sum = 0
            y_sum = 0
            for shake in self._current_screenshakes:
                x_sum += shake[-1][0]
                y_sum += shake[-1][1]

            return (round(x_sum), round(y_sum))

    def get_cinematics_queue(self):
        return self._cinematics_queue
        
    def player_state(self):
        return self._player_state

    def player_controller(self):
        return self._player_controller

    def get_mapped_action(self, idx):
        all_actions = list(self.player_state().get_all_mappable_action_providers())
        if idx < len(all_actions):
            return all_actions[idx]
        else:
            return None

    def get_targeting_action_provider(self):
        if self.held_item() is not None:
            return None
        elif self._action_to_target is not None:
            item_uid = self._action_to_target.get_item_uid()
            if item_uid is None:
                return self._action_to_target

            item = self.player_state().get_item_in_possession_with_uid(item_uid)
            if item is None:
                return None

            is_equipped = self.player_state().inventory().is_equipped(item)
            in_inv = self.player_state().inventory().is_in_inventory(item)
            if self._action_to_target.needs_equipped():
                if is_equipped:
                    return self._action_to_target
            else:
                if is_equipped or in_inv:
                    return self._action_to_target

        return None

    def get_pulsing_color(self, color):
        interp = 0.25 * (1 + math.sin(2 * math.pi * self.anim_tick / 8))
        return Utils.linear_interp(color, (1, 1, 1), interp)

    def set_targeting_action_provider(self, action_prov):
        """returns: action that's currently being targeted"""
        self._action_to_target = action_prov

    def set_mapped_action(self, idx, value, hard):
        self._mapped_actions[idx] = value
    
    def set_camera_center_in_world(self, x, y):
        """(int: x, int: y) position in world"""
        self._camera_center_in_world = (x, y)

    def get_camera_center_in_world(self):
        return self._camera_center_in_world

    def set_camera_center_on_screen(self, px, py):
        """(int: x, int: y) pixel position on screen"""
        self._camera_center_on_screen = (px, py)

    def get_camera_center_on_screen(self):
        return self._camera_center_on_screen
    
    def get_actual_camera_xy(self):
        cam_center = self.get_actual_camera_center()
        offs_x = cam_center[0] - RenderEngine.get_instance().get_game_size()[0] // 2
        offs_y = cam_center[1] - RenderEngine.get_instance().get_game_size()[1] // 2
        return (offs_x, offs_y)

    def get_actual_camera_center(self):
        x = self._camera_center_in_world[0] - (self._camera_center_on_screen[0] - RenderEngine.get_instance().get_game_size()[0] // 2)
        y = self._camera_center_in_world[1] - (self._camera_center_on_screen[1] - RenderEngine.get_instance().get_game_size()[1] // 2)
        return (x, y)

    def get_world_camera_size(self):
        return RenderEngine.get_instance().get_game_size()

    def get_world_camera_rect(self, fudge=0):
        cam_xy = self.get_actual_camera_xy()
        cam_size = self.get_world_camera_size()
        return [cam_xy[0] - fudge,
                cam_xy[1] - fudge,
                cam_size[0] + 2*fudge,
                cam_size[1] + 2*fudge]
        
    def screen_to_world_coords(self, point):
        cam = self.get_actual_camera_xy()
        return (cam[0] + point[0], cam[1] + point[1])
        
    def update_world_stuff(self):
        world = self.get_world()
        if world is not None:
            for e in self.event_queue().all_events():
                triggers_to_remove = []
                if e.get_type() in self._event_triggers:
                    for trigger in self._event_triggers[e.get_type()]:
                        if trigger.predicate(e):
                            try:
                                trigger.do_action(e, world)
                            except Exception:
                                traceback.print_exc()

                            if trigger.single_use:
                                triggers_to_remove.append(trigger)

                for t in triggers_to_remove:
                    self._event_triggers[t.event_type].remove(t)

        if not self.menu_manager().pause_world_updates():
            if self._active_tutorial is not None:
                self._active_tutorial.update()

                if self._active_tutorial.is_complete():
                    print("INFO: completed tutorial: {}".format(self._active_tutorial.get_id()))
                    self.settings().set_tutorial_finished(self._active_tutorial.get_id(), True)
                    self._active_tutorial = None
            else:
                for tut in self._inactive_tutorials:
                    if tut.is_ready():
                        print("INFO: activating tutorial: {}".format(tut.get_id()))
                        self._active_tutorial = tut
                        self._inactive_tutorials.remove(tut)
                        break

        if len(self._current_screenshakes) > 0:
            any_empty = False
            for shake_stack in self._current_screenshakes:
                shake_stack.pop()
                if len(shake_stack) == 0:
                    any_empty = True

            if any_empty:
                self._current_screenshakes = [sh for sh in self._current_screenshakes if len(sh) > 0]

        if self._world_updates_pause_timer > 0:
            self._world_updates_pause_timer -= 1

        if len(self._fade_overlay_sequence) > 0:
            self._fade_overlay_sequence.pop(-1)


def create_new(menu, from_save_data=None):
    import src.ui.menus as menus
    menu_manager = menus.MenuManager(menu)

    import src.game.dialog as dialog
    dialog_manager = dialog.DialogManager()

    new_instance = GlobalState(menu_manager, dialog_manager)

    import src.game.inventory as inventory
    inventory_state = inventory.InventoryState()

    import src.game.gameengine as gameengine
    import src.game.stats as stats
    player_state = gameengine.ActorState("player", 5, stats.default_player_stats(), inventory_state, 0, True)
    player_controller = gameengine.PlayerController()

    new_instance.set_player_state(player_state, player_controller)
    new_instance.pull_state_from_save_data(from_save_data)

    set_instance(new_instance)

