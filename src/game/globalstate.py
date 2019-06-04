import traceback
import math
import random
import os

import src.game.events as events
import src.game.settings as settings
from src.game.storystate import StoryStateKey, StoryState
from src.utils.util import Utils
import src.utils.passwordgen as passwordgen

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


class SaveDataBlob:

    def __init__(self, zone_id, kill_count, num_potions, equipment_positions, inventory_positions, story_state):
        """
        zone_id: str
        kill_count: int
        num_potions: int
        equipment_positions: map (int x, int y) -> Item
        inventory_positions: map (int x, int y) -> Item
        story_state_blob: json blob
        """
        self.zone_id = zone_id
        self.kill_count = kill_count
        self.num_potions = num_potions

        self.story_state = story_state

        self.equipment_positions = equipment_positions
        self.inventory_positions = inventory_positions

    @staticmethod
    def get_current_passwords_from_disk():
        res = []
        try:
            for file in os.listdir(os.path.join("save_data", "saved_games")):
                if file.endswith(".json"):
                    pw = file[:(len(file)-5)]
                    res.append(pw)
        except:
            print("ERROR: failure while trying to fetch already-used passwords")
            traceback.print_exc()
        return res

    def save_to_disk(self, password):
        path = SaveDataBlob.filepath_for_password(password)
        try:
            as_json = self.to_json()
            Utils.save_json_to_path(as_json, path)
            return True
        except:
            print("ERROR: failed to save {}".format(path))
            traceback.print_exc()
        return False

    @staticmethod
    def load_from_disk(password):
        path = SaveDataBlob.filepath_for_password(password)
        try:
            blob = Utils.load_json_from_path(path)
            return SaveDataBlob.from_json(blob)
        except:
            print("ERROR: failed to load {}".format(path))
            traceback.print_exc()

        return None

    def to_json(self):
        equipment = []
        for xy in self.equipment_positions:
            item_as_json = self.equipment_positions[xy].to_json()
            equipment.append((xy[0], xy[1], item_as_json))

        inventory = []
        for xy in self.inventory_positions:
            item_as_json = self.inventory_positions[xy].to_json()
            inventory.append((xy[0], xy[1], item_as_json))

        story_state_blob = self.story_state.to_json()

        return {
            "kill_count": self.kill_count,
            "num_potions": self.num_potions,
            "zone_id": self.zone_id,
            "equipment": equipment,
            "inventory": inventory,
            "story_state": story_state_blob
        }

    @staticmethod
    def from_json(blob):
        kill_count = int(blob["kill_count"])
        num_potions = int(blob["num_potions"])
        zone_id = str(blob["zone_id"])

        from src.items.item import StatCubesItem
        equipment_positions = {}
        for x_y_item in blob["equipment"]:
            try:
                x = int(x_y_item[0])
                y = int(x_y_item[1])
                item = StatCubesItem.from_json(x_y_item[2])
                equipment_positions[(x, y)] = item
            except:
                print("ERROR: couldn't deserialize item: {}".format(x_y_item))
                traceback.print_exc()

        inventory_positions = {}
        for x_y_item in blob["inventory"]:
            try:
                x = int(x_y_item[0])
                y = int(x_y_item[1])
                item = StatCubesItem.from_json(x_y_item[2])
                inventory_positions[(x, y)] = item
            except:
                print("ERROR: couldn't deserialize item: {}".format(x_y_item))
                traceback.print_exc()

        story_state_blob = blob["story_state"]
        story_state = StoryState.from_json(story_state_blob)

        return SaveDataBlob(zone_id, kill_count, num_potions, equipment_positions, inventory_positions, story_state)

    def __repr__(self):
        return str(self.to_json())


