import pathlib
import os
import traceback
import datetime

import src.utils.util as util

_all_tags = []


_LOADED_FILES = []


def get_path_to_saves():
    return str(pathlib.Path("save_data/saves/"))


def has_files_on_disk():
    for _ in all_files_on_disk():
        return True
    return False


def all_files_on_disk():
    dir_path = get_path_to_saves()
    if not os.path.isdir(dir_path):
        return

    for filename in os.listdir(dir_path):
        fpath = str(pathlib.Path(dir_path, filename))
        if os.path.isfile(fpath):
            name, ext = os.path.splitext(fpath)
            if ext != ".txt":
                continue  # some random file? whatever
            else:
                yield fpath


def reload_all_save_data_from_disk():
    _LOADED_FILES.clear()

    for fpath in all_files_on_disk():
        try:
            save_blob = load_file(fpath)
            if save_blob is not None:
                _LOADED_FILES.append(save_blob)
        except:
            print("ERROR: failed to read save data from: {}".format(fpath))
            traceback.print_exc()

    _LOADED_FILES.sort(key=lambda data: data.get_last_modified_time_for_sorting(), reverse=True)


def get_all_save_data(load_if_needed=True):
    if len(_LOADED_FILES) == 0 and load_if_needed:
        reload_all_save_data_from_disk()

    return list(_LOADED_FILES)


def load_file(path_to_file):
    json_blob = util.Utils.load_json_from_path(path_to_file)

    ret = SaveDataBlob()

    ret.set(SaveDataTags.GAME_UID, util.Utils.read_string(json_blob, SaveDataTags.GAME_UID, None))
    ret.set(SaveDataTags.VERSION_NUM, util.Utils.read_string(json_blob, SaveDataTags.VERSION_NUM, None))

    ret.set(SaveDataTags.LAST_MODIFIED_TIME, util.Utils.read_int(json_blob, SaveDataTags.LAST_MODIFIED_TIME, None))
    ret.set(SaveDataTags.ELAPSED_TIME, util.Utils.read_int(json_blob, SaveDataTags.ELAPSED_TIME, None))
    ret.set(SaveDataTags.KILL_COUNT, util.Utils.read_int(json_blob, SaveDataTags.KILL_COUNT, None))
    ret.set(SaveDataTags.DEATH_COUNT, util.Utils.read_int(json_blob, SaveDataTags.DEATH_COUNT, None))

    ret.set(SaveDataTags.SPAWN_ID, util.Utils.read_string(json_blob, SaveDataTags.SPAWN_ID, None))

    # TODO loading items

    invalid_tags = ret.get_invalid_tags()
    if len(invalid_tags) > 0:
        pretty_string = ", ".join([invalid_tags[t] for t in invalid_tags])
        raise ValueError("Invalid tags in {}: {}".format(path_to_file, pretty_string))

    return ret


class SaveDataTags:

    # string: the unique identifier for the run, used to allow / prohibit overwrites
    GAME_UID = util.Utils.add_to_list_and_return("game_uid", _all_tags)

    # string: version the file was saved in, used for bridging
    VERSION_NUM = util.Utils.add_to_list_and_return("version_num", _all_tags)

    # integer: time (in milliseconds) that this file was last saved
    LAST_MODIFIED_TIME = util.Utils.add_to_list_and_return("last_modified_time", _all_tags)

    # integer: number of ticks that have elapsed in the run so far
    ELAPSED_TIME = util.Utils.add_to_list_and_return("elapsed_time", _all_tags)

    # integer: kill count of the run so far
    KILL_COUNT = util.Utils.add_to_list_and_return("kill_count", _all_tags)

    # integer: death count of the run so far
    DEATH_COUNT = util.Utils.add_to_list_and_return("death_count", _all_tags)

    # items in the player's possession. note that the "held" item is never saved / loaded
    INVENTORY_ITEMS = util.Utils.add_to_list_and_return("inventory_items", _all_tags)
    INVENTORY_ITEM_POSITIONS = util.Utils.add_to_list_and_return("inventory_item_positions", _all_tags)
    EQUIPMENT_ITEMS = util.Utils.add_to_list_and_return("equipment_items", _all_tags)
    EQUIPMENT_ITEM_POSITIONS = util.Utils.add_to_list_and_return("equipment_item_positions", _all_tags)

    # string: the save location's identifier
    SPAWN_ID = util.Utils.add_to_list_and_return("save_location_id", _all_tags)

    @staticmethod
    def is_item_tag(tag):
        return tag in (SaveDataTags.INVENTORY_ITEMS, SaveDataTags.INVENTORY_ITEM_POSITIONS,
                       SaveDataTags.EQUIPMENT_ITEMS, SaveDataTags.EQUIPMENT_ITEM_POSITIONS)


