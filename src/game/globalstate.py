import traceback
import math
import random
import os

from src.ui.menus import MenuManager
from src.game.npc import NpcState
from src.game.dialog import DialogManager
import src.game.events as events
from src.game.settings import Settings
from src.utils.util import Utils
from src.game.inventory import InventoryState


class SaveData:

    def __init__(self, filename):
        self._filename = filename

        self.kill_count = 0
        self.num_potions = 0
        self.current_zone_id = None

        self.inventory_state = None  # not currently used heh

    def get_path(self):
        return SaveData.path_for_filename(self._filename)

    @staticmethod
    def path_for_filename(filename):
        return os.path.join("save_data", filename)

    @staticmethod
    def exists_on_disk(filename):
        return os.path.exists(SaveData.path_for_filename(filename))

    @staticmethod
    def create_new_save_file(filename):
        data = SaveData(filename)
        data.save_to_disk()
        print("INFO: created new save file {}".format(filename))
        return data

    @staticmethod
    def load_from_disk(filename):
        res = SaveData(filename)
        dest_file = res.get_path()

        try:
            json_blob = Utils.load_json_from_path(dest_file)

            print("json_blob={}".format(json_blob))
            res.kill_count = Utils.read_int(json_blob, "kill_count", 0)
            res.num_potions = Utils.read_int(json_blob, "num_potions", 0)
            res.current_zone_id = Utils.read_string(json_blob, "current_zone_id", None)
            res.inventory_state = InventoryState.from_json(Utils.read_map(json_blob, "inventory", {}))
            print("INFO: loaded save data {} from disk".format(filename))
            return res

        except ValueError:
            print("ERROR: failed to load " + dest_file)
            return None

    def to_json(self):
        return {
            "version": 0,
            "kill_count": self.kill_count,
            "num_potions": self.num_potions,
            "current_zone_id": self.current_zone_id,
            "inventory": self.inventory_state.to_json()
        }

    def save_to_disk(self):
        json_blob = self.to_json()
        dest_file = self.get_path()
        try:
            Utils.save_json_to_path(json_blob, dest_file)
            print("INFO: saved save data {} to disk".format(self._filename))
            return True
        except ValueError:
            print("ERROR: failed to save to " + dest_file)
            traceback.print_exc()
            return False

    def __repr__(self):
        return str(self.to_json())


class GlobalState:

    def __init__(self, save_data, menu_id=MenuManager.START_MENU):
        self.screen_size = [800, 600]
        self.is_fullscreen = False
    
        self.tick_counter = 0
        self.anim_tick = 0

        self.dungeon_level = 0  # this needs to be zone-level

        self._settings = Settings()

        self._save_data = save_data

        self._world_camera_center = [0, 0]
        self._player_state = None

        self._menu_manager = MenuManager(menu_id)

        self._npc_state = NpcState()
        self._dialog_manager = DialogManager()

        self._cinematics_queue = []

        self._current_screenshakes = []  # list of stacks of (x, y) pairs

        self._event_queue = events.EventQueue()
        self._event_triggers = {}  # EventType -> list(EventListener)

        """
        some of the zones require additional updating logic to handle story / boss fight stuff. 
        these Updaters handle that
        """
        self._zone_updaters = []

    def settings(self):
        return self._settings

    def save_data(self):
        return self._save_data

    def event_queue(self):
        return self._event_queue

    def add_trigger(self, trigger):
        """
        trigger: EventListener
        """
        if trigger.event_type not in self._event_triggers:
            self._event_triggers[trigger.event_type] = []

        self._event_triggers[trigger.event_type].append(trigger)

    def add_zone_updater(self, updater):
        self._zone_updaters.append(updater)

    def prepare_for_new_zone(self, zone_id):
        self._zone_updaters.clear()
        self.clear_triggers(events.EventListenerScope.ZONE)

        self.save_data().current_zone_id = zone_id

    def clear_triggers(self, scope):
        for e_type in self._event_triggers:
            self._event_triggers[e_type] = [e for e in self._event_triggers[e_type] if e.scope is not scope]

    def menu_manager(self):
        return self._menu_manager

    def world_updates_paused(self):
        return (self.menu_manager().get_active_menu_id() is not MenuManager.IN_GAME_MENU
                or self.dialog_manager().is_active())

    def dialog_manager(self):
        return self._dialog_manager

    def npc_state(self):
        return self._npc_state
        
    def set_player_state(self, state):
        self._player_state = state

    def add_screenshake(self, strength, duration, falloff=3, freq=6):
        """
        int strength: max pixel offset of shake
        int duration: ticks for which the shake will remain active
        int freq: "speed" of the shake. 1 is really fast, higher is slower
        """
        decay = lambda t: math.exp(-falloff*(t / duration))
        num_keypoints = int(duration / freq)
        x_pts = [round(2 * (0.5 - random.random()) * strength * decay(t * freq)) for t in range(0, num_keypoints)]
        y_pts = [round(2 * (0.5 - random.random()) * strength * decay(t * freq)) for t in range(0, num_keypoints)]
        x_pts.append(0)
        y_pts.append(0)

        shake_pts = []
        for i in range(0, duration):
            if i % freq == 0:
                shake_pts.append((x_pts[i // freq], y_pts[i // freq]))
            else:
                prev_pt = (x_pts[i // freq], y_pts[i // freq])
                next_pt = (x_pts[i // freq + 1], y_pts[i // freq + 1])
                shake_pts.append(Utils.linear_interp(prev_pt, next_pt, (i % freq) / freq))

        if len(shake_pts) == 0:
            return  # this shouldn't happen but ehh

        shake_pts.reverse()  # this is used as a stack
        self._current_screenshakes.append(shake_pts)

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

    def play_cinematic(self, scenes):
        self.get_cinematics_queue().extend(scenes)
        self.menu_manager().set_active_menu(MenuManager.CINEMATIC_MENU)
        
    def player_state(self):
        return self._player_state
    
    def set_world_camera_center(self, x, y):
        self._world_camera_center = (x, y)
    
    def get_world_camera(self, center=False):
        if center:
            return tuple(self._world_camera_center)
        else:
            offs_x = self._world_camera_center[0] - self.screen_size[0] // 2
            offs_y = self._world_camera_center[1] - self.screen_size[1] // 2
            return (offs_x, offs_y)

    def get_world_camera_size(self):
        return self.screen_size
        
    def screen_to_world_coords(self, point):
        cam = self.get_world_camera()
        return (cam[0] + point[0], cam[1] + point[1])
        
    def update(self, world, input_state, render_engine):
        self.event_queue().flip()
        if world is not None:
            for e in self.event_queue().all_events():
                print(e)
                triggers_to_remove = []
                if e.get_type() in self._event_triggers:
                    for trigger in self._event_triggers[e.get_type()]:
                        if trigger.predicate(e):
                            try:
                                trigger.action(e, world, self)
                            except ValueError:
                                traceback.print_exc()

                            if trigger.single_use:
                                triggers_to_remove.append(trigger)

                for t in triggers_to_remove:
                    self._event_triggers[t.event_type].remove(t)

            for zone_update in self._zone_updaters:
                zone_update.update(world, self, input_state, render_engine)

        if len(self._current_screenshakes) > 0:
            any_empty = False
            for shake_stack in self._current_screenshakes:
                shake_stack.pop()
                if len(shake_stack) == 0:
                    any_empty = True

            if any_empty:
                self._current_screenshakes = [sh for sh in self._current_screenshakes if len(sh) > 0]

        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1

