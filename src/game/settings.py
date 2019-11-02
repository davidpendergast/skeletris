import pygame
from src.utils.util import Utils
import src.game.sound_effects as sound_effects

ALL_SETTINGS = {}
ALL_KEY_SETTINGS = []


class Setting:
    def __init__(self, name, key, default, cleaner=None, on_set=None):
        self.name = name
        self.key = key
        self.default = default
        ALL_SETTINGS[key] = self

        self._cleaner = cleaner
        self._on_setter = on_set

    def clean(self, new_value):
        if self._cleaner is not None:
            return self._cleaner(new_value)
        else:
            return new_value

    def on_set(self, sttgs, old_value, new_value):
        if self._on_setter is not None:
            self._on_setter(sttgs, old_value, new_value)


class KeySetting(Setting):
    def __init__(self, name, key, default, editable=True):
        Setting.__init__(self, name, key, default)
        self.editable = editable
        ALL_KEY_SETTINGS.append(self)


def clean_keys(val):
    if val is None or not isinstance(val, list):
        return []
    else:
        return val


def clean_with_hardcoded(hard_key):
    def _cleaner(val):
        val = clean_keys(val)
        if hard_key not in val:
            val.append(hard_key)
        return val
    return _cleaner


# these are all configurable
KEY_UP = Setting("move up", "UP", [pygame.K_w], cleaner=clean_keys)
KEY_LEFT = Setting("move down", "LEFT", [pygame.K_a], cleaner=clean_keys)
KEY_RIGHT = Setting("move right", "RIGHT", [pygame.K_d], cleaner=clean_keys)
KEY_DOWN = Setting("move down", "DOWN", [pygame.K_s], cleaner=clean_keys)
KEY_SKIP_TURN = Setting("skip turn", "SKIP", [pygame.K_SPACE], cleaner=clean_keys)

KEY_INVENTORY = Setting("inventory", "INVENTORY", [pygame.K_r], cleaner=clean_keys)
KEY_ROTATE_CW = Setting("rotate item", "ROTATE_CW", [pygame.K_e], cleaner=clean_keys)
KEY_MAP = Setting("map", "MAP", [pygame.K_m], cleaner=clean_keys)
# KEY_HELP = Setting("help", "HELP", [pygame.K_h], cleaner=clean_keys)

num_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]

KEY_MAPPED_ACTIONS = [Setting("action " + str(i), "ACTION_" + str(i), [num_keys[i]], cleaner=clean_keys) for i in range(1, 7)]

# these are locked
KEY_MENU_UP = Setting("menu up", "MENU_UP", [pygame.K_UP], cleaner=clean_keys)
KEY_MENU_DOWN = Setting("menu down", "MENU_DOWN", [pygame.K_DOWN], cleaner=clean_keys)
KEY_ENTER = Setting("enter", "ENTER", [pygame.K_RETURN], cleaner=clean_keys)
KEY_EXIT = Setting("escape", "EXIT", [pygame.K_ESCAPE], cleaner=clean_keys)

AUTO_ACTIVATE_EQUIPMENT = Setting("auto equip", "AUTO_ACTIVATE_EQUIPMENT", True, cleaner=lambda x: bool(x))

EFFECTS_VOLUME = Setting("effects volume", "EFFECTS_VOLUME", 100,
                         cleaner=lambda val: Utils.bound(int(val), 0, 100),
                         on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(effects=True, music=False))

MUSIC_VOLUME = Setting("music volume", "MUSIC_VOLUME", 100,
                       cleaner=lambda val: Utils.bound(int(val), 0, 100),
                       on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(effects=False, music=True))

MUSIC_MUTED = Setting("music muted", "MUSIC_MUTED", False,
                      cleaner=lambda val: bool(val),
                      on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(effects=False, music=True))

EFFECTS_MUTED = Setting("effects muted", "EFFECTS_MUTED", False,
                        cleaner=lambda val: bool(val),
                        on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(effects=True, music=False))

FINISHED_TUTORIALS = Setting("finished tutorials", "FINISHED_TUTORIALS", [])


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
            setting.on_set(self, old_val, new_val)
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
        if num < 0 or num >= self.num_mapped_actions():
            print("WARN: num out of range for {} mapped actions: {}".format(
                self.num_mapped_actions(), num))
            return []

        return self.get(KEY_MAPPED_ACTIONS[num])

    def clear_finished_tutorials(self):
        self.set(FINISHED_TUTORIALS, [])

    def get_tutorial_finished(self, tut_id):
        return tut_id in self.get(FINISHED_TUTORIALS)

    def set_tutorial_finished(self, tut_id, val):
        if self.get_tutorial_finished(tut_id) != val:
            all_finished_tuts = self.get(FINISHED_TUTORIALS)
            if val is False:
                all_finished_tuts.remove(tut_id)
            else:
                all_finished_tuts.append(tut_id)
            self.set(FINISHED_TUTORIALS, all_finished_tuts)

    def update_volume_levels(self, music=True, effects=True):
        if music:
            vol_level = 0 if self.get(MUSIC_MUTED) else self.get(MUSIC_VOLUME)
            new_val = Utils.bound(vol_level / 100, 0, 1.0)
            pygame.mixer.music.set_volume(new_val)

        if effects:
            vol_level = 0 if self.get(EFFECTS_MUTED) else self.get(EFFECTS_VOLUME)
            new_val = Utils.bound(vol_level / 100, 0, 1.0)
            sound_effects.set_volume(new_val)

