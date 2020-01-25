import pathlib
import os
import traceback
import datetime
import random

import src.utils.util as util
import src.game.pathutils as pathutils
import src.game.version as version
import src.items.itemencoder as itemencoder

_all_tags = []


_LOADED_FILES = []


WIN_SAVE_ID = "normal_win"


def get_path_to_saves():
    return str(pathutils.get_save_data_path(with_subpath="saves/"))


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


def make_new_filepath():
    dir_path = get_path_to_saves()
    used_names = set()
    for fp in all_files_on_disk():
        used_names.add(fp)

    for i in range(1, 100):
        num_str = str(i).zfill(2)
        name = str(pathlib.Path(dir_path, "save_{}.txt".format(num_str)))
        if name not in used_names:
            return name

    # we tried to be nice. purposely not checking for collisions here
    return str(pathlib.Path(dir_path, "save_{}.txt".format(get_rand_alphanumeric_string(10))))


def get_rand_alphanumeric_string(length):
    chars = "abcdefghijklmnopqrstuvwxyz" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "1234567890"
    return "".join([random.choice(chars) for _ in range(0, length)])


def make_brand_new_blob():
    res = SaveDataBlob()

    # about 10^-29 chance of collision
    res.set(SaveDataTags.GAME_UID, get_rand_alphanumeric_string(32))

    return res


def reload_all_save_data_from_disk():
    _LOADED_FILES.clear()

    uids_to_blobs = {}  # uid str -> SaveDataBlob

    for fpath in all_files_on_disk():
        try:
            save_blob = load_file(fpath)
            if save_blob is not None:
                uid = save_blob.get(SaveDataTags.GAME_UID)

                if uid not in uids_to_blobs:
                    uids_to_blobs[uid] = save_blob
                else:
                    print("WARN: files with duplicate GAME_UIDs detected: files=({}, {}), uid={}".format(
                        fpath, uids_to_blobs[uid].filepath, uid))

                    # choose the more recent one
                    new_blob_time = save_blob.get_last_modified_time_for_sorting()
                    old_blob_time = uids_to_blobs[uid].get_last_modified_time_for_sorting()

                    if new_blob_time > old_blob_time:
                        uids_to_blobs[uid] = save_blob
        except Exception:
            print("ERROR: failed to read save data from: {}".format(fpath))
            traceback.print_exc()

    for uid in uids_to_blobs:
        _LOADED_FILES.append(uids_to_blobs[uid])

    _LOADED_FILES.sort(key=lambda data: data.get_last_modified_time_for_sorting(), reverse=True)


def get_all_in_progress_save_data(load_if_needed=True):
    if len(_LOADED_FILES) == 0 and load_if_needed:
        reload_all_save_data_from_disk()

    return [blob for blob in _LOADED_FILES if not blob.is_completed()]


def get_all_completed_save_data(load_if_needed=True, filter_non_standard_versions=True):
    """Sorts by elapsed time."""
    if len(_LOADED_FILES) == 0 and load_if_needed:
        reload_all_save_data_from_disk()

    res = []
    for blob in _LOADED_FILES:
        if blob.is_completed() and (blob.has_standard_version() or not filter_non_standard_versions):
            res.append(blob)

    res.sort(key=lambda data: data.get_elapsed_time_for_sorting())
    return res


_MOCK_CHECKSUM = 3141529   # security feature
_CHECKSUM_MOD = 123342261  # a big prime


