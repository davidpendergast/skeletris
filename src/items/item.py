import random
import uuid

from src.game.stats import StatTypes, StatProvider
from src.utils.util import Utils
import src.renderengine.img as img
from src.items.cubeutils import CubeUtils
import src.game.spriteref as spriteref
import src.utils.colors as colors
import src.game.balance as balance


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
    CUBES = "_Cubes"  # the "_" means it won't be shown in tooltips
    WEAPON = "Weapon"
    CONSUMABLE = "Consumable"
    STORY = "Quest Item"
    THROWABLE = "Throwable"


class ItemType:

    def __init__(self, name, tags, min_level=0, max_level=float("inf"), drop_rate=1):
        self.name = name
        self.tags = tags
        self.level_range = (min_level, max_level)
        self.drop_rate = drop_rate

    def get_name(self):
        return self.name

    def get_tags(self):
        return self.tags

    def get_drop_rate(self):
        return self.drop_rate

    def has_tag(self, tag):
        return tag in self.tags

    def get_level_range(self):
        return self.level_range

    def __str__(self):
        return self.name


_ALL_TYPES = []


def _new_type(name, tags, min_level=0, max_level=float('inf'), drop_rate=1):
    if not isinstance(tags, tuple):
        raise ValueError("tags needs to be a tuple: {}".format(tags))
    res = ItemType(name, tags, min_level=min_level, max_level=max_level, drop_rate=drop_rate)
    _ALL_TYPES.append(res)
    return res


