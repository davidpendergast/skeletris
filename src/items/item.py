import random
import uuid
import collections
from enum import Enum

from src.game.stats import StatType, StatProvider, ItemStatRanges
from src.utils.util import Utils
import src.renderengine.img as img
from src.items.cubeutils import CubeUtils
import src.game.spriteref as spriteref
from src.game.gameengine import ActionProvider, ActionType, ConsumeItemAction, AttackAction

CORE_STATS = [StatType.ATT, StatType.DEF, StatType.VIT]

NON_CORE_STATS = []

ITEM_CORE_NAME = {
    (): "Vessel",
    tuple([StatType.ATT]): "Cube",
    tuple([StatType.DEF]): "Tetra",
    tuple([StatType.VIT]): "Quad",
    (StatType.ATT, StatType.ATT): "Cubes",
    (StatType.ATT, StatType.DEF): "Cuboid",
    (StatType.ATT, StatType.VIT): "Cubit",
    (StatType.DEF, StatType.ATT): "Tetrit",
    (StatType.DEF, StatType.DEF): "Tetras",
    (StatType.DEF, StatType.VIT): "Tetrit",
    (StatType.VIT, StatType.ATT): "Quadcube",
    (StatType.VIT, StatType.DEF): "Quadroid",
    (StatType.VIT, StatType.VIT): "Quads"
}
     
ITEM_NAME_END = {
#    StatType.ATTACK_RADIUS: "{} of Envy",
#    StatType.ATTACK_SPEED: "Haste {}",
#    StatType.ATTACK_DAMAGE: "{} of Fury",
#    StatType.MOVEMENT_SPEED: "Pride {}",
#    StatType.DODGE: "Hiding {}",
#    StatType.ACCURACY: "Truth {}",
#    StatType.LIFE_REGEN: "Growth {}",
#    StatType.LIFE_ON_HIT: "{} of Feed",
#    StatType.LIFE_LEECH: "{} of Lust",
#    StatType.MAX_HEALTH: "Gluttony {}",
#    StatType.POTION_HEALING: "Renewal {}",
#    StatType.POTION_COOLDOWN: "Wetness {}"
}
 
STAT_DESCRIPTIONS = {
    StatType.ATT: "+{} ATT",
    StatType.DEF: "+{} DEF",
    StatType.VIT: "+{} VIT",
}    

STAT_COLORS = collections.defaultdict(lambda: (0.85, 0.85, 0.85))
STAT_COLORS.update({
        StatType.ATT: (1, 0.65, 0.65),
        StatType.DEF: (0.65, 0.65, 1),
        StatType.VIT: (0.65, 1, 0.65),
        StatType.SPEED: (1, 1, 0.65)
})


class ItemStat:
    """Stat that is attached to an item"""
    def __init__(self, stat_type, value):
        self.stat_type = stat_type
        self.value = value

    def __repr__(self):
        if self.stat_type in STAT_DESCRIPTIONS:
            return STAT_DESCRIPTIONS[self.stat_type].format(self.value)
        else:
            return "{}: {}".format(self.stat_type, self.value)

    def __eq__(self, other):
        try:
            return self.stat_type == other.stat_type and self.value == other.value
        except ValueError:
            return False

    def __hash__(self):
        return hash((self.stat_type, self.value))
            
    def color(self):
        return STAT_COLORS[self.stat_type]

    def to_json(self):
        return [self.stat_type, self.value]

    @staticmethod
    def from_json(blob):
        """
        blob: list of [str, int]
        """
        stat_type = StatType(blob[0])
        value = int(blob[1])
        return ItemStat(stat_type, value)


class ItemTags(Enum):
    EQUIPMENT = "Equipment"
    WEAPON = "Weapon"
    CONSUMABLE = "Consumable"
    STORY = "Story"


class ItemType:

    def __init__(self, name, tags):
        self.name = name
        self.tags = tags

    def get_name(self):
        return self.name

    def get_tags(self):
        return self.tags

    def has_tag(self, tag):
        return tag in self.tags


