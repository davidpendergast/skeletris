import random
import math

from src.items.item import ItemTypes, SpriteItem, StatCubesItem, AppliedStat
from src.game.stats import StatTypes, StatType, StatProvider
import src.game.spriteref as spriteref
from src.utils.util import Utils
from src.items.cubeutils import CubeUtils
import src.utils.colors as colors
import src.game.dialog as dialog
import src.game.globalstate as gs
import src.game.statuseffects as statuseffects
import src.game.balance as balance
import src.game.debug as debug


CORE_STATS = [StatTypes.ATT, StatTypes.DEF, StatTypes.VIT]

NON_CORE_STATS = []


class ItemFactory:

    @staticmethod
    def gen_item(level, item_type):
        if item_type == ItemTypes.STAT_CUBE_5:
            return StatCubesItemFactory.gen_item(level, n_cubes=5)
        elif item_type == ItemTypes.STAT_CUBE_6:
            return StatCubesItemFactory.gen_item(level, n_cubes=6)
        elif item_type == ItemTypes.STAT_CUBE_7:
            return StatCubesItemFactory.gen_item(level, n_cubes=7)

        from src.game.gameengine import ItemActions

        if item_type == ItemTypes.POTION:
            return PotionItemFactory.gen_item(level)

        elif item_type == ItemTypes.SWORD_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.SWORD_ATTACK]
            return SpriteItem("Sword of Truth", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 4, local=True)],
                              spriteref.Items.sword_small, spriteref.Items.sword_big, actions=actions)
        elif item_type == ItemTypes.WHIP_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.WHIP_ATTACK]
            return SpriteItem("Whip of Sapping", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 3, local=True),
                               AppliedStat(StatTypes.PLUS_SPEED_ON_HIT, 2, local=True)],
                              spriteref.Items.whip_small, spriteref.Items.whip_big, actions=actions)
        elif item_type == ItemTypes.DAGGER_WEAPON:
            cubes = [(0, 0), (0, 1)]
            actions = [ItemActions.DAGGER_ATTACK]
            return SpriteItem("Dagger of Quickness", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 3, local=True)],
                              spriteref.Items.dagger_small, spriteref.Items.dagger_big, actions=actions)
        elif item_type == ItemTypes.SHIELD_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.SHIELD_ATTACK]
            return SpriteItem("Shield of Mending", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 2, local=True),
                               AppliedStat(StatTypes.PLUS_DEFENSE_ON_HIT, 4, local=True)],
                              spriteref.Items.shield_small, spriteref.Items.shield_big, actions=actions)
        elif item_type == ItemTypes.SPEAR_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2), (0, 3)]
            actions = [ItemActions.SPEAR_ATTACK]
            return SpriteItem("Spear of Justice", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 2, local=True),
                               AppliedStat(StatTypes.THROWN_ATT, 4, local=True)],
                              spriteref.Items.spear_small, spriteref.Items.spear_big, actions=actions)
        elif item_type == ItemTypes.WAND_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            return SpriteItem("Wand of Mystery", item_type, level, cubes, [],
                              spriteref.Items.wand_small, spriteref.Items.wand_big)
        elif item_type == ItemTypes.BOW_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.BOW_ATTACK]
            return SpriteItem("Bow of Speed", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 3, local=True)],
                              spriteref.Items.bow_small, spriteref.Items.bow_big, actions=actions)
        elif item_type == ItemTypes.AXE_WEAPON:
            cubes = [(0, 0), (1, 0), (1, 1), (1, 2)]
            actions = [ItemActions.AXE_ATTACK]
            return SpriteItem("Axe of Striking", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 5, local=True),
                               AppliedStat(StatTypes.THROWN_ATT, 3, local=True)],
                              spriteref.Items.axe_small, spriteref.Items.axe_big, actions=actions)

        return None


_ALL_POTION_TEMPLATES = []


class PotionTemplate:

    def __init__(self, name, dialog_text, min_level=0, status=None):
        self.name = name
        self.dialog_text = dialog_text
        self.min_level = min_level
        self.status_effect = status

        _ALL_POTION_TEMPLATES.append(self)


HEALING = PotionTemplate("Potion of Healing", "That was refreshing.",
                         min_level=0,
                         status=statuseffects.new_regen_effect(balance.POTION_SMALL_HEAL_VAL,
                                                               balance.POTION_SMALL_HEAL_DURATION))


MAJOR_HEALING = PotionTemplate("Potion of Healing II", "That was refreshing!",
                               min_level=5,
                               status=statuseffects.new_regen_effect(balance.POTION_MED_HEAL_VAL,
                                                                     balance.POTION_MED_HEAL_DURATION))

HARMING = PotionTemplate("Potion of Harming", "Ow, ok oww... ouch, why did I drink that?",
                         min_level=7,
                         status=statuseffects.new_poison_effect(balance.POTION_POIS_VAL,
                                                                balance.POTION_POIS_DURATION))
SPEED_POTION = PotionTemplate("Potion of Quickness", "I feel... fast.",
                              min_level=9,
                              status=statuseffects.new_speed_effect(balance.POTION_SPEED_VAL,
                                                                    balance.POTION_SPEED_DUR))

SLOW_POTION = PotionTemplate("Potion of the Sloth", "I... feel... slow.",
                             min_level=4,
                             status=statuseffects.new_slow_effect(balance.POTION_SLOW_VAL,
                                                                  balance.POTION_SLOW_DUR))


NULL_POTION = PotionTemplate("Null Potion", "I feel a little better... I think?",
                             min_level=6,
                             status=statuseffects.new_nullification_effect(balance.POTION_NULLIFICATION_DURATION))

