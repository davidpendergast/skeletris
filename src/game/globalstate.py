import traceback
import math
import random
import os

import src.game.events as events
import src.game.settings as settings
from src.utils.util import Utils
import src.game.soundref as soundref
import src.game.sound_effects as sound_effects
from src.game.windowstate import WindowState

_GLOBAL_STATE_INSTANCE = None


def get_instance():
    """This is how callers should obtain a global state."""
    if _GLOBAL_STATE_INSTANCE is None:
        raise ValueError("global state is None!!")
    else:
        return _GLOBAL_STATE_INSTANCE


def set_instance(new_instance):
    global _GLOBAL_STATE_INSTANCE
    _GLOBAL_STATE_INSTANCE = new_instance


class RunStatisticTypes:
    KILL_COUNT = "KILL_COUNT"
    TURN_COUNT = "TURN_COUNT"

    # used to skip tutorials
    OPENED_INVENTORY_COUNT = "OPENED_INV_COUNT"
    OPENED_MAP_COUNT = "OPENED_MAP_COUNT"
    ROTATED_ITEM_COUNT = "ROTATED_ITEM_COUNT"


class GlobalState:

    def __init__(self, initial_zone_id, menu_manager, dialog_manager):
        self.tick_counter = 0
        self.anim_tick = 0

        self.initial_zone_id = initial_zone_id
        self.current_zone = None

        self._settings = settings.Settings()
        self._settings_filename = "settings.json"
        self._settings.load_from_file(self._path_to_settings())

        self._camera_center_in_world = (0, 0)
        win = WindowState.get_instance()
        self._camera_center_on_screen = (win.get_screen_size()[0] // 2, win.get_screen_size()[0] // 2)
        self._player_state = None
        self._player_controller = None

        self._active_world = None

        self._inactive_tutorials = []
        self._active_tutorial = None

        self._world_updates_pause_timer = 0

        self._story_vars = {}

        self._run_statistics = {}

        self._menu_manager = menu_manager
        self._dialog_manager = dialog_manager

        self.active_sidepanel_id = None  # one of the SidePanelTypes

        self._cinematics_queue = []

        self._current_screenshakes = []  # list of stacks of (x, y) pairs

        self._fade_overlay_sequence = []  # list of (color, alpha) tuples

        self._event_queue = events.EventQueue()
        self._event_triggers = {}  # EventType -> list(EventListener)

        self._mapped_actions = [None for _ in range(0, 6)]
        self._action_to_target = None
        self._waiting_for_player = False

        self._targetable_coords_in_world = {}  # (x, y) -> color

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

    def settings(self):
        return self._settings

    def save_settings_to_disk(self):
        self._settings.save_to_file(self._path_to_settings())

    def _path_to_settings(self):
        return os.path.join("save_data", self._settings_filename)

    def event_queue(self):
        return self._event_queue

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

    def set_run_statistic(self, run_stat_type, val):
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
            self.event_queue().add(events.ToggledSidepanelEvent(panel_id, False))
        else:
            self.set_active_sidepanel(panel_id, play_sound=play_sound)
            self.event_queue().add(events.ToggledSidepanelEvent(panel_id, True))

    def clear_triggers(self, scope):
        for e_type in self._event_triggers:
            self._event_triggers[e_type] = [e for e in self._event_triggers[e_type] if e.scope is not scope]

    def get_fade_overlay_state(self):
        if len(self._fade_overlay_sequence) > 0:
            return self._fade_overlay_sequence[-1]
        else:
            return None

    def do_fade_sequence(self, start_alpha, end_alpha, duration, color=(0, 0, 0)):
        self._fade_overlay_sequence.clear()
        for i in range(0, duration + 1):
            # it's a stack, so building it backwards
            alpha = end_alpha * (1 - i / duration) + start_alpha * (i / duration)
            alpha = Utils.bound(alpha, 0, 1)
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
        if self.player_state().held_item is not None:
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

    def get_targeting_action_color(self):
        action_prov = self.get_targeting_action_provider()
        if action_prov is None:
            return (1, 1, 1)
        else:
            color = action_prov.get_color()
            return self.get_pulsing_color(color)

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
        offs_x = cam_center[0] - WindowState.get_instance().get_screen_size()[0] // 2
        offs_y = cam_center[1] - WindowState.get_instance().get_screen_size()[1] // 2
        return (offs_x, offs_y)

    def get_actual_camera_center(self):
        x = self._camera_center_in_world[0] - (self._camera_center_on_screen[0] - WindowState.get_instance().get_screen_size()[0] // 2)
        y = self._camera_center_in_world[1] - (self._camera_center_on_screen[1] - WindowState.get_instance().get_screen_size()[1] // 2)
        return (x, y)

    def get_world_camera_size(self):
        return WindowState.get_instance().get_screen_size()

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
        
    def update(self):
        world = self.get_world()
        if world is not None:
            for e in self.event_queue().all_events():
                triggers_to_remove = []
                if e.get_type() in self._event_triggers:
                    for trigger in self._event_triggers[e.get_type()]:
                        if trigger.predicate(e):
                            try:
                                trigger.do_action(e, world)
                            except ValueError:
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

        if self._world_updates_pause_timer > 0 and not self.menu_manager().pause_world_updates():
            self._world_updates_pause_timer -= 1

        if len(self._fade_overlay_sequence) > 0:
            self._fade_overlay_sequence.pop(-1)

        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1


def create_new(menu):
    import src.ui.menus as menus
    menu_manager = menus.MenuManager(menu)

    import src.game.dialog as dialog
    dialog_manager = dialog.DialogManager()

    import src.worldgen.zones as zones
    new_instance = GlobalState(zones.first_zone_id(), menu_manager, dialog_manager)

    import src.game.inventory as inventory
    inventory_state = inventory.InventoryState()

    import src.game.gameengine as gameengine
    import src.game.stats as stats
    player_state = gameengine.ActorState("player", 5, stats.default_player_stats(), inventory_state, 0)
    player_controller = gameengine.PlayerController()

    new_instance.set_player_state(player_state, player_controller)

    set_instance(new_instance)