_ALL_TYPES = []


def _new_type(name, tags):
    res = ItemType(name, tags)
    _ALL_TYPES.append(res)
    return res


class ItemTypes:

    @staticmethod
    def all_types():
        return list(_ALL_TYPES)

    STAT_CUBE_5 = _new_type("Small Trinket", (ItemTags.EQUIPMENT))
    STAT_CUBE_6 = _new_type("Medium Relic", (ItemTags.EQUIPMENT))
    STAT_CUBE_7 = _new_type("Large Artifact", (ItemTags.EQUIPMENT)),

    SWORD_WEAPON = _new_type("Sword", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    SHIELD_WEAPON = _new_type("Shield", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    SPEAR_WEAPON = _new_type("Spear", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    WHIP_WEAPON = _new_type("Whip", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    DAGGER_WEAPON = _new_type("Dagger", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    AXE_WEAPON = _new_type("Axe", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    BOW_WEAPON = _new_type("Bow", (ItemTags.EQUIPMENT, ItemTags.WEAPON))
    WAND_WEAPON = _new_type("Wand", (ItemTags.EQUIPMENT, ItemTags.WEAPON))

    POTION = _new_type("Potion", (ItemTags.CONSUMABLE))


class ConsumeItemActionProvider(ActionProvider):

    def __init__(self):
        ActionProvider.__init__(self, "Drink", ActionType.CONSUME_ITEM, color=(0.5, 1, 0.5))

    def get_action(self, actor, position=None, item=None):
        return ConsumeItemAction(actor, item)


class AttackItemActionProvider(ActionProvider):

    def __init__(self, name, icon, target_range):
        ActionProvider.__init__(self, name, ActionType.ATTACK, icon_sprite=icon,
                                target_positions=target_range, color=(1, 0.5, 0.5), needs_to_be_equipped=True)

    def is_mappable(self):
        return True

    def get_action(self, actor, position=None, item=None):
        return AttackAction(actor, item, position)


class ItemActions:
    _cardinal_targets_only = ((-1, 0), (1, 0), (0, -1), (0, 1))

    CONSUME_ITEM = ConsumeItemActionProvider()
    SWORD_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.sword_icon, _cardinal_targets_only)
    SPEAR_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.spear_icon, _cardinal_targets_only)
    WHIP_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.whip_icon, _cardinal_targets_only)
    SHIELD_BLOCK = AttackItemActionProvider("Protect", spriteref.Items.shield_icon, _cardinal_targets_only)  # TODO
    DAGGER_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.dagger_icon, _cardinal_targets_only)
    BOW_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.bow_icon, _cardinal_targets_only)
    AXE_ATTACK = AttackItemActionProvider("Attack", spriteref.Items.axe_icon, _cardinal_targets_only)


class Item(StatProvider):

    def __init__(self, name, item_type, level, cubes, stats, actions=None, color=(1, 1, 1), uuid_str=None, can_rotate=True, title_color=(1, 1, 1)):
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

    def rotate(self):
        return self

    def w(self):
        return max([c[0] for c in self.cubes]) + 1

    def h(self):
        return max([c[1] for c in self.cubes]) + 1

    def stat_value(self, stat_type):
        res = 0
        for stat in self.all_stats():
            if stat.stat_type == stat_type:
                res += stat.value
        return res

    def all_stats(self):
        return self.stats

    def all_actions(self):
        return self.item_actions

    def core_stats(self):
        return [s for s in self.stats if s.stat_type in CORE_STATS]

    def non_core_stats(self):
        return [s for s in self.stats if s.stat_type not in CORE_STATS]

    def get_small_img(self, scale, layer_id, input_img=None):
        pass

    def get_big_img(self, scale, layer_id, input_img=None):
        pass

    def get_entity_sprite(self):
        return spriteref.Items.misc_small


class SpriteItem(Item):

    def __init__(self, name, item_type, level, cubes, stats, small_sprite, big_sprite, sprite_rotation=0,
                 uuid_str=None, can_rotate=True, color=(1,1,1), title_color=(1, 1, 1), actions=None):

        Item.__init__(self, name, item_type, level, cubes, stats, color=color, uuid_str=uuid_str,
                      can_rotate=can_rotate, title_color=title_color, actions=actions)

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
            print("rotating {} to {}".format(self, new_rotation))

            return SpriteItem(self.name, self.get_type(), self.get_level(), new_cubes, self.stats, self._small_sprite,
                              self._big_sprite, sprite_rotation=new_rotation, uuid_str=self.uuid, color=self.color,
                              can_rotate=self._can_rotate, title_color=self.title_color, actions=self.item_actions)


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
            stat = ItemStat.from_json(stat_blob)
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


class ItemFactory:

    @staticmethod
    def gen_item(level, item_type):
        if item_type == ItemTypes.STAT_CUBE_5:
            return StatCubesItemFactory.gen_item(level, n_cubes=5)
        elif item_type == ItemTypes.STAT_CUBE_6:
            return StatCubesItemFactory.gen_item(level, n_cubes=6)
        elif item_type == ItemTypes.STAT_CUBE_7:
            return StatCubesItemFactory.gen_item(level, n_cubes=7)

        elif item_type == ItemTypes.POTION:
            cubes = [(0, 0)]
            actions = [ItemActions.CONSUME_ITEM]
            return SpriteItem("Potion of Null", item_type, level, cubes, {}, spriteref.Items.potion_small, spriteref.Items.potion_big, actions=actions)

        elif item_type == ItemTypes.SWORD_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.SWORD_ATTACK]
            return SpriteItem("Light of Truth", item_type, level, cubes, {}, spriteref.Items.sword_small, spriteref.Items.sword_big, actions=actions)
        elif item_type == ItemTypes.WHIP_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.WHIP_ATTACK]
            return SpriteItem("Pain Rope", item_type, level, cubes, {}, spriteref.Items.whip_small, spriteref.Items.whip_big, actions=actions)
        elif item_type == ItemTypes.DAGGER_WEAPON:
            cubes = [(0, 0), (0, 1)]
            actions = [ItemActions.DAGGER_ATTACK]
            return SpriteItem("Quick Iron", item_type, level, cubes, {}, spriteref.Items.dagger_small, spriteref.Items.dagger_big, actions=actions)
        elif item_type == ItemTypes.SHIELD_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.SHIELD_BLOCK]
            return SpriteItem("Fortress of Mending", item_type, level, cubes, {}, spriteref.Items.shield_small, spriteref.Items.shield_big, actions=actions)
        elif item_type == ItemTypes.SPEAR_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2), (0, 3)]
            actions = [ItemActions.SPEAR_ATTACK]
            return SpriteItem("Justice Beacon", item_type, level, cubes, {}, spriteref.Items.spear_small, spriteref.Items.spear_big, actions=actions)
        elif item_type == ItemTypes.WAND_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            return SpriteItem("Stick of Mystery", item_type, level, cubes, {}, spriteref.Items.wand_small, spriteref.Items.wand_big)
        elif item_type == ItemTypes.BOW_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.BOW_ATTACK]
            return SpriteItem("Bow of Speed", item_type, level, cubes, {}, spriteref.Items.bow_small, spriteref.Items.bow_big, actions=actions)
        elif item_type == ItemTypes.AXE_WEAPON:
            cubes = [(0, 0), (1, 0), (1, 1), (1, 2)]
            actions = [ItemActions.AXE_ATTACK]
            return SpriteItem("Hatchet of Striking", item_type, level, cubes, {}, spriteref.Items.axe_small, spriteref.Items.axe_big, actions=actions)

        return None


