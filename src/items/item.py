import random
import uuid

from src.game.stats import StatTypes, StatProvider
from src.utils.util import Utils
import src.renderengine.img as img
from src.items.cubeutils import CubeUtils
import src.game.spriteref as spriteref
import src.utils.colors as colors


ITEM_CORE_NAME = {
    (): "Vessel",
    tuple([StatTypes.ATT]): "Cube",
    tuple([StatTypes.DEF]): "Tetra",
    tuple([StatTypes.VIT]): "Quad",
    (StatTypes.ATT, StatTypes.ATT): "Cubes",
    (StatTypes.ATT, StatTypes.DEF): "Cuboid",
    (StatTypes.ATT, StatTypes.VIT): "Cubit",
    (StatTypes.DEF, StatTypes.ATT): "Tetrit",
    (StatTypes.DEF, StatTypes.DEF): "Tetras",
    (StatTypes.DEF, StatTypes.VIT): "Tetrit",
    (StatTypes.VIT, StatTypes.ATT): "Quadcube",
    (StatTypes.VIT, StatTypes.DEF): "Quadroid",
    (StatTypes.VIT, StatTypes.VIT): "Quads"
}


class AppliedStat:

    """A stat with a value, generally "applied" to something like an item."""
    def __init__(self, stat_type, value, local=False):
        self.stat_type = stat_type
        self.value = value
        self.local = local

    def __repr__(self):
        res = self.stat_type.get_description(self.value, local=self.local)
        if "+-" in res:
            # kinda wonky to handle negative values like this but it should work
            return res.replace("+-", "-")
        else:
            return res

    def __eq__(self, other):
        try:
            return (self.stat_type == other.stat_type and
                    self.value == other.value and
                    self.local == other.local)
        except ValueError:
            return False

    def __hash__(self):
        return hash((self.stat_type, self.value, self.local))
            
    def color(self):
        return self.stat_type.get_color()

    def is_hidden(self):
        return self.stat_type.is_hidden(local=self.local)

    def is_local(self):
        return self.local

    def get_type(self):
        return self.stat_type

    def get_value(self):
        return self.value

    def to_json(self):
        return [self.stat_type, self.value]

    @staticmethod
    def from_json(blob):
        pass


class ItemTags:
    EQUIPMENT = "Equipment"
    WEAPON = "Weapon"
    CONSUMABLE = "Consumable"
    STORY = "Quest Item"
    THROWABLE = "Throwable"


class ItemType:

    def __init__(self, name, tags, min_level=0, max_level=float("inf")):
        self.name = name
        self.tags = tags
        self.level_range = (min_level, max_level)

    def get_name(self):
        return self.name

    def get_tags(self):
        return self.tags

    def has_tag(self, tag):
        return tag in self.tags

    def get_level_range(self):
        return self.level_range

    def __str__(self):
        return self.name


_ALL_TYPES = []


def _new_type(name, tags, min_level=0, max_level=float('inf')):
    if not isinstance(tags, tuple):
        raise ValueError("tags needs to be a tuple: {}".format(tags))
    res = ItemType(name, tags, min_level=min_level, max_level=max_level)
    _ALL_TYPES.append(res)
    return res


class ItemTypes:

    @staticmethod
    def all_types(at_level=None):
        if at_level is None:
            return list(_ALL_TYPES)
        else:
            res = []
            for t in _ALL_TYPES:
                if t.get_level_range()[0] <= at_level <= t.get_level_range()[1]:
                    res.append(t)
            return res

    STAT_CUBE_5 = _new_type("Small Trinket", tuple([ItemTags.EQUIPMENT]))
    STAT_CUBE_6 = _new_type("Medium Relic", tuple([ItemTags.EQUIPMENT]), min_level=7)
    STAT_CUBE_7 = _new_type("Large Artifact", tuple([ItemTags.EQUIPMENT]), min_level=5),

    SWORD_WEAPON = _new_type("Sword", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=3)
    SHIELD_WEAPON = _new_type("Shield", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=5)
    SPEAR_WEAPON = _new_type("Spear", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=7)
    WHIP_WEAPON = _new_type("Whip", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=5)
    DAGGER_WEAPON = _new_type("Dagger", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE))
    AXE_WEAPON = _new_type("Axe", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=9)
    BOW_WEAPON = _new_type("Bow", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=9)
    WAND_WEAPON = _new_type("Wand", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=7)

    POTION = _new_type("Potion", tuple([ItemTags.CONSUMABLE, ItemTags.THROWABLE]))


