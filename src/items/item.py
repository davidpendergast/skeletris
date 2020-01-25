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
        except Exception:
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


class ItemTags:
    EQUIPMENT = "Equipment"
    CUBES = "_Cubes"  # the "_" means it won't be shown in tooltips
    WEAPON = "Weapon"
    CONSUMABLE = "Consumable"
    STORY = "Quest Item"
    THROWABLE = "Throwable"


class ItemType:

    def __init__(self, name, type_id, tags, min_level=0, max_level=float("inf"), drop_rate=1):
        self.name = name
        self.type_id = type_id
        self.tags = tags
        self.level_range = (min_level, max_level)
        self.drop_rate = drop_rate

    def get_name(self):
        return self.name

    def get_id(self):
        return self.type_id

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


_ALL_TYPES = {}  # type_id -> ItemType


def _new_type(name, type_id, tags, min_level=0, max_level=float('inf'), drop_rate=1):
    if not isinstance(tags, tuple):
        raise ValueError("tags needs to be a tuple: {}".format(tags))
    res = ItemType(name, type_id, tags, min_level=min_level, max_level=max_level, drop_rate=drop_rate)
    _ALL_TYPES[type_id] = res
    return res


class ItemTypes:

    @staticmethod
    def all_types(at_level=None, with_tags=()):
        if at_level is None:
            types_at_level = [_ALL_TYPES[t_id] for t_id in _ALL_TYPES]
        else:
            types_at_level = []
            for t_id in _ALL_TYPES:
                t = _ALL_TYPES[t_id]
                if t.get_level_range()[0] <= at_level <= t.get_level_range()[1]:
                    types_at_level.append(t)

        if len(with_tags) > 0:
            return [t for t in types_at_level if any(t.has_tag(tag) for tag in with_tags)]
        else:
            return types_at_level

    @staticmethod
    def get_type_for_id(type_id):
        if type_id in _ALL_TYPES:
            return _ALL_TYPES[type_id]
        else:
            return None

    STAT_CUBE_5 = _new_type("Small Artifact", "stat_cubes_5", (ItemTags.EQUIPMENT, ItemTags.CUBES),
                            drop_rate=balance.STAT_CUBE_5_DROP_RATE)
    STAT_CUBE_6 = _new_type("Medium Artifact", "stat_cubes_6", (ItemTags.EQUIPMENT, ItemTags.CUBES), min_level=1,
                            drop_rate=balance.STAT_CUBE_6_DROP_RATE)
    STAT_CUBE_7 = _new_type("Large Artifact", "stat_cubes_7", (ItemTags.EQUIPMENT, ItemTags.CUBES), min_level=2,
                            drop_rate=balance.STAT_CUBE_7_DROP_RATE)

    SWORD_WEAPON = _new_type("Sword", "weapon_sword", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=3,
                             drop_rate=balance.WEAPON_DROP_RATE)
    SHIELD_WEAPON = _new_type("Shield", "weapon_shield", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=5,
                              drop_rate=balance.WEAPON_DROP_RATE)
    SPEAR_WEAPON = _new_type("Spear", "weapon_spear", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=7,
                             drop_rate=balance.WEAPON_DROP_RATE)
    WHIP_WEAPON = _new_type("Whip", "weapon_whip", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=5,
                            drop_rate=balance.WEAPON_DROP_RATE)
    DAGGER_WEAPON = _new_type("Dagger", "weapon_dagger", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=1,
                              drop_rate=balance.WEAPON_DROP_RATE)
    AXE_WEAPON = _new_type("Axe", "weapon_axe", (ItemTags.EQUIPMENT, ItemTags.WEAPON, ItemTags.THROWABLE), min_level=9,
                           drop_rate=balance.WEAPON_DROP_RATE)
    BOW_WEAPON = _new_type("Bow", "weapon_bow", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=9,
                           drop_rate=balance.WEAPON_DROP_RATE)
    WAND_WEAPON = _new_type("Wand", "weapon_wand", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=7,
                            drop_rate=balance.WEAPON_DROP_RATE)
    FISHING_ROD_WEAPON = _new_type("Fishing Rod", "weapon_fishing_rod", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=4,
                                   drop_rate=balance.FISHING_ROD_DROP_RATE)
    SLINGSHOT_WEAPON = _new_type("Slingshot", "weapon_slingshot", (ItemTags.EQUIPMENT, ItemTags.WEAPON), min_level=6,
                                 drop_rate=balance.WEAPON_DROP_RATE)

    POTION = _new_type("Potion", "potion", tuple([ItemTags.CONSUMABLE, ItemTags.THROWABLE]),
                       drop_rate=balance.POTION_DROP_RATE)

    # TODO - one day
    #SUMMONING_TOME = _new_type("Summoning Tome", "summon_tome", tuple([ItemTags.CONSUMABLE]),
    #                           drop_rate=balance.SUMMONING_TOME_DROP_RATE)


