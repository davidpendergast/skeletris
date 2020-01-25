import random
import math

from src.items.item import ItemTypes, SpriteItem, StatCubesItem, AppliedStat, ItemTags
from src.game.stats import StatTypes, StatType, StatProvider
import src.game.spriteref as spriteref
from src.utils.util import Utils
from src.items.cubeutils import CubeUtils
import src.game.statuseffects as statuseffects
import src.game.balance as balance
import src.game.debug as debug


CORE_STATS = [StatTypes.ATT, StatTypes.DEF, StatTypes.VIT]

NON_CORE_STATS = [StatTypes.HP_ON_KILL]


class ItemFactory:

    @staticmethod
    def gen_item_type(level):
        if debug.ignore_loot_levels():
            item_type_choices = ItemTypes.all_types()
            return random.choice(item_type_choices)
        else:
            item_type_choices = []
            for c in ItemTypes.all_types(at_level=level):
                for _ in range(0, c.get_drop_rate()):
                    item_type_choices.append(c)
            if len(item_type_choices) > 0:
                return random.choice(item_type_choices)
            else:
                print("WARN: no valid item types to drop as loot at level: {}".format(level))
                return None

    @staticmethod
    def gen_item(level, item_type=None):
        if item_type is None:
            item_type = ItemFactory.gen_item_type(level)
            if item_type is None:
                return None

        if item_type == ItemTypes.STAT_CUBE_5:
            return StatCubesItemFactory.gen_item(level, 5)
        elif item_type == ItemTypes.STAT_CUBE_6:
            return StatCubesItemFactory.gen_item(level, 6)
        elif item_type == ItemTypes.STAT_CUBE_7:
            return StatCubesItemFactory.gen_item(level, 7)

        elif item_type == ItemTypes.POTION:
            return PotionItemFactory.gen_item(level)

        elif item_type.has_tag(ItemTags.WEAPON):
            return WeaponItemFactory.gen_item(level, item_type=item_type)

        return None


#_ALL_SPRITE_BUNDLES_FOR_ITEMS = {}  # bundle_id -> _SpriteBundleForItem


#class _SpriteBundleForItem:

#    def __init__(self, bundle_id, entity_sprite, inventory_sprite, projectile_sprite=None):
#        self.bundle_id = bundle_id
#        self.entity_sprite = entity_sprite
#        self.inventory_sprite = inventory_sprite
#        self.projectile_sprite = projectile_sprite

#        _ALL_SPRITE_BUNDLES_FOR_ITEMS[bundle_id] = self


#class _SpriteBundlesForItems:

#    @staticmethod
#    def get_bundle_for_id(bundle_id):
#        if bundle_id in _ALL_SPRITE_BUNDLES_FOR_ITEMS:
#            return _ALL_SPRITE_BUNDLES_FOR_ITEMS[bundle_id]
#        else:
#            return None

#    SWORD_SPRITES = _SpriteBundleForItem("sword_sprites", spriteref.Items.sword_small, spriteref.Items.sword_big)


