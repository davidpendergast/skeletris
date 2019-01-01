import pygame
from src.utils.util import Utils
import src.utils.passwordgen as passwordgen

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
KEY_UP = Setting("move up", "UP", [pygame.K_w])
KEY_LEFT = Setting("move down", "LEFT", [pygame.K_a])
KEY_RIGHT = Setting("move right", "RIGHT", [pygame.K_d])
KEY_DOWN = Setting("move down", "DOWN", [pygame.K_s])
KEY_ATTACK = Setting("attack", "ATTACK", [pygame.K_j])
KEY_INVENTORY = Setting("inventory", "INVENTORY", [pygame.K_r])
KEY_ROTATE_CW = Setting("rotate item", "ROTATE_CW", [pygame.K_e])
KEY_INTERACT = Setting("interact", "INTERACT", [pygame.K_i])
KEY_POTION = Setting("potion", "POTION", [pygame.K_k])


# these are locked
KEY_MENU_UP = Setting("menu up", "MENU_UP", [pygame.K_UP])
KEY_MENU_DOWN = Setting("menu down", "MENU_DOWN", [pygame.K_DOWN])
KEY_ENTER = Setting("enter", "ENTER", [pygame.K_RETURN])
KEY_EXIT = Setting("escape", "EXIT", [pygame.K_ESCAPE])

MASTER_VOLUME = Setting("master volume", "MASTER_VOLUME", 100)
MASTER_VOLUME.clean = lambda val: Utils.bound(int(val), 0, 100)
# MASTER_VOLUME.on_set = lambda o, n: pygame.mixer.set_volume(n / 100)

MUSIC_VOLUME = Setting("music volume", "MUSIC_VOLUME", 100)
MUSIC_VOLUME.clean = lambda val: Utils.bound(int(val), 0, 100)
MUSIC_VOLUME.on_set = lambda old_val, new_val: pygame.mixer.music.set_volume(new_val / 100)

LAST_PASSWORD = Setting("last password", "LAST_PASSWORD", None)
LAST_PASSWORD.clean = lambda val: val if passwordgen.is_valid(val) else None


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

    def menu_up_key(self):
        return self.get(KEY_MENU_UP)

    def menu_down_key(self):
        return self.get(KEY_MENU_DOWN)

    def attack_key(self):
        return self.get(KEY_ATTACK)

    def inventory_key(self):
        return self.get(KEY_INVENTORY)

    def interact_key(self):
        # kinda a hack, but I want enter to also be usable as the interact key.
        return self.get(KEY_INTERACT) + self.enter_key()

    def potion_key(self):
        return self.get(KEY_POTION)

    def exit_key(self):
        return self.get(KEY_EXIT)

    def enter_key(self):
        return self.get(KEY_ENTER)

    def rotate_cw_key(self):
        return self.get(KEY_ROTATE_CW)
