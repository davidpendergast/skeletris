import pygame
from src.utils.util import Utils

ALL_SETTINGS = {}


class Setting:
    def __init__(self, key, default):
        self.key = key
        self.default = default
        ALL_SETTINGS[key] = self

    def clean(self, new_value):
        return new_value

    def on_set(self, old_value, new_value, gs):
        pass


KEY_UP = Setting("UP", [pygame.K_w, pygame.K_UP])
KEY_LEFT = Setting("LEFT", [pygame.K_a, pygame.K_LEFT])
KEY_RIGHT = Setting("RIGHT", [pygame.K_d, pygame.K_RIGHT])
KEY_DOWN = Setting("DOWN", [pygame.K_s, pygame.K_DOWN])
KEY_ATTACK = Setting("ATTACK", [pygame.K_j, pygame.K_x, pygame.K_SPACE])
KEY_INVENTORY = Setting("INVENTORY", [pygame.K_r])
KEY_ROTATE_CW = Setting("ROTATE_CW", [pygame.K_e])
KEY_INTERACT = Setting("INTERACT", [pygame.K_RETURN, pygame.K_i])
KEY_KILL = Setting("KILL", [pygame.K_k])
KEY_ENTER = Setting("ENTER", [pygame.K_RETURN])
KEY_EXIT = Setting("EXIT", [pygame.K_ESCAPE])
KEY_POTION = Setting("POTION", [pygame.K_q])

MASTER_VOLUME = Setting("MASTER_VOLUME", 100)
MASTER_VOLUME.clean = lambda val: Utils.bound(int(val), 0, 100)
# MASTER_VOLUME.on_set = lambda o, n: pygame.mixer.set_volume(n / 100)

MUSIC_VOLUME = Setting("MUSIC_VOLUME", 100)
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
        pass

    def save_to_file(self, filename):
        pass

    def up_key(self):
        return self.get(KEY_UP)

    def left_key(self):
        return self.get(KEY_LEFT)

    def right_key(self):
        return self.get(KEY_RIGHT)

    def down_key(self):
        return self.get(KEY_DOWN)

    def attack_key(self):
        return self.get(KEY_ATTACK)

    def inventory_key(self):
        return self.get(KEY_INVENTORY)

    def interact_key(self):
        return self.get(KEY_INTERACT)

    def potion_key(self):
        return self.get(KEY_POTION)

    def exit_key(self):
        return self.get(KEY_EXIT)

    def enter_key(self):
        return self.get(KEY_ENTER)

    def rotate_cw_key(self):
        return self.get(KEY_ROTATE_CW)