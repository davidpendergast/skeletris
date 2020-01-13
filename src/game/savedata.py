import src.utils.util as util
import pathlib
import os
import traceback

_all_tags = []


_LOADED_FILES = []


def get_path_to_saves():
    return str(pathlib.Path("save_data/saves/"))


def get_all_files(load_if_needed=True):
    if len(_LOADED_FILES) == 0 and load_if_needed:
        reload_all_files_from_disk()

    return list(_LOADED_FILES)


def reload_all_files_from_disk():
    _LOADED_FILES.clear()

    dir_path = get_path_to_saves()
    if not os.path.isdir(dir_path):
        return

    for fpath in os.listdir(dir_path):
        if os.path.isfile(fpath):
            try:
                save_blob = load_file(fpath)
                if save_blob is not None:
                    _LOADED_FILES.append(save_blob)
            except:
                print("ERROR: failed to read save data from: {}".format(fpath))
                traceback.print_exc()


def load_file(path_to_file):
    name, ext = os.path.splitext(path_to_file)
    if ext != "txt":
        return None  # some random file? whatever

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
            raise ValueError("cannot set item-type tag \"{}\" using basic set method".format(tag))
        return self.tags[tag]

    def set(self, tag, value):
        if SaveDataTags.is_item_tag(tag):
            raise ValueError("cannot get item-type tag \"{}\" using basic get method".format(tag))

        if not isinstance(value, int) and not isinstance(value, str):
            raise ValueError("unexpected data type for tag \"{}\": {}".format(tag, value))

        self.tags[tag] = value

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

        return res

    def add_item(self, item, pos, location):
        pass

    def get_all_items_and_positions(self, location):
        """returns: list of (item, (int x, int y))"""
        return []