def load_file(path_to_file):
    json_blob = util.Utils.load_json_from_path(path_to_file)

    ret = SaveDataBlob(filepath=path_to_file)

    claimed_checksum = util.Utils.read_int(json_blob, SaveDataTags.CHECKSUM, -1)

    json_blob[SaveDataTags.CHECKSUM] = _MOCK_CHECKSUM
    actual_checksum = util.Utils.checksum(json_blob, m=_CHECKSUM_MOD)

    if SaveDataTags.VERSION_NUM in json_blob:
        try:
            vers_list = json_blob[SaveDataTags.VERSION_NUM]
            major = int(vers_list[0])
            minor = int(vers_list[1])
            bugfix = int(vers_list[2])
            desc = str(vers_list[3])

            if actual_checksum != claimed_checksum:
                print("WARN: checksum of {} is incorrect, marking as modified".format(path_to_file))
                ret.set(SaveDataTags.VERSION_NUM, (major, minor, bugfix, "MOD"))
            else:
                ret.set(SaveDataTags.VERSION_NUM, (major, minor, bugfix, desc))

        except Exception:
            traceback.print_exc()
            ret.set(SaveDataTags.VERSION_NUM, None)
    else:
        ret.set(SaveDataTags.VERSION_NUM, None)

    ret.set(SaveDataTags.GAME_UID, util.Utils.read_string(json_blob, SaveDataTags.GAME_UID, None))
    ret.set(SaveDataTags.LAST_MODIFIED_TIME, util.Utils.read_int(json_blob, SaveDataTags.LAST_MODIFIED_TIME, None))
    ret.set(SaveDataTags.ELAPSED_TIME, util.Utils.read_int(json_blob, SaveDataTags.ELAPSED_TIME, 0))
    ret.set(SaveDataTags.KILL_COUNT, util.Utils.read_int(json_blob, SaveDataTags.KILL_COUNT, 0))
    ret.set(SaveDataTags.TURN_COUNT, util.Utils.read_int(json_blob, SaveDataTags.TURN_COUNT, 0))
    ret.set(SaveDataTags.DEATH_COUNT, util.Utils.read_int(json_blob, SaveDataTags.DEATH_COUNT, 0))
    ret.set(SaveDataTags.CHECKPOINT_COUNT, util.Utils.read_int(json_blob, SaveDataTags.CHECKPOINT_COUNT, 1))
    ret.set(SaveDataTags.CHECKSUM, -1)  # only ever set at save time

    ret.set(SaveDataTags.SPAWN_ID, util.Utils.read_string(json_blob, SaveDataTags.SPAWN_ID, None))

    inv_items_tag = SaveDataTags.INVENTORY_ITEMS
    inv_pos_tag = SaveDataTags.INVENTORY_ITEM_POSITIONS
    inv_items, inv_positions = _load_items_from_json(json_blob, inv_items_tag, inv_pos_tag)

    ret.set(SaveDataTags.INVENTORY_ITEMS, inv_items)
    ret.set(SaveDataTags.INVENTORY_ITEM_POSITIONS, inv_positions)

    eq_items_tag = SaveDataTags.EQUIPMENT_ITEMS
    eq_pos_tag = SaveDataTags.EQUIPMENT_ITEM_POSITIONS
    eq_items, eq_positions = _load_items_from_json(json_blob, eq_items_tag, eq_pos_tag)

    ret.set(SaveDataTags.EQUIPMENT_ITEMS, eq_items)
    ret.set(SaveDataTags.EQUIPMENT_ITEM_POSITIONS, eq_positions)

    invalid_tags = ret._get_invalid_tags()
    if len(invalid_tags) > 0:
        pretty_string = ", ".join([invalid_tags[t] for t in invalid_tags])
        raise ValueError("Invalid tags in {}: {}".format(path_to_file, pretty_string))

    return ret


def _load_items_from_json(json_blob, items_tag, positions_tag):
    """
        returns: list of items, list of (x, y) positions
    """
    json_items = util.Utils.read_safely(json_blob, items_tag, [])
    json_positions = util.Utils.read_safely(json_blob, positions_tag, [])

    if len(json_items) != len(json_positions):
        print("ERROR: malformed json, item list and position list have different lengths: " +
              "{} has length {}, and {} has length {}".format(
                items_tag, len(json_items), positions_tag, len(json_positions)))
        return [], []

    res_items = []
    res_positions = []
    for i in range(0, len(json_items)):
        try:
            json_pos = json_positions[i]
            json_item = json_items[i]

            raw_pos = (int(json_pos[0]), int(json_pos[1]))
            raw_item = itemencoder.json_to_item(json_item)

            res_positions.append(raw_pos)
            res_items.append(raw_item)
        except Exception:
            print("ERROR: failed to deserialize item at list index, skipping it: {}".format(i))
            traceback.print_exc()

    return res_items, res_positions