class GlobalState:

    def __init__(self, initial_zone_id, menu_manager, dialog_manager, story_state):
        self.screen_size = [800, 600]
        self.is_fullscreen = False
    
        self.tick_counter = 0
        self.anim_tick = 0
        self.turn_counter = 0

        self.initial_zone_id = initial_zone_id
        self.current_zone = None

        self._settings = settings.Settings()
        self._settings_filename = "settings.json"
        self._settings.load_from_file(self._path_to_settings())

        self._camera_center_in_world = (0, 0)
        self._camera_center_on_screen = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        self._player_state = None
        self._player_controller = None

        self._story_state = story_state

        self._menu_manager = menu_manager
        self._dialog_manager = dialog_manager

        self._inventory_open = False

        self._cinematics_queue = []

        self._current_screenshakes = []  # list of stacks of (x, y) pairs

        self._event_queue = events.EventQueue()
        self._event_triggers = {}  # EventType -> list(EventListener)

        self._mapped_actions = [None for _ in range(0, 6)]
        self._action_to_target = None

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

        self.current_zone = zone

    def is_inventory_open(self):
        return self._inventory_open

    def set_inventory_open(self, val):
        self._inventory_open = val

    def clear_triggers(self, scope):
        for e_type in self._event_triggers:
            self._event_triggers[e_type] = [e for e in self._event_triggers[e_type] if e.scope is not scope]

    def menu_manager(self):
        return self._menu_manager

    def world_updates_paused(self):
        return self.menu_manager().pause_world_updates() or self.dialog_manager().is_active()

    def dialog_manager(self):
        return self._dialog_manager

    def story_state(self):
        return self._story_state

    def save_game_to_disk(self, password=None):
        """
        return: (bool, str)
            bool: True if save is successful, False otherwise
            str: password used for successful save.
        """
        if self.current_zone is None:
            print("ERROR: cannot save game if current_zone is None")
            return (False, None)

        if password is None:
            already_used = SaveDataBlob.get_current_passwords_from_disk()
            password = passwordgen.gen_unique_password(already_used)

        # equip_items = self.player_state().inventory().equip_grid.to_map()
        # inv_items = self.player_state().inventory().inv_grid.to_map()

        save_blob = SaveDataBlob(self.current_zone.ZONE_ID,
                                 10,
                                 5,
                                 None,  # equip_items,
                                 None,  # inv_items,
                                 self.story_state())

        res = save_blob.save_to_disk(password)
        if res:
            self.save_settings_to_disk()

        return (res, password)

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
            item = self._action_to_target.get_item()
            if item is None:
                return self._action_to_target

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
        offs_x = cam_center[0] - self.screen_size[0] // 2
        offs_y = cam_center[1] - self.screen_size[1] // 2
        return (offs_x, offs_y)

    def get_actual_camera_center(self):
        x = self._camera_center_in_world[0] - (self._camera_center_on_screen[0] - self.screen_size[0] // 2)
        y = self._camera_center_in_world[1] - (self._camera_center_on_screen[1] - self.screen_size[1] // 2)
        return (x, y)

    def get_world_camera_size(self):
        return self.screen_size
        
    def screen_to_world_coords(self, point):
        cam = self.get_actual_camera_xy()
        return (cam[0] + point[0], cam[1] + point[1])
        
    def update(self, world):
        self.event_queue().flip()
        if world is not None:
            for e in self.event_queue().all_events():
                print(e)
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


def create_new(menu, from_pw=None):
    import src.ui.menus as menus
    menu_manager = menus.MenuManager(menu)

    import src.game.dialog as dialog
    dialog_manager = dialog.DialogManager()

    import src.worldgen.zones as zones
    new_instance = GlobalState(zones.first_zone_id(), menu_manager, dialog_manager, StoryState())

    import src.game.inventory as inventory
    inventory_state = inventory.InventoryState()

    import src.game.gameengine as gameengine
    import src.game.stats as stats
    player_state = gameengine.ActorState("player", 5, stats.default_player_stats(), inventory_state, 0)
    player_controller = gameengine.PlayerController()

    new_instance.set_player_state(player_state, player_controller)

    loaded_from_pw = False

    if from_pw is not None:
        save_data = SaveDataBlob.load_from_disk(from_pw)
        if save_data is not None:
            loaded_from_pw = True

            for xy in save_data.equipment_positions:
                item = save_data.equipment_positions[xy]
                if player_state.inventory().equip_grid.can_place(item, xy):
                    player_state.inventory().equip_grid.place(item, xy)
                else:
                    print("ERROR: cannot place equipment item at position ({}, {}):\n{}".format(xy[0], xy[1], item))

            for xy in save_data.inventory_positions:
                item = save_data.inventory_positions[xy]
                if player_state.inventory().inv_grid.can_place(item, xy):
                    player_state.inventory().inv_grid.place(item, xy)
                else:
                    print("ERROR: cannot place inventory item at position ({}, {}):\n{}".format(xy[0], xy[1], item))

            player_state.set_hp(player_state.max_hp())

            new_instance._story_state = save_data.story_state

            if save_data.zone_id in zones._ALL_ZONES:
                new_instance.initial_zone_id = save_data.zone_id

    set_instance(new_instance)