class Item(StatProvider):

    def __init__(self, name, item_type, level, cubes, stats, actions=None, consume_effect=None, color=(1, 1, 1),
                 uuid_str=None, can_rotate=True, title_color=(1, 1, 1)):
        self.name = name
        self.level = level
        self.item_type = item_type
        self.item_actions = tuple() if actions is None else tuple(actions)
        self.stats = tuple(stats)
        self.cubes = tuple(CubeUtils.clean_cubes(cubes))
        self.color = color
        self.uuid = uuid_str if uuid_str is not None else str(uuid.uuid4())
        self._can_rotate = can_rotate
        self.title_color = title_color
        self.consume_effect = consume_effect

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.uuid == other.uuid
        else:
            return False

    def __hash__(self):
        return hash(self.uuid)

    def get_title(self):
        return self.name

    def get_type(self):
        return self.item_type

    def get_level(self):
        return self.level

    def get_title_color(self):
        return self.title_color

    def sprite_rotation(self):
        return 0

    def can_equip(self):
        return False

    def can_rotate(self):
        return self._can_rotate

    def get_consume_effect(self):
        """returns: the status that's applied when the item is consumed or thrown."""
        return self.consume_effect

    def can_consume(self):
        return self.get_type().has_tag(ItemTags.CONSUMABLE)

    def can_throw(self):
        return self.get_type().has_tag(ItemTags.THROWABLE)

    def rotate(self):
        return self

    def w(self):
        return max([c[0] for c in self.cubes]) + 1

    def h(self):
        return max([c[1] for c in self.cubes]) + 1

    def stat_value(self, stat_type, local=False):
        res = 0
        for stat in self.all_applied_stats():
            if stat.stat_type == stat_type and stat.local == local:
                res += stat.value
        return res

    def all_applied_stats(self):
        return self.stats

    def all_actions(self):
        return self.item_actions

    def get_small_img(self, scale, layer_id, input_img=None):
        pass

    def get_big_img(self, scale, layer_id, input_img=None):
        pass

    def get_entity_sprite(self):
        return spriteref.Items.misc_small


class SpriteItem(Item):

    def __init__(self, name, item_type, level, cubes, stats, small_sprite, big_sprite, sprite_rotation=0,
                 uuid_str=None, can_rotate=True, color=(1, 1, 1), title_color=(1, 1, 1), actions=None, consume_effect=None):

        Item.__init__(self, name, item_type, level, cubes, stats, color=color, uuid_str=uuid_str,
                      can_rotate=can_rotate, title_color=title_color, actions=actions, consume_effect=consume_effect)

        self._small_sprite = small_sprite
        self._big_sprite = big_sprite
        self._sprite_rotation = sprite_rotation

    def big_sprite(self):
        return self._big_sprite

    def get_entity_sprite(self):
        return self._small_sprite

    def sprite_rotation(self):
        return self._sprite_rotation

    def get_big_img(self, scale, layer_id, input_img=None):
        if input_img is None:
            input_img = img.ImageBundle.new_bundle(layer_id, scale=scale)
        input_img.update(new_model=self.big_sprite())
        return input_img

    def rotate(self):
        if not self.can_rotate():
            return self
        else:
            new_cubes = CubeUtils.rotate_cubes(self.cubes)
            new_rotation = (self.sprite_rotation() + 1) % 4

            return SpriteItem(self.name, self.get_type(), self.get_level(), new_cubes, self.stats, self._small_sprite,
                              self._big_sprite, sprite_rotation=new_rotation, uuid_str=self.uuid, color=self.color,
                              can_rotate=self._can_rotate, title_color=self.title_color, actions=self.item_actions,
                              consume_effect=self.consume_effect)


