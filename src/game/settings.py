import pygame
from src.utils.util import Utils
import src.game.sound_effects as sound_effects
import src.game.music as music
import src.game.debug as debug
import src.game.pathutils as pathutils

import pathlib
import traceback

ALL_SETTINGS = {}
ALL_KEY_SETTINGS = []


FILENAME = "settings.json"
KEYS_FILENAME = "key_settings.json"
DEBUG_FILENAME = "debug_settings.json"


class Setting:

    def __init__(self, name, key, default, cleaner=None, on_set=None, filename=FILENAME):
        self.name = name
        self.key = key
        self.default = default
        ALL_SETTINGS[key] = self

        self._cleaner = cleaner
        self._on_setter = on_set

        self.filename = filename

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


_num_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
             pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]


class KeyBindings:

    # configurable
    KEY_UP = Setting("move up", "UP", [pygame.K_w], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_LEFT = Setting("move down", "LEFT", [pygame.K_a], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_RIGHT = Setting("move right", "RIGHT", [pygame.K_d], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_DOWN = Setting("move down", "DOWN", [pygame.K_s], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_SKIP_TURN = Setting("skip turn", "SKIP", [pygame.K_SPACE], cleaner=clean_keys, filename=KEYS_FILENAME)

    KEY_INVENTORY = Setting("inventory", "INVENTORY", [pygame.K_e], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_ROTATE_CW = Setting("rotate item", "ROTATE_CW", [pygame.K_r], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_MAP = Setting("map", "MAP", [pygame.K_m], cleaner=clean_keys, filename=KEYS_FILENAME)

    # not configurable
    KEY_MENU_UP = Setting("menu up", "MENU_UP", [pygame.K_UP], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_MENU_DOWN = Setting("menu down", "MENU_DOWN", [pygame.K_DOWN], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_MENU_LEFT = Setting("menu left", "MENU_LEFT", [pygame.K_LEFT], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_MENU_RIGHT = Setting("menu right", "MENU_RIGHT", [pygame.K_RIGHT], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_ENTER = Setting("enter", "ENTER", [pygame.K_RETURN], cleaner=clean_keys, filename=KEYS_FILENAME)
    KEY_EXIT = Setting("escape", "EXIT", [pygame.K_ESCAPE], cleaner=clean_keys, filename=KEYS_FILENAME)

    KEY_MAPPED_ACTIONS = [Setting("action " + str(i), "ACTION_" + str(i), [_num_keys[i]], cleaner=clean_keys, filename=KEYS_FILENAME) for i in range(1, 7)]


class MiscSettings:

    FINISHED_TUTORIALS = Setting("finished tutorials", "FINISHED_TUTORIALS", [])


def pixel_scale_options():
    return [0, 1, 2, 3, 4]  # 0 is automatic mode, where it scales based on window size


class VideoSettings:

    PIXEL_SCALE = Setting("pixel scale", "PIXEL_SCALE", pixel_scale_options()[0], filename=None,
                          cleaner=lambda x: x if x in pixel_scale_options() else pixel_scale_options()[0])


class SoundSettings:

    EFFECTS_VOLUME = Setting("effects volume", "EFFECTS_VOLUME", 60,
                             cleaner=lambda val: Utils.bound(int(val), 0, 100),
                             on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(for_effects=True, for_music=False))

    MUSIC_VOLUME = Setting("music volume", "MUSIC_VOLUME", 100,
                           cleaner=lambda val: Utils.bound(int(val), 0, 100),
                           on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(for_effects=False, for_music=True))

    MUSIC_MUTED = Setting("music muted", "MUSIC_MUTED", False,
                          cleaner=lambda val: bool(val),
                          on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(for_effects=False, for_music=True))

    EFFECTS_MUTED = Setting("effects muted", "EFFECTS_MUTED", False,
                            cleaner=lambda val: bool(val),
                            on_set=lambda sttgs, old_val, new_val: sttgs.update_volume_levels(for_effects=True, for_music=False))


class DebugSettings:

    DEBUG_ENABLED = Setting("debug enabled", "DEBUG_ENABLED", False,
                            cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    IGNORE_LOOT_LEVELS = Setting("ignore loot levels", "IGNORE_LOOT_LEVELS", False,
                                 cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    PLAYER_CANT_DIE = Setting("invincible", "PLAYER_CANT_DIE", False,
                              cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    INSTA_KILL = Setting("+99 attack", "INSTA_KILL", False,
                         cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    MAP_SEES_ALL = Setting("super map", "MAP_SEES_ALL", False,
                           cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    UNLIMITED_TRADES = Setting("unlimited trades", "UNLIMITED_TRADES", False,
                               cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    HOLY_ARTIFACTS_100x_MORE_LIKELY = Setting("holy cannoli", "HOLY_ARTIFACTS_100x_MORE_LIKELY", False,
                                              cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)

    NEVER_SHOW_TUTORIALS = Setting("never show tutorials", "NEVER_SHOW_TUTORIALS", False,
                                   cleaner=lambda val: bool(val), filename=DEBUG_FILENAME)


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
            setting.on_set(self, old_val, new_val)

        except Exception:
            print("ERROR: failed to set {} to {}".format(setting.key, val))
            traceback.print_exc()

    def all_filenames(self):
        res = set()
        for key in ALL_SETTINGS:
            if ALL_SETTINGS[key].filename is not None:
                res.add(ALL_SETTINGS[key].filename)

        if not debug.is_dev() and DEBUG_FILENAME in res:
            res.remove(DEBUG_FILENAME)

        return [x for x in res]

    def _to_filepath(self, filename):
        save_data_dir = pathutils.get_save_data_path()
        return pathlib.Path(save_data_dir, filename)

    def load_from_disk(self, filenames=None):
        if filenames is None:
            filenames = self.all_filenames()

        for filename in filenames:
            filepath = self._to_filepath(filename)
            if not filepath.exists():
                print("INFO: setting file {} doesn't exist, skipping loading those prefs".format(filepath))
                continue

            try:
                loaded_values = Utils.load_json_from_path(filepath)
                for key in loaded_values:
                    val = loaded_values[key]
                    if key in ALL_SETTINGS:
                        if ALL_SETTINGS[key].filename == filename:
                            self.set(ALL_SETTINGS[key], val)
                        else:
                            print("WARN: setting was saved into wrong file {} -> {}, skipping it".format(filename, key))
                            continue
                    else:
                        print("INFO: skipping unknown setting: {} -> {}".format(filename, key))

                print("INFO: successfully loaded settings from {}".format(filepath))

            except (OSError, ValueError, TypeError):
                print("ERROR: failed to load settings from {}".format(filepath))
                traceback.print_exc()

            except Exception:
                print("ERROR: unexpected error while loading settings from {}".format(filepath))
                traceback.print_exc()

    def save_to_disk(self, filenames=None):
        if filenames is None:
            filenames = self.all_filenames()

        blob_per_file = {}  # filename -> {key -> value}
        for filename in filenames:
            blob_per_file[filename] = {}

        for key in self.values:
            filename = ALL_SETTINGS[key].filename
            if filename in blob_per_file:
                blob_per_file[filename][key] = self.values[key]

        for filename in blob_per_file:
            blob = blob_per_file[filename]
            filepath = self._to_filepath(filename)

            try:
                Utils.save_json_to_path(blob, filepath)
                print("INFO: successfully saved settings to {}".format(filepath))

            except Exception:
                print("ERROR: failed to save settings to {}".format(filepath))
                traceback.print_exc()

    def up_key(self):
        return self.get(KeyBindings.KEY_UP)

    def left_key(self):
        return self.get(KeyBindings.KEY_LEFT)

    def right_key(self):
        return self.get(KeyBindings.KEY_RIGHT)

    def down_key(self):
        return self.get(KeyBindings.KEY_DOWN)

    def skip_turn_key(self):
        return self.get(KeyBindings.KEY_SKIP_TURN)

    def menu_up_key(self):
        return self.get(KeyBindings.KEY_MENU_UP)

    def menu_down_key(self):
        return self.get(KeyBindings.KEY_MENU_DOWN)

    def menu_left_key(self):
        return self.get(KeyBindings.KEY_MENU_LEFT)

    def menu_right_key(self):
        return self.get(KeyBindings.KEY_MENU_RIGHT)

    def inventory_key(self):
        return self.get(KeyBindings.KEY_INVENTORY)

    def exit_key(self):
        return self.get(KeyBindings.KEY_EXIT)

    def enter_key(self):
        return self.get(KeyBindings.KEY_ENTER)

    def rotate_cw_key(self):
        return self.get(KeyBindings.KEY_ROTATE_CW)

    def map_key(self):
        return self.get(KeyBindings.KEY_MAP)

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
        return len(KeyBindings.KEY_MAPPED_ACTIONS)

    def action_key(self, num):
        if num < 0 or num >= self.num_mapped_actions():
            print("WARN: num out of range for {} mapped actions: {}".format(
                self.num_mapped_actions(), num))
            return []

        return self.get(KeyBindings.KEY_MAPPED_ACTIONS[num])

    def clear_finished_tutorials(self):
        self.set(MiscSettings.FINISHED_TUTORIALS, [])

    def get_tutorial_finished(self, tut_id):
        return tut_id in self.get(MiscSettings.FINISHED_TUTORIALS)

    def set_tutorial_finished(self, tut_id, val):
        if self.get_tutorial_finished(tut_id) != val:
            all_finished_tuts = self.get(MiscSettings.FINISHED_TUTORIALS)
            if val is False:
                all_finished_tuts.remove(tut_id)
            else:
                all_finished_tuts.append(tut_id)
            self.set(MiscSettings.FINISHED_TUTORIALS, all_finished_tuts)

    def update_volume_levels(self, for_music=True, for_effects=True):
        if for_music:
            vol_level = 0 if self.get(SoundSettings.MUSIC_MUTED) else self.get(SoundSettings.MUSIC_VOLUME)
            new_val = Utils.bound(vol_level / 100, 0, 1.0)
            music.set_master_volume(new_val)

        if for_effects:
            vol_level = 0 if self.get(SoundSettings.EFFECTS_MUTED) else self.get(SoundSettings.EFFECTS_VOLUME)
            new_val = Utils.bound(vol_level / 100, 0, 1.0)
            sound_effects.set_volume(new_val)

    def pixel_scale(self):
        return self.get(VideoSettings.PIXEL_SCALE)

    def set_pixel_scale(self, val):
        self.set(VideoSettings.PIXEL_SCALE, val)

    def pixel_scale_options(self):
        return pixel_scale_options()

