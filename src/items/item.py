from enum import Enum
import random
import collections


class StatType(Enum):
    ATT = "ATT",
    DEF = "DEF",
    VIT = "VIT",
    ATTACK_RADIUS = "ATTACK_RADIUS",
    # MOV_SPD_WHILE_ATTACKING = "MOV_SPD_WHILE_ATTACKING",
    ATTACK_SPEED = "ATTACK_SPEED",
    ATTACK_DAMAGE= "ATTACK_DAMAGE",
    # MOV_SPD_OF_ENEMIES_IN_RADIUS = "MOV_SPD_OF_ENEMIES_IN_RADIUS",
    MOVEMENT_SPEED = "MOVEMENT_SPEED",
    DODGE = "DODGE",
    ACCURACY = "ACCURACY",
    LIFE_REGEN = "LIFE_REGEN",
    LIFE_ON_HIT = "LIFE_ON_HIT",
    LIFE_LEECH = "LIFE_LEECH",
    MAX_HEALTH = "MAX_HEALTH",
    POTION_HEALING = "POTION_HEALING",
    POTION_COOLDOWN = "POTION_COOLDOWN",

    HOLE_BONUS = "HOLE_BONUS"
    
CORE_STATS = [StatType.ATT, StatType.DEF, StatType.VIT]  
SPECIAL_STATS = [StatType.HOLE_BONUS]
NON_CORE_STATS = [s for s in StatType if (s not in CORE_STATS and s not in SPECIAL_STATS)]
 
STAT_DESCRIPTIONS = {
    StatType.ATT:"+{} ATT",
    StatType.DEF:"+{} DEF",
    StatType.VIT:"+{} VIT",
    StatType.ATTACK_RADIUS:"+{}% ATT Range",
    # StatType.MOV_SPD_WHILE_ATTACKING:"+{}% Movespeed While Attacking",
    StatType.ATTACK_SPEED:"+{}% Attack SPD",
    StatType.ATTACK_DAMAGE:"+{} Attack DMG",
    # StatType.MOV_SPD_OF_ENEMIES_IN_RADIUS:"-{}% Attacked Enemy Speed",
    StatType.MOVEMENT_SPEED:"+{}% Movespeed",
    StatType.DODGE:"+{}% Dodge",
    StatType.ACCURACY:"+{} Accuracy",
    StatType.LIFE_REGEN:"+{} Life Regen",
    StatType.LIFE_ON_HIT:"+{} Life on Hit",
    StatType.LIFE_LEECH:"+{}% Life Leech",
    StatType.MAX_HEALTH:"+{}% Max HP",
    StatType.POTION_HEALING:"+{} Pot Heal",
    StatType.POTION_COOLDOWN:"-{}% Pot Delay"
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
        self.cubes = cubes
        self.color = color
        self.cube_art = {} if cube_art is None else cube_art
    
    def level_string(self):
        return "lvl:{}".format(self.level)
        
    def w(self):
        return max([c[0] for c in self.cubes]) + 1
        
    def h(self):
        return max([c[1] for c in self.cubes]) + 1
        
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
        
        
class ItemFactory:
    def do_seed(seed):
        if seed is not None:
            random.seed(seed)
            
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
        
        # push cubes to top left
        min_x = min([c[0] for c in res])
        min_y = min([c[1] for c in res])
        if min_x > 0 or min_y > 0:
            res = [(c[0] - min_x, c[1] - min_y) for c in res]
                
        return tuple(res)
        
    def gen_core_stats():
        res = []
        for stat in CORE_STATS:
            if random.random() < 0.333:
                res.append(ItemStat(stat, int(random.random()*30)))
        return res
        
    def gen_non_core_stats(n):
        choices = list(NON_CORE_STATS)
        res = []
        while len(res) < n and len(choices) > 0:
            choice = choices[int(len(choices)*random.random())]
            value = 1 + int(random.random() * 16)
            res.append(ItemStat(choice, value))
            
        return res
        
    def gen_item():
        name = "Cube of Hate"
        stats = ItemFactory.gen_core_stats() 
        stats.extend(ItemFactory.gen_non_core_stats(int(4*random.random())))
        cubes = ItemFactory.gen_cubes(5 + int(2 * random.random()))
        color = [1, 0.5 + random.random()/2, 0.5 + random.random()/2]
        random.shuffle(color)
        color = tuple(color)
        cube_art = {}
        for c in cubes:
            if random.random() < 0.15:
                cube_art[c] = int(6*random.random())
        level = 1 + int(63 * random.random())   
        return Item(name, level, stats, cubes, color, cube_art)

     
if __name__ == "__main__":
     print(ItemFactory.gen_item())