class ItemTypes:

    @staticmethod
    def all_types(at_level=None, with_tags=()):
        if at_level is None:
            types_at_level = list(_ALL_TYPES)
        else:
            types_at_level = []
            for t in _ALL_TYPES:
                if t.get_level_range()[0] <= at_level <= t.get_level_range()[1]:
                    types_at_level.append(t)

        if len(with_tags) > 0:
            return [t for t in types_at_level if t in with_tags]
        else:
            return types_at_level

    STAT_CUBE_5 = _new_type("Small Artifact", (ItemTags.EQUIPMENT, ItemTags.CUBES),
                            drop_rate=balance.STAT_CUBE_5_DROP_RATE)
    STAT_CUBE_6 = _new_type("Medium Artifact", (ItemTags.EQUIPMENT, ItemTags.CUBES), min_level=1,
                            drop_rate=balance.STAT_CUBE_6_DROP_RATE)
    STAT_CUBE_7 = _new_type("Large Artifact", (ItemTags.EQUIPMENT, ItemTags.CUBES), min_level=2,
                            drop_rate=balance.STAT_CUBE_7_DROP_RATE)

    SWORD_WEAPON = _new_type("Sword", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=3,
                             drop_rate=balance.WEAPON_DROP_RATE)
    SHIELD_WEAPON = _new_type("Shield", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=5,
                              drop_rate=balance.WEAPON_DROP_RATE)
    SPEAR_WEAPON = _new_type("Spear", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=7,
                             drop_rate=balance.WEAPON_DROP_RATE)
    WHIP_WEAPON = _new_type("Whip", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=5,
                            drop_rate=balance.WEAPON_DROP_RATE)
    DAGGER_WEAPON = _new_type("Dagger", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=1,
                              drop_rate=balance.WEAPON_DROP_RATE)
    AXE_WEAPON = _new_type("Axe", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=9,
                           drop_rate=balance.WEAPON_DROP_RATE)
    BOW_WEAPON = _new_type("Bow", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=9,
                           drop_rate=balance.WEAPON_DROP_RATE)
    WAND_WEAPON = _new_type("Wand", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=7,
                            drop_rate=balance.WEAPON_DROP_RATE)

    POTION = _new_type("Potion", tuple([ItemTags.CONSUMABLE, ItemTags.THROWABLE]),
                       drop_rate=balance.POTION_DROP_RATE)


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

    def get_color(self):
        return self.color

    def get_title_color(self):
        return self.title_color

    def sprite_rotation(self):
        return 0

    def can_equip(self):
        return self.get_type().has_tag(ItemTags.EQUIPMENT)

    def can_rotate(self):
        return self._can_rotate

    def get_consume_effect(self):
        """returns: the status that's applied when the item is consumed or thrown."""
        return self.consume_effect

    def can_consume(self):
        return self.get_type().has_tag(ItemTags.CONSUMABLE)

    def can_throw(self):
        return self.get_type().has_tag(ItemTags.THROWABLE)

    def get_projectile_sprite(self):
        """returns: the projectile sprite this item should use for its attack animations."""
        return None

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
                 uuid_str=None, can_rotate=True, color=(1, 1, 1), title_color=(1, 1, 1), actions=None, consume_effect=None,
                 projectile_sprite=None):

        Item.__init__(self, name, item_type, level, cubes, stats, color=color, uuid_str=uuid_str,
                      can_rotate=can_rotate, title_color=title_color, actions=actions, consume_effect=consume_effect)

        self._small_sprite = small_sprite
        self._big_sprite = big_sprite
        self._projectile_sprite = projectile_sprite
        self._sprite_rotation = sprite_rotation

    def big_sprite(self):
        return self._big_sprite

    def get_entity_sprite(self):
        return self._small_sprite

    def get_projectile_sprite(self):
        return self._projectile_sprite

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
                              consume_effect=self.consume_effect, projectile_sprite=self._projectile_sprite)


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
        return "lvl:{}".format(self.level + 1)

    def rotate(self):
        new_cubes = []
        new_art = {}
        rotation_mapping = CubeUtils.calc_rotation_mapping(self.cubes)
        for cube in self.cubes:
            new_cube = rotation_mapping[cube]
            new_cubes.append(new_cube)
            if cube in self.cube_art:
                new_art[new_cube] = self.cube_art[cube]

        new_cubes = CubeUtils.sort_cubes(new_cubes)

        return StatCubesItem(self.name, self.level, self.stats, new_cubes,
                             self.color, cube_art=new_art, uuid_str=self.uuid)

    def mirror(self):
        new_cubes = []
        new_art = {}
        mirror_mapping = CubeUtils.calc_mirror_mapping(self.cubes)
        for cube in self.cubes:
            new_cube = mirror_mapping[cube]
            new_cubes.append(new_cube)
            if cube in self.cube_art:
                new_art[new_cube] = self.cube_art[cube]

        new_cubes = CubeUtils.sort_cubes(new_cubes)

        return StatCubesItem(self.name, self.level, self.stats, new_cubes,
                             self.color, cube_art=new_art, uuid_str=self.uuid)

    def reroll_cubes(self):
        import src.items.itemgen as itemgen
        new_cubes = itemgen.StatCubesItemFactory.gen_cubes(len(self.cubes))
        new_art = {}

        artless_cubes = [c for c in new_cubes]
        random.shuffle(artless_cubes)
        for art_c in self.cube_art:
            if len(artless_cubes) > 0:  # shouldn't ever have a mismatch here, but ehh
                new_art[artless_cubes.pop()] = self.cube_art[art_c]

        new_name = itemgen.StatCubesItemFactory.gen_name_for_stats_and_cubes(self.stats, new_cubes)

        return StatCubesItem(new_name, self.level, self.stats, new_cubes,
                             self.color, cube_art=new_art, uuid_str=self.uuid)

    def reroll_art(self):
        import src.items.itemgen as itemgen
        new_color = itemgen.StatCubesItemFactory.gen_color_for_stats(self.stats)
        new_art = itemgen.StatCubesItemFactory.gen_cube_art_for_stats_and_cubes(self.stats, self.cubes)

        return StatCubesItem(self.name, self.level, self.stats, self.cubes,
                             new_color, cube_art=new_art, uuid_str=self.uuid)

    def reroll_stats(self):
        import src.items.itemgen as itemgen
        new_stats = itemgen.StatCubesItemFactory.gen_stats_for_cubes(self.level, self.cubes)
        new_name = itemgen.StatCubesItemFactory.gen_name_for_stats_and_cubes(new_stats, self.cubes)
        new_color = itemgen.StatCubesItemFactory.gen_color_for_stats(new_stats)
        new_art = itemgen.StatCubesItemFactory.gen_cube_art_for_stats_and_cubes(new_stats, self.cubes)

        return StatCubesItem(new_name, self.level, new_stats, self.cubes,
                             new_color, cube_art=new_art, uuid_str=self.uuid)

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

