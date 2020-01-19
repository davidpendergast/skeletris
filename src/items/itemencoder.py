
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
CUBE_ART_KEY = "cube_art"   # list of (int, int, int)

# specific to sprite items
ROTATION_KEY = "rotation"   # int equal to 0, 1, 2, or 3
SUBTYPE_KEY = "subtype"     # str


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


def json_to_item(json_blob):
    item_id_in_json = str(_get_json_attribute(json_blob, TYPE_KEY, fail_if_missing=True))
    stats_in_json = _get_json_attribute(json_blob, STATS_KEY, fail_if_missing=True)
    cubes_in_json = _get_json_attribute(json_blob, CUBES_KEY, assert_type=list, fail_if_missing=True)

    item_type = item.ItemTypes.get_type_for_id(item_id_in_json)
    if item_type is None:
        raise ValueError("unrecognized {}: {}".format(TYPE_KEY, item_id_in_json))

    item_cubes = []
    for json_cube in cubes_in_json:
        item_cubes.append((int(json_cube[0]), int(json_cube[1])))

    item_level = _get_json_attribute(json_blob, LEVEL_KEY, assert_type=int, fail_if_missing=True)
    item_uid = _get_json_attribute(json_blob, UID_KEY, assert_type=str, fail_if_missing=True)

    item_stats = _json_to_stats(stats_in_json, strict=True)

    if item_type.has_tag(item.ItemTags.CUBES):
        # stat cube item
        color_in_json = _get_json_attribute(json_blob, COLOR_KEY, assert_type=list, fail_if_missing=True)
        cube_art_in_json = _get_json_attribute(json_blob, CUBE_ART_KEY, assert_type=list, fail_if_missing=True)

        item_name = _get_json_attribute(json_blob, NAME_KEY, assert_type=str, fail_if_missing=True)
        item_color = _json_to_color(color_in_json)
        item_cube_art = _json_to_cube_art(cube_art_in_json)

        return build_stat_cubes_item(item_type, item_cubes, item_level, item_uid, item_stats,
                                     item_name, item_color, item_cube_art)
    else:
        # it's a sprite item
        item_rotation = _get_json_attribute(json_blob, ROTATION_KEY, assert_type=int, fail_if_missing=True)
        item_subtype = _get_json_attribute(json_blob, SUBTYPE_KEY, assert_type=str, fail_if_missing=True)

        return build_sprite_item(item_type, item_subtype, item_level, item_uid, item_rotation)


def _get_json_attribute(json_blob, key, assert_type=None, allow_none=False, fail_if_missing=False, or_else=None):
    if key in json_blob:
        val = json_blob[key]

        if val is None:
            if allow_none:
                return None
            else:
                raise ValueError("attribute {} has illegal value: {}".format(key, None))
        elif assert_type is not None and not isinstance(val, assert_type):
            raise ValueError("attribute {} should have type {}, but instead got: {}".format(key, assert_type, val))

        return val

    if fail_if_missing:
        raise ValueError("missing attribute: {}".format(key))
    else:
        return or_else


def _add_stat_cube_item_attributes_to_json(json_blob, the_item):
    json_blob[NAME_KEY] = str(the_item.get_title())
    json_blob[COLOR_KEY] = _color_to_json(the_item.get_color())
    json_blob[CUBE_ART_KEY] = _cube_art_to_json(the_item.get_cube_art())


def _add_sprite_item_attributes_to_json(json_blob, the_item):
    json_blob[ROTATION_KEY] = int(the_item.sprite_rotation())
    json_blob[SUBTYPE_KEY] = str(the_item.get_subtype_id())


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


def _cube_art_to_json(cube_art):
    res = []  # list of (cube_x, cube_y, art_id)
    for cube_xy in cube_art:
        art_id = cube_art[cube_xy]
        res.append((cube_xy[0], cube_xy[1], art_id))
    return res


def _json_to_cube_art(json_art_list):
    res = {}  # (int, int) -> int
    for val in json_art_list:
        cube_pos = (int(val[0]), int(val[1]))
        art_id = int(val[2])
        res[cube_pos] = art_id
    return res


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


def build_stat_cubes_item(item_type, cubes, level, uid, stats, name, color, cube_art):
    if item_type == item.ItemTypes.STAT_CUBE_5:
        if len(cubes) != 5:
            raise ValueError("item with type {} must have 5 cubes, instead got: {}".format(item_type, cubes))
    elif item_type == item.ItemTypes.STAT_CUBE_6:
        if len(cubes) != 6:
            raise ValueError("item with type {} must have 6 cubes, instead got: {}".format(item_type, cubes))
    elif item_type == item.ItemTypes.STAT_CUBE_7:
        if len(cubes) != 7:
            raise ValueError("item with type {} must have 7 cubes, instead got: {}".format(item_type, cubes))
    else:
        raise ValueError("not a stat cubes item type: {}".format(item_type))

    return item.StatCubesItem(name, level, stats, cubes, color, cube_art=cube_art, uuid_str=uid)


def build_sprite_item(item_type, subtype, level, uid, rotation):
    if item_type == item.ItemTypes.POTION:
        return build_potion_item(subtype, level, uid)
    elif item_type.has_tag(item.ItemTags.WEAPON):
        return build_weapon_item(item_type, level, uid, rotation)
    else:
        raise ValueError("unrecognized item type: {}".format(item_type))


def build_potion_item(subtype, level, uid):
    potion_template = itemgen.PotionTemplates.get_template_with_id(subtype)
    if potion_template is None:
        raise ValueError("unrecognized potion type: {}".format(subtype))
    else:
        res = itemgen.PotionItemFactory.gen_item(level, template=potion_template)
        if res is None:
            raise ValueError("failed to make potion for template: {}".format(potion_template))
        else:
            res.uuid = uid  # just for good measure
            return res


def build_weapon_item(item_type, level, uid, rotation):
    res = itemgen.WeaponItemFactory.gen_item(level, item_type)
    if res is None:
        raise ValueError("failed to build item for type: {}".format(item_type))
    res.uuid = uid  # just for good measure

    for _ in range(0, 4):
        if res.sprite_rotation() != (rotation % 4):
            res = res.rotate()
        else:
            return res

    raise ValueError("failed to rotate item to rotation: {}".format(rotation))


if __name__ == "__main__":
    import random

    n = 10000
    for i in range(0, n):
        item_level = int(16 * random.random())

        rand_item = itemgen.ItemFactory.gen_item(item_level)
        as_json = item_to_json(rand_item)
        back_to_item = json_to_item(as_json)

        if not rand_item.test_equals(back_to_item):
            print("failed to roundtrip item: {}".format(rand_item))
            print("made json: {}".format(as_json))
            print("converted back to item: {}".format(back_to_item))

