import random
import collections

from src.game.stats import StatType, ItemStatRanges
from src.utils.util import Utils

CORE_STATS = [StatType.ATT, StatType.DEF, StatType.VIT]

# TODO - regen is too OP, decide whether to balance or totally remove
SPECIAL_STATS = [StatType.HOLE_BONUS, StatType.LIFE_REGEN]

NON_CORE_STATS = [s for s in StatType if (s not in CORE_STATS and s not in SPECIAL_STATS)]

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
    StatType.ATTACK_RADIUS: "{} of Envy",
    StatType.ATTACK_SPEED: "Haste {}",
    StatType.ATTACK_DAMAGE: "{} of Fury",
    StatType.MOVEMENT_SPEED: "Pride {}",
    StatType.DODGE: "Hiding {}",
    StatType.ACCURACY: "Truth {}",
    StatType.LIFE_REGEN: "Growth {}",
    StatType.LIFE_ON_HIT: "{} of Feed",
    StatType.LIFE_LEECH: "{} of Lust",
    StatType.MAX_HEALTH: "Gluttony {}",
    StatType.POTION_HEALING: "Renewal {}",
    StatType.POTION_COOLDOWN: "Wetness {}"
}

ITEM_NAME_SPECIAL_MODIFIER = {
    StatType.HOLE_BONUS: "Holy {}"
}
 
STAT_DESCRIPTIONS = {
    StatType.ATT: "+{} ATT",
    StatType.DEF: "+{} DEF",
    StatType.VIT: "+{} VIT",
    StatType.ATTACK_RADIUS: "+{}% ATT Range",
    StatType.ATTACK_SPEED: "+{}% Attack SPD",
    StatType.ATTACK_DAMAGE: "+{}% Attack DMG",
    StatType.MOVEMENT_SPEED: "+{}% Movespeed",
    StatType.DODGE: "+{} Dodge",
    StatType.ACCURACY: "+{} Accuracy",
    StatType.LIFE_REGEN: "+{} Life Regen",
    StatType.LIFE_ON_HIT: "+{} Life on Hit",
    StatType.LIFE_LEECH: "+{}% Life Leech",
    StatType.MAX_HEALTH: "+{}% Max HP",
    StatType.POTION_HEALING: "+{} Pot Heal",
    StatType.POTION_COOLDOWN: "-{}% Pot Delay"
}    

