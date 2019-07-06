import pygame
from src.utils.util import Utils
import src.game.sound_effects as sound_effects

ALL_SETTINGS = {}
ALL_KEY_SETTINGS = []


class Setting:
    def __init__(self, name, key, default):
        self.name = name
        self.key = key
        self.default = default
        ALL_SETTINGS[key] = self

    def clean(self, new_value):
        return new_value

    def on_set(self, old_value, new_value):
        pass


class KeySetting(Setting):
    def __init__(self, name, key, default, editable=True):
        Setting.__init__(self, name, key, default)
        self.editable = editable
        ALL_KEY_SETTINGS.append(self)


# these are all configurable
KEY_UP = Setting("move up", "UP", [pygame.K_w, pygame.K_UP])
KEY_LEFT = Setting("move down", "LEFT", [pygame.K_a, pygame.K_LEFT])
KEY_RIGHT = Setting("move right", "RIGHT", [pygame.K_d, pygame.K_RIGHT])
KEY_DOWN = Setting("move down", "DOWN", [pygame.K_s, pygame.K_DOWN])
KEY_SKIP_TURN = Setting("skip turn", "SKIP", [pygame.K_RETURN, pygame.K_SPACE])

KEY_INVENTORY = Setting("inventory", "INVENTORY", [pygame.K_i])
KEY_ROTATE_CW = Setting("rotate item", "ROTATE_CW", [pygame.K_e])
KEY_MAP = Setting("map", "MAP", [pygame.K_m])
KEY_HELP = Setting("help", "HELP", [pygame.K_h])

num_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]

KEY_MAPPED_ACTIONS = [Setting("action " + str(i), "ACTION_" + str(i), [num_keys[i]]) for i in range(1, 7)]

# these are locked
KEY_MENU_UP = Setting("menu up", "MENU_UP", [pygame.K_UP])
KEY_MENU_DOWN = Setting("menu down", "MENU_DOWN", [pygame.K_DOWN])
KEY_ENTER = Setting("enter", "ENTER", [pygame.K_RETURN])
KEY_EXIT = Setting("escape", "EXIT", [pygame.K_ESCAPE])

EFFECTS_VOLUME = Setting("effects volume", "EFFECTS_VOLUME", 100)
EFFECTS_VOLUME.clean = lambda val: Utils.bound(int(val), 0, 100)
EFFECTS_VOLUME.on_set = lambda old_val, new_val: sound_effects.set_volume(new_val / 100)

MUSIC_VOLUME = Setting("music volume", "MUSIC_VOLUME", 100)
MUSIC_VOLUME.clean = lambda val: Utils.bound(int(val), 0, 100)
MUSIC_VOLUME.on_set = lambda old_val, new_val: pygame.mixer.music.set_volume(new_val / 100)


class Settings:

    def __init__(self):
        self.values = {}
        for setting_key in ALL_SETTINGS:
            self.values[setting_key] = ALL_SETTINGS[setting_key].default

    def get(self, setting):
        return self.values[setting.key]

    def set(self, setting, val):
        try:
            old_val = self.values[setting.key]
            new_val = setting.clean(val)
            self.values[setting.key] = new_val
            print("INFO: updated setting {} from {} to {}.".format(setting.key, old_val, new_val))
            setting.on_set(old_val, new_val)
        except ValueError:
            print("ERROR: failed to set {} to {}".format(setting.key, val))

    def load_from_file(self, filename):
        try:
            loaded_values = Utils.load_json_from_path(filename)
            for key in loaded_values:
                val = loaded_values[key]
                if key in ALL_SETTINGS:
                    self.set(ALL_SETTINGS[key], val)
                else:
                    print("INFO: skipping unknown setting: {}".format(key))
            print("INFO: successfully loaded settings from {}".format(filename))

        except Exception:
            print("ERROR: failed to load settings from {}".format(filename))

    def save_to_file(self, filename):
        try:
            Utils.save_json_to_path(self.values, filename)
            print("INFO: successfully saved settings to {}".format(filename))
        except Exception:
            print("ERROR: failed to save settings to {}".format(filename))

    def up_key(self):
        return self.get(KEY_UP)

    def left_key(self):
        return self.get(KEY_LEFT)

    def right_key(self):
        return self.get(KEY_RIGHT)

    def down_key(self):
        return self.get(KEY_DOWN)

    def skip_turn_key(self):
        return self.get(KEY_SKIP_TURN)

    def menu_up_key(self):
        return self.get(KEY_MENU_UP)

    def menu_down_key(self):
        return self.get(KEY_MENU_DOWN)

    def inventory_key(self):
        return self.get(KEY_INVENTORY)

    def exit_key(self):
        return self.get(KEY_EXIT)

    def enter_key(self):
        return self.get(KEY_ENTER)

    def rotate_cw_key(self):
        return self.get(KEY_ROTATE_CW)

    def map_key(self):
        return self.get(KEY_MAP)

    def help_key(self):
        return self.get(KEY_HELP)

    def all_direction_keys(self):
        res = []
        res.extend(self.up_key())
        res.extend(self.down_key())
        res.extend(self.left_key())
        res.extend(self.right_key())
        return res

    def all_dialog_dismiss_keys(self):
        res = []
        res.extend(self.all_direction_keys())
        res.extend(self.enter_key())
        res.extend(self.rotate_cw_key())
        res.extend(self.skip_turn_key())
        return res

    def num_mapped_actions(self):
        return len(KEY_MAPPED_ACTIONS)

    def action_key(self, num):
        return self.get(KEY_MAPPED_ACTIONS[num])
