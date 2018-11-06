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


MASTER_VOLUME = Setting("MASTER_VOLUME", 100)
MASTER_VOLUME.clean = lambda s, val: Utils.bound(int(val), 0, 100)
# MASTER_VOLUME.on_set = lambda o, n: pygame.mixer.set_volume(n / 100)

MUSIC_VOLUME = Setting("MUSIC_VOLUME", 100)
MUSIC_VOLUME.clean = lambda s, val: Utils.bound(int(val), 0, 100)
MUSIC_VOLUME.on_set = lambda o, n: pygame.mixer.music.set_volume(n / 100)


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
            setting.on_set(old_val, new_val)
        except ValueError:
            print("ERROR: failed to set {} to {}".format(setting.key, val))

    def load_from_file(self, filename):
        pass

    def save_to_file(self, filename):
        pass