class SaveDataBlob:

    # item storage locations
    INVENTORY = 0
    EQUIPMENT = 1

    def __init__(self):
        self.tags = {}
        for t in _all_tags:
            if SaveDataTags.is_item_tag(t):
                self.tags[t] = []
            else:
                self.tags[t] = None

    def get(self, tag):
        if SaveDataTags.is_item_tag(tag):
            raise ValueError("cannot get item-type tag \"{}\" using basic set method".format(tag))
        return self.tags[tag]

    def set(self, tag, value):
        if SaveDataTags.is_item_tag(tag):
            raise ValueError("cannot set item-type tag \"{}\" using basic get method".format(tag))

        if value is None or isinstance(value, int) or isinstance(value, str):
            self.tags[tag] = value
        else:
            raise ValueError("unexpected data type for tag \"{}\": {}".format(tag, value))

    def get_pretty_string(self, max_length=-1):
        save_id = self.get(SaveDataTags.SPAWN_ID)
        zone_name = None
        if save_id is not None:
            import src.worldgen.zones as zones
            zone_id = zones.get_zone_id_for_save_id(save_id)
            if zone_id is not None:
                zone_name = zones.get_zone(zone_id).get_name()
        if zone_name is None:
            return "UNKNOWN[{}={}]".format(SaveDataTags.SPAWN_ID, save_id)

        elapsed_time = self.get(SaveDataTags.ELAPSED_TIME)
        if elapsed_time is None:
            elapsed_time_str = "???"
        elif elapsed_time >= 216000000:  # you will NOT break my UI
            elapsed_time_str = "999:59:59"
        else:
            elapsed_time_str = util.Utils.ticks_to_time_string(elapsed_time, fps=60)

        save_time = self.get(SaveDataTags.LAST_MODIFIED_TIME)
        if save_time is None:
            save_time_str = "?-?-20??"
        else:
            save_time_str = datetime.datetime.fromtimestamp(save_time).strftime("%m-%d-%Y")
            if len(save_time_str) > 10:  # protect the UI
                save_time_str = save_time_str[0:7] + "..."

        date_part = " ({}) {}".format(elapsed_time_str, save_time_str)

        if 0 < max_length <= 3:
            max_length = 4

        if len(zone_name) > 0 and 0 < max_length < len(zone_name) + len(date_part):
            new_zone_name_length = max(1, max_length - len(date_part) - 3)
            zone_name = zone_name[0:new_zone_name_length] + "..."

        res = zone_name + date_part
        if 0 < max_length < len(res):
            return res[0:max_length - 3] + "..."

        return res

    def get_invalid_tags(self):
        """returns: tag_id -> error message"""
        res = {}
        for t in _all_tags:
            if t not in self.tags:
                res[t] = "{} is missing".format(t)
            elif self.tags[t] is None:
                res[t] = "{} is None".format(t)

        t1 = SaveDataTags.INVENTORY_ITEMS
        t2 = SaveDataTags.INVENTORY_ITEM_POSITIONS
        if t1 not in res and t2 not in res:
            l1 = len(self.tags[t1])
            l2 = len(self.tags[t2])
            if l1 != l2:
                res[t2] = "{} has incorrect length: {} (expected {})".format(t2, l2, l1)

        t1 = SaveDataTags.EQUIPMENT_ITEMS
        t2 = SaveDataTags.EQUIPMENT_ITEM_POSITIONS
        if t1 not in res and t2 not in res:
            l1 = len(self.tags[t1])
            l2 = len(self.tags[t2])
            if l1 != l2:
                res[t2] = "{} has incorrect length: {} (expected {})".format(t2, l2, l1)

        import src.worldgen.zones as zones
        t = SaveDataTags.SPAWN_ID
        save_zone = zones.get_zone_id_for_save_id(self.tags[t])
        if save_zone is None:
            res[t] = "{} isn't recognized: {}".format(t, self.tags[t])

        return res

    def add_item(self, item, pos, location):
        pass

    def get_all_items_and_positions(self, location):
        """returns: list of (item, (int x, int y))"""
        return []

    def get_last_modified_time_for_sorting(self):
        res = self.get(SaveDataTags.LAST_MODIFIED_TIME)
        if res is None or not isinstance(res, int):
            return 0
        else:
            return res

