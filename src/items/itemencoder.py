
import src.items.item as item
import src.items.itemgen as itemgen


# universal item attributes
TYPE_KEY = "item_type"      # str
CUBES_KEY = "cubes"         # list of (int, int)
LEVEL_KEY = "level"         # int
UID_KEY = "uid"             # str
STATS_KEY = "stats"         # list of (str, int, bool)

# specific to stat cube items
NAME_KEY = "name"           # str
COLOR_KEY = "color"         # (int, int, int)
CUBES_ART_KEY = "cube_art"  # dict (int, int) -> int

# specific to sprite items
ROTATION_KEY = "rotation"   # int equal to 0, 1, 2, or 3


def item_to_json(the_item):
    json_blob = {}
    json_blob[TYPE_KEY] = str(the_item.get_type().get_id())
    json_blob[CUBES_KEY] = list(the_item.get_cubes())
    json_blob[LEVEL_KEY] = int(the_item.get_level())
    json_blob[UID_KEY] = str(the_item.get_uid())
    json_blob[STATS_KEY] = _stats_to_json(the_item.all_applied_stats())

    if isinstance(the_item, item.StatCubesItem):
        _add_stat_cube_item_attributes_to_json(json_blob, the_item)
    elif isinstance(the_item, item.SpriteItem):
        _add_sprite_item_attributes_to_json(json_blob, the_item)
    else:
        raise ValueError("unrecognized item type: {}".format(the_item))

    return json_blob


def json_to_item(json_blob, strict=False):
    pass


def _add_stat_cube_item_attributes_to_json(json_blob, the_item):
    json_blob[NAME_KEY] = str(the_item.get_title())
    json_blob[COLOR_KEY] = _color_to_json(the_item.get_color())
    json_blob[CUBES_ART_KEY] = dict(the_item.get_cube_art())


def _add_sprite_item_attributes_to_json(json_blob, the_item):
    json_blob[ROTATION_KEY] = int(the_item.sprite_rotation())


def _color_to_json(float_color):
    r = int(min(255, max(0, 255 * float_color[0])))
    g = int(min(255, max(0, 255 * float_color[1])))
    b = int(min(255, max(0, 255 * float_color[2])))
    return [r, g, b]


def _json_to_color(int_color):
    r = min(1, max(0, int_color[0] / 255))
    g = min(1, max(0, int_color[1] / 255))
    b = min(1, max(0, int_color[2] / 255))
    return (r, g, b)


def _stats_to_json(applied_stats_list):
    res = []
    for stat in applied_stats_list:
        stat_id = stat.get_type().get_id()
        stat_value = stat.get_value()
        stat_is_local = stat.is_local()

        if not isinstance(stat_id, str) or not isinstance(stat_value, int) or not isinstance(stat_is_local, bool):
            raise ValueError("failed to serialize stat: {}".format(stat))

        res.append((stat_id, stat_value, stat_is_local))
    return res


def _json_to_stats(list_blob, strict=False):
    res = []
    for tup in list_blob:
        stat_id = str(tup[0])
        stat_value = int(tup[1])
        stat_is_local = bool(tup[2])

        stat_type = item.StatTypes.get_type_for_id(stat_id)
        if stat_type is None:
            if strict:
                raise ValueError("unrecognized stat id: {}".format(stat_id))
            else:
                print("WARN: unrecognized stat id, skipping: {}".format(stat_id))
        else:
            res.append(item.AppliedStat(stat_type, stat_value, local=stat_is_local))
    return res


if __name__ == "__main__":
    import random

    n = 100
    for i in range(0, n):
        item_level = int(16 * random.random())
        rand_item = itemgen.ItemFactory.gen_item(item_level)

        as_json = item_to_json(rand_item)
        print("made item: {}".format(as_json))