class Item(StatProvider):

    def __init__(self, name, item_type, level, cubes, stats, actions=None, consume_effect=None, consume_duration=3,
                 color=(1, 1, 1), uuid_str=None, can_rotate=True):
        self.name = name
        self.level = level
        self.item_type = item_type
        self.item_actions = tuple() if actions is None else tuple(actions)
        self.stats = tuple(stats)
        self.cubes = tuple(CubeUtils.clean_cubes(cubes))
        self.color = color
        self.uuid = uuid_str if uuid_str is not None else str(uuid.uuid4())
        self._can_rotate = can_rotate

        self.consume_effect = consume_effect
        self.consume_duration = consume_duration

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

    def get_cubes(self):
        return self.cubes

    def get_uid(self):
        return self.uuid

    def get_level(self):
        return self.level

    def get_color(self):
        return self.color

    def sprite_rotation(self):
        return 0

    def can_equip(self):
        return self.get_type().has_tag(ItemTags.EQUIPMENT)

    def can_rotate(self):
        return self._can_rotate

    def get_consume_effect(self):
        """returns: the status that's applied when the item is consumed or thrown."""
        return self.consume_effect

    def get_consume_duration(self):
        """returns: the duration of the status that's applied when the item is consumed or thrown."""
        return self.consume_duration

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
        """beware - you probably want all_action_providers()"""
        return self.item_actions

    def all_action_providers(self):
        from src.game.gameengine import ItemActionProvider
        return [ItemActionProvider(self, act) for act in self.all_actions()]

    def get_small_img(self, scale, layer_id, input_img=None):
        pass

    def get_big_img(self, scale, layer_id, input_img=None):
        pass

    def get_entity_sprite(self):
        return spriteref.Items.misc_small

    def test_equals(self, other):
        try:
            return (
                self.name == other.name and
                self.level == other.level and
                self.stats == other.stats and
                Utils.mag(Utils.sub(self.color, other.color)) < 0.01 and
                set(self.cubes) == set(other.cubes) and
                self.uuid == other.uuid and
                self.consume_effect == other.consume_effect and
                self.consume_duration == other.consume_duration
            )
        except Exception:
            return False


class SpriteItem(Item):

    def __init__(self, name, item_type, level, cubes, stats, small_sprite, big_sprite, sprite_rotation=0,
                 uuid_str=None, can_rotate=True, color=(1, 1, 1), actions=None,
                 consume_effect=None, consume_duration=3, projectile_sprite=None, subtype_id="basic"):

        Item.__init__(self, name, item_type, level, cubes, stats, color=color, uuid_str=uuid_str,
                      can_rotate=can_rotate, actions=actions,
                      consume_effect=consume_effect, consume_duration=consume_duration)

        self._subtype_id = subtype_id
        self._small_sprite = small_sprite
        self._big_sprite = big_sprite
        self._projectile_sprite = projectile_sprite
        self._sprite_rotation = sprite_rotation

    def get_subtype_id(self):
        return self._subtype_id

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
                              can_rotate=self._can_rotate, actions=self.item_actions,
                              consume_effect=self.consume_effect, consume_duration=self.consume_duration,
                              projectile_sprite=self._projectile_sprite, subtype_id=self._subtype_id)

    def test_equals(self, other):
        try:
            return (
                super().test_equals(other) and
                self._subtype_id == other._subtype_id and
                self._small_sprite == other._small_sprite and
                self._big_sprite == other._big_sprite and
                self._projectile_sprite == other._projectile_sprite and
                self._sprite_rotation == other._sprite_rotation
            )
        except Exception:
            return False


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
                      can_rotate=True)
        self.cube_art = {} if cube_art is None else cube_art
    
    def level_string(self):
        return "lvl:{}".format(self.level + 1)

    def get_cube_art(self):
        return self.cube_art

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

        factory_clz = itemgen.StatCubesItemFactory

        new_stat_types = factory_clz.gen_stat_types_for_cubes(self.level, self.cubes)
        new_stats = factory_clz.gen_applied_stats_for_cubes_and_stat_types(self.level, self.cubes, new_stat_types)
        new_name = factory_clz.gen_name_for_stats_and_cubes(new_stats, self.cubes)
        new_color = factory_clz.gen_color_for_stats(new_stats)
        new_art = factory_clz.gen_cube_art_for_stats_and_cubes(new_stats, self.cubes)

        return StatCubesItem(new_name, self.level, new_stats, self.cubes,
                             new_color, cube_art=new_art, uuid_str=self.uuid)

    def __str__(self):
        res = "[{}]".format(self.name)
        res += "\n  " + self.uuid
        res += "\n  " + self.level_string() + ", color:{}".format(self.color) + " cube_art:{}".format(self.cube_art)
        res += "\n  cubes: {}".format(self.cubes)
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

    def test_equals(self, other):
        try:
            return (
                super().test_equals(other) and
                self.cube_art == other.cube_art
            )
        except Exception:
            return False

    def __eq__(self, other):
        try:
            return self.uuid == other.uuid
        except Exception:
            return False

    def __hash__(self):
        return hash(self.uuid)