def write_to_disk(save_blob):
    cur_version = version.get_version()
    blob_version = save_blob.get(SaveDataTags.VERSION_NUM)
    if blob_version is None or len(blob_version) != 4:
        save_blob.set(SaveDataTags.VERSION_NUM, cur_version)
    elif blob_version[3] == "DEV" or blob_version[3] == "MOD":
        # if you ever played it in a non-standard mode, forever blemish the save file
        save_blob.set(SaveDataTags.VERSION_NUM, (cur_version[0], cur_version[1], cur_version[2], blob_version[3]))
    else:
        save_blob.set(SaveDataTags.VERSION_NUM, cur_version)

    cur_time = int(datetime.datetime.now().timestamp())
    save_blob.set(SaveDataTags.LAST_MODIFIED_TIME, cur_time)

    save_blob.set(SaveDataTags.CHECKSUM, -1)

    invalid_tags = save_blob._get_invalid_tags()
    if len(invalid_tags) > 0:
        pretty_string = ", ".join([invalid_tags[t] for t in invalid_tags])
        print("ERROR: invalid tags, not saving: {}".format(pretty_string))
        return False

    json_blob = {}

    for t in _all_tags:
        if not SaveDataTags.is_item_tag(t):
            json_blob[t] = save_blob.get(t)  # these are just basic datatypes

    item_tag_pairs = [(SaveDataTags.INVENTORY_ITEMS, SaveDataTags.INVENTORY_ITEM_POSITIONS),
                      (SaveDataTags.EQUIPMENT_ITEMS, SaveDataTags.EQUIPMENT_ITEM_POSITIONS)]

    for pair in item_tag_pairs:
        item_list_tag, position_list_tag = pair
        item_list = save_blob.get(item_list_tag)
        position_list = save_blob.get(position_list_tag)

        json_blob[item_list_tag] = []
        json_blob[position_list_tag] = []

        for i in range(0, len(item_list)):
            json_item = None
            raw_item = item_list[i]
            pos = [position_list[i][0], position_list[i][1]]

            try:
                json_item = itemencoder.item_to_json(raw_item)

            except Exception:
                traceback.print_exc()

            if json_item is None:
                print("ERROR: failed to serialize item: {}".format(raw_item))
            else:
                json_blob[item_list_tag].append(json_item)
                json_blob[position_list_tag].append(pos)

    if save_blob.filepath is None:
        save_blob.filepath = make_new_filepath()

    json_blob[SaveDataTags.CHECKSUM] = _MOCK_CHECKSUM
    real_checksum = util.Utils.checksum(json_blob, m=_CHECKSUM_MOD)

    json_blob[SaveDataTags.CHECKSUM] = real_checksum

    try:
        # here goes nothing...
        util.Utils.save_json_to_path(json_blob, save_blob.filepath)
    except Exception:
        print("ERROR: failed to write game data to file: {}".format(save_blob.filepath))
        traceback.print_exc()
        return False

    print("INFO: successfully saved game data to {}".format(save_blob.filepath))
    return True


def delete_from_disk(save_blob):
    the_filepath = save_blob.filepath
    if the_filepath is not None:
        try:
            os.remove(str(the_filepath))
            return True
        except OSError:
            print("ERROR: failed to delete save file: {}".format(the_filepath))
            traceback.print_exc()
            return False