class WeaponItemFactory:

    @staticmethod
    def gen_item(level, item_type=None):

        if item_type is None:
            all_types = ItemTypes.all_types(at_level=level, with_tags=(ItemTags.WEAPON,))
            if len(all_types) > 0:
                item_type = random.choice(all_types)
            else:
                print("WARN: no valid weapon types for level: {}".format(level))
                return None

        from src.game.gameengine import ItemActions

        if item_type == ItemTypes.SWORD_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.SWORD_ATTACK]
            return SpriteItem("Sword of Truth", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 3, local=True)],
                              spriteref.Items.sword_small, spriteref.Items.sword_big, actions=actions)

        elif item_type == ItemTypes.WHIP_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.WHIP_ATTACK]
            return SpriteItem("Whip of Agony", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 1, local=True),
                               AppliedStat(StatTypes.FLINCH_ON_HIT, 1, local=True)],
                              spriteref.Items.whip_small, spriteref.Items.whip_big, actions=actions)

        elif item_type == ItemTypes.DAGGER_WEAPON:
            cubes = [(0, 0), (0, 1)]
            actions = [ItemActions.DAGGER_ATTACK]
            return SpriteItem("Dagger of Pain", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 1, local=True),
                               AppliedStat(StatTypes.THROWN_ATT, 1, local=True)],
                              spriteref.Items.dagger_small, spriteref.Items.dagger_big, actions=actions)

        elif item_type == ItemTypes.SHIELD_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.SHIELD_ATTACK]
            return SpriteItem("Shield of Security", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 2, local=True),
                               AppliedStat(StatTypes.PLUS_DEFENSE_ON_HIT, 4, local=True)],
                              spriteref.Items.shield_small, spriteref.Items.shield_big, actions=actions)

        elif item_type == ItemTypes.SPEAR_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2), (0, 3)]
            actions = [ItemActions.SPEAR_ATTACK]
            return SpriteItem("Spear of Justice", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 3, local=True),
                               AppliedStat(StatTypes.THROWN_ATT, 3, local=True)],
                              spriteref.Items.spear_small, spriteref.Items.spear_big, actions=actions)

        elif item_type == ItemTypes.WAND_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.WAND_ATTACK]
            return SpriteItem("Wand of Harming", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, -1, local=True),
                               AppliedStat(StatTypes.POISON_ON_HIT, 2, local=True)],
                              spriteref.Items.wand_small, spriteref.Items.wand_big,
                              projectile_sprite=spriteref.Items.projectile_small, actions=actions)

        elif item_type == ItemTypes.BOW_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2)]
            actions = [ItemActions.BOW_ATTACK]
            return SpriteItem("Bow of Power", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 2, local=True)],
                              spriteref.Items.bow_small, spriteref.Items.bow_big, actions=actions,
                              projectile_sprite=spriteref.Items.arrow_projectile_small)

        elif item_type == ItemTypes.AXE_WEAPON:
            cubes = [(0, 0), (1, 0), (1, 1), (1, 2)]
            actions = [ItemActions.AXE_ATTACK]
            return SpriteItem("Axe of Striking", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 4, local=True),
                               AppliedStat(StatTypes.THROWN_ATT, 2, local=True)],
                              spriteref.Items.axe_small, spriteref.Items.axe_big, actions=actions)

        elif item_type == ItemTypes.FISHING_ROD_WEAPON:
            cubes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
            actions = [ItemActions.FISHING_ROD_ATTACK]
            return SpriteItem("Rod of Glory", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 2, local=True),
                               AppliedStat(StatTypes.GRASP_ON_MELEE_HIT, 2, local=True)],
                              spriteref.Items.fishing_rod_small, spriteref.Items.fishing_rod_big, actions=actions)

        elif item_type == ItemTypes.SLINGSHOT_WEAPON:
            cubes = [(0, 0), (0, 1), (1, 0), (1, 1)]
            actions = [ItemActions.SLINGSHOT_ATTACK]
            return SpriteItem("Slingshot of Hope", item_type, level, cubes,
                              [AppliedStat(StatTypes.ATT, 0, local=True),
                               AppliedStat(StatTypes.SWAP_ON_HIT, 1, local=True)],
                              spriteref.Items.slingshot_small, spriteref.Items.slingshot_big, actions=actions)

        print("ERROR: unrecognized weapon type: {}".format(item_type))
        return None


_ALL_POTION_TEMPLATES = []


class PotionTemplate:

    def __init__(self, name, type_id, min_level=0, status=None, duration=3, drop_rate=1):
        self.name = name
        self.type_id = type_id
        self.min_level = min_level
        self.status_effect = status
        self.duration = duration
        self.drop_rate = drop_rate

        _ALL_POTION_TEMPLATES.append(self)


HEALING = PotionTemplate("Potion of Healing", "heal_1", min_level=0, drop_rate=7,
                         status=statuseffects.StatusEffectTypes.HP_REGEN_1,
                         duration=balance.POTION_SMALL_HEAL_DURATION)