class StatCubesItemFactory:

    @staticmethod
    def gen_core_stat(lvl):
        stat = CORE_STATS[int(random.random() * len(CORE_STATS))]
        low, high = ItemStatRanges.get_range(stat, lvl)

        return ItemStat(stat, random.randint(low, high))

    @staticmethod
    def gen_non_core_stats(lvl, n, exclude=()):
        res = []
        choices = [x for x in NON_CORE_STATS + CORE_STATS if x not in exclude]
        while len(res) < n and len(choices) > 0:
            choice = choices[int(len(choices)*random.random())]
            low, high = ItemStatRanges.get_range(choice, lvl)
            res.append(ItemStat(choice, random.randint(low, high)))
            choices.remove(choice)

        return res

    @staticmethod
    def get_name(core_types, non_core_types):
        if len(core_types) > 2:
            core_types = core_types[:2]
        name = ITEM_CORE_NAME[tuple(core_types)]
        
        if len(non_core_types) > 0:
            name = ITEM_NAME_END[non_core_types[0]].format(name)
            
        return name

    @staticmethod
    def gen_item(level, n_cubes=None):
        primary_stat = StatCubesItemFactory.gen_core_stat(level)
        n_cubes = n_cubes if n_cubes is not None else 5 + int(2 * random.random())
        n_secondary_stats = Utils.bound(int((n_cubes-4) * random.random()), 0, 4)

        secondary_stats = StatCubesItemFactory.gen_non_core_stats(level, n_secondary_stats, exclude=[primary_stat.stat_type])

        core_stats = [primary_stat] + [x for x in secondary_stats if x.stat_type in CORE_STATS]
        non_core_stats = [x for x in secondary_stats if x.stat_type in NON_CORE_STATS]

        cubes = CubeUtils.gen_cubes(n_cubes)

        name = StatCubesItemFactory.get_name(
                list(map(lambda x: x.stat_type, core_stats)),
                list(map(lambda x: x.stat_type, non_core_stats)))
        
        stats = core_stats + non_core_stats

        color = tuple([0.5 + random.random() * 0.25] * 3)
        if len(core_stats) > 0:
            rand1 = 0.5 + random.random() * 0.5
            rand2 = 0.5 + random.random() * 0.5
            max_core = max(core_stats, key=lambda x: x.value)
            if max_core.stat_type is StatType.ATT:
                color = (1, rand1, rand2)
            elif max_core.stat_type is StatType.VIT:
                color = (rand1, 1, rand2)
            elif max_core.stat_type is StatType.DEF:
                color = (rand1, rand2, 1)

        cube_art = {}
        cubes_copy = [c for c in cubes]
        random.shuffle(cubes_copy)

        for i in range(0, n_secondary_stats):
            if i < len(cubes_copy):
                cube_art[cubes_copy[i]] = 1 + int(5*random.random())

        return StatCubesItem(name, level, stats, cubes, color, cube_art=cube_art)