NIGHT_VISION = PotionTemplate("Potion of Light", "Wow, I should have updated my prescription years ago.",
                              min_level=3,
                              status=statuseffects.new_night_vision_effect(balance.POTION_NIGHT_VISION_VAL,
                                                                           balance.POTION_NIGHT_VISION_DURATION))


class PotionTemplates:

    @staticmethod
    def all_templates(for_level=None):
        all_of_em = _ALL_POTION_TEMPLATES
        if for_level is None:
            return list(all_of_em)
        else:
            return [t for t in all_of_em if t.min_level <= for_level]


class PotionItemFactory:

    @staticmethod
    def gen_item(level):
        if debug.ignore_level_restrictions_on_drops():
            templates = [t for t in PotionTemplates.all_templates()]
        else:
            templates = [t for t in PotionTemplates.all_templates(for_level=level)]

        if len(templates) == 0:
            template = NULL_POTION
        else:
            template = random.choice(templates)

        from src.game.gameengine import ItemActions

        cubes = [(0, 0)]
        consume_effect = template.status_effect
        color = (1, 1, 1) if consume_effect is None else consume_effect.get_color()
        res = SpriteItem(template.name, ItemTypes.POTION, template.min_level, cubes, {},
                          spriteref.Items.potion_small, spriteref.Items.potion_big,
                          actions=[ItemActions.CONSUME_ITEM], consume_effect=consume_effect, color=color)

        return res


def _exp_map(x1, y0, y1, intensity=0, integral=True):
    """
        intensity: float in [0.0, 1.0). bigger = harsher slope near max
    """
    b = intensity
    a = (1 / x1) * math.log((y1 - y0*b) / (y0 * (1 - b)))
    if integral:
        return [round((y0 * b) + y0 * (1 - b) * math.exp(a * x)) for x in range(0, x1+1)]
    else:
        return [(y0 * b) + y0 * (1 - b) * math.exp(a * x) for x in range(0, x1 + 1)]


def _linear_map(x1, y0, y1):
    return [round(y0 + (x / x1) * (y1 - y0)) for x in range(0, x1+1)]


class ItemStatRanges:

    MAX_VALS_FOR_LEVEL = {
        StatTypes.ATT: _linear_map(16, 1, 8),
        StatTypes.DEF: _linear_map(16, 1, 8),
        StatTypes.VIT: _linear_map(16, 1, 24),
        StatTypes.SPEED: _linear_map(16, 1, 4),
    }

    @staticmethod
    def get_range(stat_type, lvl):
        if stat_type in ItemStatRanges.MAX_VALS_FOR_LEVEL:
            max_vals = ItemStatRanges.MAX_VALS_FOR_LEVEL[stat_type]
            if lvl < len(max_vals):
                return (1, max_vals[lvl])
            else:
                return (1, max_vals[-1])
        else:
            return (1, 1)


class StatCubesItemFactory:

    @staticmethod
    def gen_core_stat(lvl):
        stat = CORE_STATS[int(random.random() * len(CORE_STATS))]
        low, high = ItemStatRanges.get_range(stat, lvl)

        return AppliedStat(stat, random.randint(low, high))

    @staticmethod
    def gen_non_core_stats(lvl, n, exclude=()):
        res = []
        choices = [x for x in NON_CORE_STATS + CORE_STATS if x not in exclude]
        while len(res) < n and len(choices) > 0:
            choice = choices[int(len(choices) * random.random())]
            low, high = ItemStatRanges.get_range(choice, lvl)
            res.append(AppliedStat(choice, random.randint(low, high)))
            choices.remove(choice)

        return res

    @staticmethod
    def gen_item(level, n_cubes=None):
        primary_stat = StatCubesItemFactory.gen_core_stat(level)
        n_cubes = n_cubes if n_cubes is not None else 5 + int(2 * random.random())
        n_secondary_stats = Utils.bound(int((n_cubes - 4) * random.random()), 0, 4)

        secondary_stats = StatCubesItemFactory.gen_non_core_stats(level, n_secondary_stats,
                                                                  exclude=[primary_stat.stat_type])

        core_stats = [primary_stat] + [x for x in secondary_stats if x.stat_type in CORE_STATS]
        non_core_stats = [x for x in secondary_stats if x.stat_type in NON_CORE_STATS]

        cubes = CubeUtils.gen_cubes(n_cubes)

        # TODO - should probably overhaul item naming
        if len(cubes) <= 5:
            name = ItemTypes.STAT_CUBE_5.get_name()
        elif len(cubes) == 6:
            name = ItemTypes.STAT_CUBE_6.get_name()
        else:
            name = ItemTypes.STAT_CUBE_7.get_name()

        stats = core_stats + non_core_stats

        color = tuple([0.5 + random.random() * 0.25] * 3)
        if len(core_stats) > 0:
            rand1 = 0.5 + random.random() * 0.5
            rand2 = 0.5 + random.random() * 0.5
            max_core = max(core_stats, key=lambda x: x.value)
            if max_core.stat_type is StatTypes.ATT:
                color = (1, rand1, rand2)
            elif max_core.stat_type is StatTypes.VIT:
                color = (rand1, 1, rand2)
            elif max_core.stat_type is StatTypes.DEF:
                color = (rand1, rand2, 1)

        cube_art = {}
        cubes_copy = [c for c in cubes]
        random.shuffle(cubes_copy)

        for i in range(0, n_secondary_stats):
            if i < len(cubes_copy):
                cube_art[cubes_copy[i]] = 1 + int(5 * random.random())

        return StatCubesItem(name, level, stats, cubes, color, cube_art=cube_art)