MAJOR_HEALING = PotionTemplate("Potion of Healing II", "heal_2", min_level=5, drop_rate=4,
                               status=statuseffects.StatusEffectTypes.HP_REGEN_2,
                               duration=balance.POTION_MED_HEAL_DURATION)

HARMING = PotionTemplate("Potion of Harming", "harm_1", min_level=4, drop_rate=5,
                         status=statuseffects.StatusEffectTypes.POISON,
                         duration=balance.POTION_POIS_DURATION)

SPEED_POTION = PotionTemplate("Potion of Quickness", "speed_1", min_level=1, drop_rate=5,
                              status=statuseffects.StatusEffectTypes.SPEED,
                              duration=balance.POTION_SPEED_DUR)

SLOW_POTION = PotionTemplate("Potion of the Sloth", "slow_1", min_level=5, drop_rate=4,
                             status=statuseffects.StatusEffectTypes.SLOWNESS,
                             duration=balance.POTION_SLOW_DUR)


NULL_POTION = PotionTemplate("Null Potion", "null_1", min_level=6, drop_rate=3,
                             status=statuseffects.StatusEffectTypes.NULLIFICATION,
                             duration=balance.POTION_NULLIFICATION_DURATION)

NIGHT_VISION = PotionTemplate("Potion of Light", "light_1", min_level=3, drop_rate=2,
                              status=statuseffects.StatusEffectTypes.NIGHT_VISION,
                              duration=balance.POTION_NIGHT_VISION_DURATION)

CONFUSION_POTION = PotionTemplate("Confusion Potion", "confuse_1", min_level=5, drop_rate=5,
                                  status=statuseffects.StatusEffectTypes.CONFUSION,
                                  duration=balance.POTION_CONFUSION_DURATION)


class PotionTemplates:

    @staticmethod
    def all_templates(for_level=None):
        all_of_em = _ALL_POTION_TEMPLATES
        if for_level is None:
            return list(all_of_em)
        else:
            return [t for t in all_of_em if t.min_level <= for_level]

    @staticmethod
    def get_template_with_id(type_id):
        for pot in _ALL_POTION_TEMPLATES:
            if pot.type_id == type_id:
                return pot
        return None


class PotionItemFactory:

    @staticmethod
    def gen_item(level, template=None, not_templates=()):
        if template is None:
            if debug.ignore_loot_levels():
                all_temps = [t for t in PotionTemplates.all_templates() if t not in not_templates]
                template = None if len(all_temps) == 0 else random.choice(all_temps)
            else:
                all_temps = [t for t in PotionTemplates.all_templates(for_level=level) if t not in not_templates]
                weighted_temps = []
                for t in all_temps:
                    for _ in range(0, t.drop_rate):
                        weighted_temps.append(t)
                template = None if len(weighted_temps) == 0 else random.choice(weighted_temps)

        if template is None:
            return None

        from src.game.gameengine import ItemActions

        cubes = [(0, 0)]
        color = (1, 1, 1) if template.status_effect is None else template.status_effect.get_color()
        res = SpriteItem(template.name, ItemTypes.POTION, template.min_level, cubes, {},
                         spriteref.Items.potion_small, spriteref.Items.potion_big,
                         subtype_id=template.type_id, actions=[ItemActions.CONSUME_ITEM], color=color,
                         consume_effect=template.status_effect, consume_duration=template.duration)

        return res


# TODO - maybe one day
#_ALL_SUMMONING_TOME_TEMPLATES = []


#class SummoningTomeTemplate:

#    def __init__(self, name, enemy_template, min_level=0, drop_rate=1):
#        self.name = name
#        self.min_level = min_level
#        self.enemy_template = enemy_template
#        self.drop_rate = drop_rate
#        _ALL_SUMMONING_TOME_TEMPLATES.append(self)