class ItemTest:

    @staticmethod
    def test_item_serialization():
        n = 1000
        for _ in range(0, n):
            item = StatCubesItemFactory.gen_item(int(random.random() * 64))
            as_json = item.to_json()
            back_to_item = StatCubesItem.from_json(as_json)

            if not item.test_equals(back_to_item):
                print("ERROR: test failure on test_equals")
                print("original:\n{}".format(item))
                print("post-json:\n{}".format(back_to_item))
                return

            if item != back_to_item:
                print("ERROR: test failure on __eq__")
                print("original:\n{}".format(item))
                print("post-json:\n{}".format(back_to_item))
                return

    @staticmethod
    def test_item_rotation():
        n = 1000
        for _ in range(0, n):
            item = StatCubesItemFactory.gen_item(int(random.random() * 64))
            rot1 = CubeUtils.rotate_item(item)
            rot2 = CubeUtils.rotate_item(rot1)
            rot3 = CubeUtils.rotate_item(rot2)
            rot4 = CubeUtils.rotate_item(rot3)

            if not item.test_equals(rot4):
                print("ERROR: test failure on test_item_rotation")
                print("original:\n{}".format(item))
                print("rotated:\n{}".format(rot4))
                return


if __name__ == "__main__":
    ItemTest.test_item_serialization()
    ItemTest.test_item_rotation()