class SaveDataTags:

    # string: the unique identifier for the run, used to allow / prohibit overwrites
    GAME_UID = util.Utils.add_to_list_and_return("game_uid", _all_tags)

    # [int, int, int, string]: version the file was saved in, used for bridging
    VERSION_NUM = util.Utils.add_to_list_and_return("version_num", _all_tags)

    # integer: time (in seconds since epoch) that this file was last saved
    LAST_MODIFIED_TIME = util.Utils.add_to_list_and_return("last_modified_time", _all_tags)

    # integer: number of ticks that have elapsed in the run so far
    ELAPSED_TIME = util.Utils.add_to_list_and_return("elapsed_time", _all_tags)

    # integer: kill count of the run so far
    KILL_COUNT = util.Utils.add_to_list_and_return("kill_count", _all_tags)

    # integer: turn count of the run so far
    TURN_COUNT = util.Utils.add_to_list_and_return("turn_count", _all_tags)

    # integer: death count of the run so far
    DEATH_COUNT = util.Utils.add_to_list_and_return("death_count", _all_tags)

    # integer: number of checkpoints you activated
    CHECKPOINT_COUNT = util.Utils.add_to_list_and_return("checkpoint_count", _all_tags)

    # items in the player's possession. note that the "held" item is never saved / loaded
    INVENTORY_ITEMS = util.Utils.add_to_list_and_return("inventory_items", _all_tags)
    INVENTORY_ITEM_POSITIONS = util.Utils.add_to_list_and_return("inventory_item_positions", _all_tags)
    EQUIPMENT_ITEMS = util.Utils.add_to_list_and_return("equipment_items", _all_tags)
    EQUIPMENT_ITEM_POSITIONS = util.Utils.add_to_list_and_return("equipment_item_positions", _all_tags)

    # string: the save location's identifier
    SPAWN_ID = util.Utils.add_to_list_and_return("save_location_id", _all_tags)

    # integer: checksum of the (other) contents of the file
    CHECKSUM = util.Utils.add_to_list_and_return("checksum", _all_tags)

    @staticmethod
    def is_item_tag(tag):
        return tag in (SaveDataTags.INVENTORY_ITEMS, SaveDataTags.INVENTORY_ITEM_POSITIONS,
                       SaveDataTags.EQUIPMENT_ITEMS, SaveDataTags.EQUIPMENT_ITEM_POSITIONS)

    @staticmethod
    def is_integer_tag(tag):
        return tag in (SaveDataTags.LAST_MODIFIED_TIME, SaveDataTags.ELAPSED_TIME, SaveDataTags.KILL_COUNT,
                       SaveDataTags.DEATH_COUNT, SaveDataTags.TURN_COUNT, SaveDataTags.CHECKPOINT_COUNT, SaveDataTags.CHECKSUM)

    @staticmethod
    def is_string_tag(tag):
        return tag in (SaveDataTags.GAME_UID, SaveDataTags.SPAWN_ID)