class StatCubesItem(Item):

    def __init__(self, name, level, stats, cubes, color, cube_art=None, uuid_str=None):
        """
            name: str
            level: int: 0 to 255
            stats: ordered list of Stat objects
            cubes: list of (int: x, int: y)
            color: tuple (float, float, float)
            cube_art: dict of (x, y) -> int: art_id
            uuid_str: str
        """
        if len(cubes) <= 5:
            item_type = ItemTypes.STAT_CUBE_5
        elif len(cubes) == 6:
            item_type = ItemTypes.STAT_CUBE_6
        else:
            item_type = ItemTypes.STAT_CUBE_7

        Item.__init__(self, name, item_type, level, cubes, stats, color=color, uuid_str=uuid_str,
                      can_rotate=True, title_color=(1, 1, 1))
        self.cube_art = {} if cube_art is None else cube_art
    
    def level_string(self):
        return "lvl:{}".format(self.level)

    def can_equip(self):
        return True

    def rotate(self):
        new_cubes = CubeUtils.rotate_cubes(self.cubes)
        return StatCubesItem(self.name, self.level, self.stats,
                             new_cubes, self.color, cube_art=self.cube_art, uuid_str=self.uuid)
        
    def __str__(self):
        res = "[{}]".format(self.name)
        res += "\n  " + self.uuid
        res += "\n  " + self.level_string()
        for stat in self.stats:
            res += "\n  " + str(stat)
        res += "\n"
        for y in range(0, 5):
            res += "\n  "
            for x in range(0, 5):
                if (x, y) in self.cubes:
                    res += "X "
                else:
                    res += "- "    
        res += "\n[" + "_"*len(self.name) + "]"
        return res

    def get_entity_sprite(self):
        return spriteref.get_item_entity_sprite(self.cubes)

    def to_json(self):
        blob = {
            "name": self.name,
            "level": self.level,
            "cubes": self.cubes,
            "color": self.color,
            "cube_art": [],
            "stats": [],
            "uuid": self.uuid
        }

        for xy in self.cube_art:
            blob["cube_art"].append((xy[0], xy[1], self.cube_art[xy]))

        for stat in self.stats:
            as_json = stat.to_json()
            blob["stats"].append(as_json)

        return blob

    @staticmethod
    def from_json(blob):
        name = str(blob["name"])
        level = int(blob["level"])

        cubes = []
        for cube_blob in blob["cubes"]:
            c_x = int(cube_blob[0])
            c_y = int(cube_blob[1])
            cubes.append((c_x, c_y))

        color_r = float(blob["color"][0])
        color_g = float(blob["color"][1])
        color_b = float(blob["color"][2])
        color = (color_r, color_g, color_b)

        cube_art = {}
        for cube_art_blob in blob["cube_art"]:
            x = int(cube_art_blob[0])
            y = int(cube_art_blob[1])
            art_id = int(cube_art_blob[2])
            cube_art[(x, y)] = art_id

        stats = []
        for stat_blob in blob["stats"]:
            stat = AppliedStat.from_json(stat_blob)
            stats.append(stat)

        uuid_str = str(blob["uuid"])

        return StatCubesItem(name, level, stats, cubes, color, cube_art=cube_art, uuid_str=uuid_str)

    def test_equals(self, other):
        try:
            return (
                self.name == other.name and
                self.level == other.level and
                self.stats == other.stats and
                self.color == other.color and
                self.cubes == other.cubes and
                self.cube_art == other.cube_art and
                self.uuid == other.uuid
            )
        except ValueError:
            return False

    def __eq__(self, other):
        try:
            return self.uuid == other.uuid
        except ValueError:
            return False

    def __hash__(self):
        return hash(self.uuid)