#class SummoningTomeTemplates:
#
#    def all_templates(self, for_level=None):
#        all_of_em = _ALL_SUMMONING_TOME_TEMPLATES
#        if for_level is None:
#            return list(all_of_em)
#        else:
#            return [t for t in all_of_em if t.min_level <= for_level]


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
        StatTypes.HP_ON_KILL: _linear_map(16, 1, 8)
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
    def gen_color_for_stats(stats):
        color = tuple([0.5 + random.random() * 0.25] * 3)
        core_stats = [s for s in stats if s.get_type() in CORE_STATS]
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
        return color

    @staticmethod
    def gen_cube_art_for_stats_and_cubes(stats, cubes, art_types=()):
        """art_types: list of ints from 1 to 5"""
        cube_art = {}
        cubes_copy = [c for c in cubes]
        random.shuffle(cubes_copy)

        for i in range(0, len(stats)):
            if i < len(cubes_copy):
                if i < len(art_types):
                    cube_art[cubes_copy[i]] = art_types[i]
                else:
                    cube_art[cubes_copy[i]] = 1 + int(5 * random.random())

        return cube_art

    @staticmethod
    def gen_stat_types_for_cubes(level, cubes):
        # require at least one core stat
        res = [random.choice(CORE_STATS), ]

        choices = [s for s in CORE_STATS + NON_CORE_STATS if s != res[0]]

        n_secondary_stats = int((balance.max_stats_for_n_cubes(len(cubes))) * random.random())

        for i in range(0, n_secondary_stats):
            if len(choices) > 0:
                next_stat = random.choice(choices)
                choices.remove(next_stat)

                res.append(next_stat)

        return res

    @staticmethod
    def gen_applied_stats_for_cubes_and_stat_types(level, cubes, stat_types):
        res = []
        for stat_type in stat_types:
            low, high = ItemStatRanges.get_range(stat_type, level)
            res.append(AppliedStat(stat_type, random.randint(low, high)))

        if CubeUtils.is_holy(cubes):
            for stat in res:
                stat.value = StatCubesItemFactory.modify_stat_for_holy_item(stat.get_type(), stat.get_value())

        return res

    @staticmethod
    def modify_stat_for_holy_item(stat_type, base_value, unmodify=False):
        if stat_type in CORE_STATS:
            if not unmodify:
                return base_value * 2
            else:
                return base_value // 2
        else:
            return base_value

    @staticmethod
    def gen_name_for_stats_and_cubes(stats, cubes):
        if CubeUtils.is_holy(cubes):
            return "Holy Artifact"
        elif len(cubes) <= 5:
            return ItemTypes.STAT_CUBE_5.get_name()
        elif len(cubes) == 6:
            return ItemTypes.STAT_CUBE_6.get_name()
        else:
            return ItemTypes.STAT_CUBE_7.get_name()

    @staticmethod
    def gen_cubes(n_cubes):
        cubes = CubeUtils.gen_cubes(n_cubes)
        is_holy = CubeUtils.is_holy(cubes)

        if n_cubes >= 7 and not is_holy and debug.holy_artifacts_100x_more_likely():
            for _ in range(0, 100):
                cubes = CubeUtils.gen_cubes(n_cubes)
                is_holy = CubeUtils.is_holy(cubes)
                if is_holy:
                    break

        return cubes

    @staticmethod
    def gen_item(level, n_cubes):
        cubes = StatCubesItemFactory.gen_cubes(n_cubes)
        return StatCubesItemFactory.gen_item_for_cubes(level, cubes)

    @staticmethod
    def gen_item_for_cubes(level, cubes):
        stat_types = StatCubesItemFactory.gen_stat_types_for_cubes(level, cubes)
        stats = StatCubesItemFactory.gen_applied_stats_for_cubes_and_stat_types(level, cubes, stat_types)
        return StatCubesItemFactory.gen_item_for_cubes_and_stats(level, cubes, stats)

    @staticmethod
    def gen_item_for_cubes_and_stats(level, cubes, stats):
        cubes = CubeUtils.clean_cubes(cubes)

        name = StatCubesItemFactory.gen_name_for_stats_and_cubes(stats, cubes)
        color = StatCubesItemFactory.gen_color_for_stats(stats)
        cube_art = StatCubesItemFactory.gen_cube_art_for_stats_and_cubes(stats, cubes)

        return StatCubesItem(name, level, stats, cubes, color, cube_art=cube_art)