class SaveDataBlob:

    # item storage locations
    INVENTORY = 0
    EQUIPMENT = 1

    def __init__(self, filepath=None):
        self.filepath = filepath
        self.tags = {}
        for t in _all_tags:
            if SaveDataTags.is_item_tag(t):
                self.tags[t] = []
            else:
                self.tags[t] = None

    def get(self, tag):
        return self.tags[tag]

    def set(self, tag, value):
        if value is None:
            if SaveDataTags.is_item_tag(tag):
                raise ValueError("list-type item tag cannot be set to None")
            else:
                self.tags[tag] = None
                return

        if SaveDataTags.is_integer_tag(tag) and not isinstance(value, int):
            raise ValueError("unexpected value for integer tag \"{}\": {}".format(tag, value))

        if tag == SaveDataTags.VERSION_NUM:
            if not isinstance(value, (tuple, list)):  # c(._.)o  monkey of disapproval
                raise ValueError("unexpected data type for version tag \"{}\": {}".format(tag, value))

            if len(value) != 4 or not (isinstance(value[0], int) and isinstance(value[1], int)
                                       and isinstance(value[2], int) and isinstance(value[3], str)):
                raise ValueError("unexpected value for version tag \"{}\": {}".format(tag, value))

        if SaveDataTags.is_string_tag(tag) and not isinstance(value, str):
            raise ValueError("unexpected value for string tag \"{}\": {}".format(tag, value))

        if SaveDataTags.is_item_tag(tag) and not isinstance(value, list):
            raise ValueError("unexpected value for list-type tag {}: {}".format(tag, value))

        if tag not in self.tags:
            raise ValueError("unrecognized tag: {}".format(tag))

        self.tags[tag] = value

    def is_completed(self):
        """Whether the save file has been won (thus making it a high score file)."""
        return self.get(SaveDataTags.SPAWN_ID) == WIN_SAVE_ID

    def has_standard_version(self):
        my_version = self.get(SaveDataTags.VERSION_NUM)
        if my_version is None or len(my_version) != 4:
            return False
        else:
            desc = my_version[3]
            return desc != "DEV" and desc != "MOD"

    def get_pretty_save_id_name(self):
        save_id = self.get(SaveDataTags.SPAWN_ID)

        if self.is_completed():
            return "Win"

        zone_name = None
        if save_id is not None:
            import src.worldgen.zones as zones
            zone_id = zones.get_zone_id_for_save_id(save_id)
            if zone_id is not None:
                zone_name = zones.get_zone(zone_id).get_name()

        if zone_name is None:
            return "UNKNOWN[{}={}]".format(SaveDataTags.SPAWN_ID, save_id)
        else:
            return zone_name

    def get_pretty_elapsed_time(self, show_hours_if_zero=False):
        elapsed_time = self.get(SaveDataTags.ELAPSED_TIME)
        if elapsed_time is None:
            return "???"
        elif elapsed_time >= 216000000:  # you will NOT break my UI
            return "999:59:59"
        else:
            return util.Utils.ticks_to_time_string(elapsed_time, show_hours_if_zero=show_hours_if_zero, fps=60)

    def get_pretty_last_modified_date(self):
        save_time = self.get(SaveDataTags.LAST_MODIFIED_TIME)
        if save_time is None:
            return "?-?-20??"
        else:
            save_time_str = datetime.datetime.fromtimestamp(save_time).strftime("%m-%d-%Y")
            if len(save_time_str) > 10:  # remember to increase this in 10,000 C.E.
                return save_time_str[0:7] + "..."
            return save_time_str

    def get_pretty_string(self, include_elapsed_time=True, include_version_desc=True, max_length=-1):
        if 0 < max_length <= 3:
            max_length = 4

        zone_name = self.get_pretty_save_id_name()
        time_part = "" if not include_elapsed_time else " ({})".format(self.get_pretty_elapsed_time())

        version_part = ""
        if include_version_desc:
            vers = self.get(SaveDataTags.VERSION_NUM)
            if vers is not None and (vers[3] == "DEV" or vers[3] == "MOD"):
                version_part = " ({})".format(vers[3])

        if len(zone_name) > 0 and 0 < max_length < len(zone_name) + len(time_part) + len(version_part):
            new_zone_name_length = max(1, max_length - len(time_part) - len(version_part) - 3)
            zone_name = zone_name[0:new_zone_name_length] + "..."

        res = zone_name + time_part + version_part

        if 0 < max_length < len(res):
            return res[0:max_length - 3] + "..."

        return res

    def _get_invalid_tags(self):
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
        if self.tags[t] != WIN_SAVE_ID:
            save_zone = zones.get_zone_id_for_save_id(self.tags[t])
            if save_zone is None:
                res[t] = "{} isn't recognized: {}".format(t, self.tags[t])

        return res

    def get_last_modified_time_for_sorting(self):
        res = self.get(SaveDataTags.LAST_MODIFIED_TIME)
        if res is None or not isinstance(res, int):
            return 0
        else:
            return res

    def get_elapsed_time_for_sorting(self):
        res = self.get(SaveDataTags.ELAPSED_TIME)
        if res is None or not isinstance(res, int) or res < 0:
            return float('inf')
        else:
            return res