STAT_COLORS = collections.defaultdict(lambda: (0.85, 0.85, 0.85))
STAT_COLORS.update({
        StatType.ATT: (1, 0.65, 0.65),
        StatType.DEF: (0.65, 0.65, 1),
        StatType.VIT: (0.65, 1, 0.65),
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
            
    def color(self):
        return STAT_COLORS[self.stat_type]


class Item:
    def __init__(self, name, level, stats, cubes, color, cube_art=None):
        """
            name: str
            level: int: 0 to 255
            stats: ordered list of Stat objects
            cubes: list of (int: x, int: y)
            color: tuple (float, float, float)
            cube_art: dict of (x, y) -> int: art_id
        """
        self.name = name
        self.level = level
        self.stats = stats
        self.cubes = ItemFactory.clean_cubes(cubes)
        self.cubes = tuple(cubes)
        self.color = color
        self.cube_art = {} if cube_art is None else cube_art

    def is_attack_item(self):
        return False

    def get_title_color(self):
        return (1, 1, 1)
    
    def level_string(self):
        return "lvl:{}".format(self.level)
        
    def w(self):
        return max([c[0] for c in self.cubes]) + 1
        
    def h(self):
        return max([c[1] for c in self.cubes]) + 1
        
    def all_stats(self):
        return self.stats
        
    def core_stats(self):
        return [s for s in self.stats if s.stat_type in CORE_STATS]
        
    def non_core_stats(self):
        return [s for s in self.stats if s.stat_type not in CORE_STATS]
        
    def __str__(self):
        res = "[{}]".format(self.name)
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


class AttackItem(Item):

    def __init__(self, name, attack, level, stats, cubes, color, cube_art=None):
        Item.__init__(self, name, level, stats, cubes, color, cube_art=cube_art)
        self.attack = attack

    def get_attack(self):
        return self.attack

    def is_attack_item(self):
        return True

    def get_title_color(self):
        att_color = self.get_attack().dmg_color
        return Utils.linear_interp(att_color, (1, 1, 1), 0.75)
        
        
class ItemFactory:

    @staticmethod
    def item_size(cubes):
        x_range = [cubes[0][0], cubes[0][0]]
        y_range = [cubes[0][1], cubes[0][1]]
        for c in cubes:
            x_range[0] = min(x_range[0], c[0])
            x_range[1] = max(x_range[1], c[0])
            y_range[0] = min(y_range[0], c[1])
            y_range[1] = max(y_range[1], c[1])
        return (x_range[1] - x_range[0] + 1, y_range[1] - y_range[0] + 1)

    @staticmethod
    def clean_cubes(cubes):
        temp = list(cubes)
        temp = ItemFactory._push_to_origin(temp)
        temp.sort(key=lambda c: c[0] + 1000*c[1])
        return tuple(temp)

    @staticmethod
    def rotate_item(item):
        new_cubes = []
        for cube in item.cubes:
            new_cubes.append((5 - cube[1], cube[0]))
        new_cubes = ItemFactory.clean_cubes(new_cubes)

        if not item.is_attack_item():
            return Item(item.name, item.level, item.stats,
                        new_cubes, item.color, cube_art=item.cube_art)
        else:
            return AttackItem(item.name, item.get_attack(), item.level,
                              item.stats, new_cubes, item.color, cube_art=item.cube_art)

    @staticmethod
    def do_seed(seed):
        if seed is not None:
            random.seed(seed)

    @staticmethod
    def gen_cubes(n, size=(5, 5), seed=None):
        ItemFactory.do_seed(seed)
        if n > size[0] * size[1]:
            raise ValueError("{} is too many cubes for {}".format(n, size))
           
        choices = []
        for x in range(0, size[0]):
            for y in range(0, size[1]):
                choices.append((x, y))
        random.shuffle(choices)
        rejects = []
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diag = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        res = [choices.pop()]
        
        while len(res) < n:
            c = choices.pop()
            
            # if it's touching a cube we already have, add it.
            touch = sum([int((n[0]+c[0], n[1]+c[1]) in res) for n in neighbors])
            touch_diag = sum([int((n[0]+c[0], n[1]+c[1]) in res) for n in diag])
            
            if touch > 0 and (touch_diag == 0 or random.random() < 0.5):
                res.append(c)
            else:
                rejects.append(c)
                
            if len(choices) == 0:
                choices = rejects
                random.shuffle(choices)
                rejects = []
        
        res = ItemFactory.clean_cubes(res)
                
        return tuple(res)

    @staticmethod
    def _push_to_origin(cubes):
        min_x = min([c[0] for c in cubes])
        min_y = min([c[1] for c in cubes])
        if min_x != 0 or min_y != 0:
            return [(c[0] - min_x, c[1] - min_y) for c in cubes]
        else:
            return cubes

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
    def get_special_stats(cubes):
        return []

    @staticmethod
    def get_name(core_types, non_core_types, special_types):
        if len(core_types) > 2:
            core_types = core_types[:2]
        name = ITEM_CORE_NAME[tuple(core_types)]
        
        if len(non_core_types) > 0:
            name = ITEM_NAME_END[non_core_types[0]].format(name)
        
        if len(special_types) > 0:
            name = ITEM_NAME_SPECIAL_MODIFIER[special_types[0]].format(name)
            
        return name

    @staticmethod
    def gen_item(level, attack=None):
        primary_stat = ItemFactory.gen_core_stat(level)
        n_secondary_stats = int(4 * random.random()) if attack is None else 0
        n_cubes = 5 + int(2 * random.random()) if attack is None else 4

        secondary_stats = ItemFactory.gen_non_core_stats(level, n_secondary_stats, exclude=[primary_stat.stat_type])

        core_stats = [primary_stat] + [x for x in secondary_stats if x.stat_type in CORE_STATS]
        non_core_stats = [x for x in secondary_stats if x.stat_type in NON_CORE_STATS]

        cubes = ItemFactory.gen_cubes(n_cubes)
        special_stats = ItemFactory.get_special_stats(cubes) if attack is None else []

        if attack is None:
            name = ItemFactory.get_name(
                    list(map(lambda x: x.stat_type, core_stats)),
                    list(map(lambda x: x.stat_type, non_core_stats)),
                    list(map(lambda x: x.stat_type, special_stats)))
        else:
            name = attack.name
        
        stats = core_stats + non_core_stats + special_stats

        if attack is not None:
            diff = Utils.sub((1, 1, 1), attack.dmg_color)
            diff = Utils.mult(diff, 0.25)
            color = Utils.sub((1, 1, 1), diff)
        else:
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

        if attack is None:
            return Item(name, level, stats, cubes, color, cube_art)
        else:
            return AttackItem(name, attack, level, stats, cubes, color, cube_art)

    NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    @staticmethod
    def _get_all_possible_cube_configs_helper(n, size, base, already_seen):
        if n <= 0:
            return []
        else:
            res = []
            for cube in base:
                for n_offs in ItemFactory.NEIGHBORS:
                    neighbor = (cube[0] + n_offs[0], cube[1] + n_offs[1])
                    if neighbor not in base:
                        base_copy = [c for c in base]
                        base_copy.append(neighbor)
                        base_copy = ItemFactory.clean_cubes(base_copy)

                        bc_size = ItemFactory.item_size(base_copy)

                        if bc_size[0] <= size[0] and bc_size[1] <= size[1] and base_copy not in already_seen:
                            already_seen.add(base_copy)
                            if n == 1:
                                res.append(base_copy)
                            else:
                                res.extend(ItemFactory._get_all_possible_cube_configs_helper(n-1, size,
                                                                                             base_copy, already_seen))
            return res

    @staticmethod
    def get_all_possible_cube_configs(n=(5, 6, 7), size=(5, 5)):
        """
        :param n: number of allowable cubes. Either a list of numbers or a single number.
        :param size: bounding size of allowable cube configs.
        :return: all possible cube configurations
        """
        try:
            res = []
            for num in n:
                res.extend(ItemFactory._get_all_possible_cube_configs_helper(num-1, size, [(0, 0)], set()))
            return res
        except TypeError:
            return ItemFactory._get_all_possible_cube_configs_helper(n-1, size, [(0, 0)], set())

