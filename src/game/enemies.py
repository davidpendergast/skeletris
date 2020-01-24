import random

import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.stats import StatTypes
import src.game.stats as stats
import src.game.inventory as inventory
import src.items.item as item
import src.utils.colors as colors
import src.items.itemgen as itemgen
import src.game.balance as balance
import src.game.constants as constants


_ALL_TYPES = {}


class EnemyType:

    def __init__(self, type_id):
        self.type_id = type_id
        _ALL_TYPES[type_id] = self

    def __eq__(self, other):
        if isinstance(other, EnemyType):
            return self.type_id == other.type_id
        else:
            return False


class EnemyTypes:
    ANIMAL = EnemyType("ANIMAL")
    UNDEAD = EnemyType("UNDEAD")
    FUNGUS = EnemyType("FUNGUS")
    MASKED = EnemyType("MASKED")
    BOSS = EnemyType("BOSS")
    INANIMATE = EnemyType("INANIMATE")

    @staticmethod
    def all_types():
        return list(_ALL_TYPES)


class EnemyTemplate:

    def __init__(self, name):
        self._name = name

    def get_sprites(self):
        return spriteref.player_idle_arms_up_all

    def get_types(self):
        return []

    def get_moving_sprites(self):
        return self.get_sprites()

    def get_shadow_sprite(self):
        return spriteref.medium_shadow

    def get_sprite_offset(self):
        return (0, constants.CELLSIZE // 5)

    def get_shadow_offset(self):
        return (0, 0)

    def get_bar_offset(self):
        return (0, 0)

    def can_xflip(self):
        return True

    def get_map_identifier(self):
        return ("m", colors.RED)

    def get_name(self):
        return self._name

    def get_level_range(self):
        return range(0, 64)

    def show_zees(self):
        return not self.is_inanimate()

    def is_inanimate(self):
        return EnemyTypes.INANIMATE in self.get_types()

    def get_stats(self):
        base_stats = {
            StatTypes.VIT: 3,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1,
            StatTypes.SUMMONING_SICKNESS_ON_SUMMON: 4,
            StatTypes.FLINCH_RESIST: 1
        }
        overrides = self.get_stat_overrides()
        base_stats.update(overrides)

        return stats.BasicStatLookup(base_stats)

    def get_stat_overrides(self):
        """Subclasses can override this to provide their template's custom stats.
            :returns: map: StatType -> int value
        """
        return {}

    def get_spawn_items(self, level, randval=None):
        yield

    def get_controller(self):
        from src.game.gameengine import EnemyController
        return EnemyController()

    def get_idle_anim_rate(self):
        return 4

    def get_moving_anim_rate(self):
        return 2


class WebTemplate(EnemyTemplate):

    """Essentially just a wall that can be broken down."""

    def __init__(self):
        EnemyTemplate.__init__(self, "Web")

    def get_sprites(self):
        return spriteref.enemy_web_all

    def get_map_identifier(self):
        return ("w", colors.RED)

    def get_types(self):
        return [EnemyTypes.INANIMATE]

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 4,
            StatTypes.DEF: 0,
            StatTypes.SPEED: 1,
            StatTypes.INTELLIGENCE: 0,
            StatTypes.WEALTH: 0
        }

    def get_controller(self):
        import src.game.gameengine as gameengine
        return gameengine.NullController(silent=True)

class CaveCrawlerTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Crawler")

    def get_sprites(self):
        return spriteref.enemy_cave_crawler_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_level_range(self):
        return range(1, 3)

    def get_map_identifier(self):
        return ("c", colors.RED)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 8,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1,
            StatTypes.THROW_AFFINITY: 1
        }

    def get_spawn_items(self, level, randval=None):
        yield itemgen.WeaponItemFactory.gen_item(level, item.ItemTypes.DAGGER_WEAPON)


class SmallFrogTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Frog")

    def get_sprites(self):
        return spriteref.enemy_frog_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_map_identifier(self):
        return ("f", colors.RED)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 6,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1
        }

    def get_level_range(self):
        return range(0, 5)


class TrilliteTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trillite")

    def get_sprites(self):
        return spriteref.enemy_small_trilla_all

    def get_types(self):
        return [EnemyTypes.ANIMAL, EnemyTypes.MASKED]

    def get_map_identifier(self):
        return ("t", colors.RED)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 10,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1
        }

    def get_level_range(self):
        return range(5, 11)


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trilla")

    def get_sprites(self):
        return spriteref.enemy_trilla_all

    def get_types(self):
        return [EnemyTypes.ANIMAL, EnemyTypes.MASKED]

    def get_map_identifier(self):
        return ("T", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 16,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3
        }

    def get_level_range(self):
        return range(8, 11)


class SporeTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Spore")

    def get_sprites(self):
        return spriteref.enemy_spore_all

    def get_types(self):
        return [EnemyTypes.FUNGUS]

    def get_map_identifier(self):
        return ("s", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.small_shadow

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 12,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1,
            StatTypes.CONFUSION_ON_HIT: 3,
            StatTypes.UNFLINCHING: 1
        }

    def get_level_range(self):
        return range(8, 13)


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Small Muncher"
        EnemyTemplate.__init__(self, name)

    def get_sprites(self):
        return spriteref.enemy_muncher_small_alt_all if self._is_alt else spriteref.enemy_muncher_small_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_map_identifier(self):
        return ("m", colors.RED)

    def get_level_range(self):
        return range(2, 5)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 8,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1,  # wealth 1 because they're guaranteed to have a potion
            StatTypes.POTION_AFFINITY: 2
        }

    def get_spawn_items(self, level, randval=None):
        yield itemgen.PotionItemFactory.gen_item(level, template=itemgen.HEALING)


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Muncher"
        EnemyTemplate.__init__(self, name)

    def get_sprites(self):
        return spriteref.enemy_muncher_alt_all if self._is_alt else spriteref.enemy_muncher_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_map_identifier(self):
        return ("M", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(10, 14)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 30,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 8,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3,
        }

    def get_spawn_items(self, level, randval=None):
        yield itemgen.PotionItemFactory.gen_item(level, template=itemgen.MAJOR_HEALING)


class SlugTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Slug")

    def get_sprites(self):
        return spriteref.enemy_slug_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_map_identifier(self):
        return ("S", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(5, 8)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 20,
            StatTypes.SPEED: 1,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 6,
            StatTypes.DEF: 6,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.SLOW_ON_HIT: 3,
            StatTypes.WEALTH: 2
        }


class WitchTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Witch")

    def get_sprites(self):
        return spriteref.enemy_witch_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_shadow_sprite(self):
        return spriteref.medium_shadow

    def get_map_identifier(self):
        return ("W", colors.RED)

    def get_level_range(self):
        return range(12, 16)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 25,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 3,
            StatTypes.DEF: 5,
            StatTypes.INTELLIGENCE: 4,
            StatTypes.WEALTH: 1,
            StatTypes.POTION_AFFINITY: 3
        }

    def get_spawn_items(self, level, randval=None):
        n_potions = 1
        for _ in range(0, n_potions):
            templates_to_use = itemgen.PotionTemplates.all_templates(level)
            if len(templates_to_use) > n_potions:
                templates_to_use = random.choices(templates_to_use, k=n_potions)

            for t in templates_to_use:
                potion = itemgen.PotionItemFactory.gen_item(level, t)
                if potion is not None:
                    yield potion


class GiantTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Giant")

    def get_sprites(self):
        return spriteref.enemy_giant_all

    def get_types(self):
        return [EnemyTypes.UNDEAD]

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("G", colors.RED)

    def get_level_range(self):
        return range(12, 16)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 28,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 6,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.HP_REGEN: 2,
            StatTypes.WEALTH: 4,
            StatTypes.UNSWAPPABLE: 1,
        }


class CrabTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Crab")

    def get_sprites(self):
        return spriteref.enemy_crab_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("c", colors.RED)

    def get_shadow_offset(self):
        return (0, -constants.CELLSIZE // 16)

    def get_level_range(self):
        return range(4, 7)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 16,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1,
            StatTypes.GRASP_ON_MELEE_HIT: 1
        }


class CyclopsTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cyclops")

    def get_sprites(self):
        return spriteref.enemy_cyclops_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_map_identifier(self):
        return ("C", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(6, 10)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 15,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.FLINCH_ON_HIT: 1,
        }


# TODO these suck, consider deleting
class DicelTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Dicel")

    def get_sprites(self):
        return spriteref.enemy_dicel_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_level_range(self):
        return range(4, 7)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 12,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1
        }


class GhastTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Ghast")

    def get_sprites(self):
        return spriteref.enemy_ghast_all

    def get_types(self):
        return [EnemyTypes.ANIMAL]

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("g", colors.RED)

    def get_level_range(self):
        return range(4, 8)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 9,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.UNARMED_IS_PROJECTILE: 1
        }


class ScorpionTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wanderer")

    def get_sprites(self):
        return spriteref.enemy_scorpion_all

    def get_types(self):
        return [EnemyTypes.UNDEAD]

    def get_map_identifier(self):
        return ("w", colors.RED)

    def get_level_range(self):
        return range(9, 14)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 18,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.POISON_ON_HIT: 4,
        }


class WraithTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wraith")

    def get_sprites(self):
        return spriteref.enemy_wraith_all

    def get_types(self):
        return [EnemyTypes.UNDEAD]

    def get_map_identifier(self):
        return ("W", colors.RED)

    def get_level_range(self):
        return range(11, 16)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 25,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 6,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.UNARMED_RANGE: 3,
            StatTypes.UNARMED_IS_PROJECTILE: 1,
            StatTypes.CONFUSION_ON_HIT: 5,
            StatTypes.SWAP_ON_HIT: 1,
        }


# TODO - not currently used
class FungoiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Fungal Bundle")

    def get_sprites(self):
        return spriteref.enemy_fungoi_all

    def get_types(self):
        return [EnemyTypes.FUNGUS]

    def get_level_range(self):
        return range(10, 15)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 10,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2
        }


class OysterTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Oyster")

    def get_sprites(self):
        return spriteref.enemy_oyster_all

    def get_types(self):
        return [EnemyTypes.FUNGUS]

    def get_level_range(self):
        return range(13, 16)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 18,
            StatTypes.SPEED: 6,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 5,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.BLINDNESS_ON_HIT: 6,
            StatTypes.UNFLINCHING: 1,
        }

    def get_map_identifier(self):
        return ("O", colors.RED)


# TODO these suck so bad that i'm starting to miss the snowman
class SkulkerTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Skulker")

    def get_sprites(self):
        return spriteref.enemy_skullwalker

    def get_types(self):
        return [EnemyTypes.UNDEAD]

    def get_level_range(self):
        return range(9, 12)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 20,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.DEF: 4,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.CHILL_ON_HIT: 3,
            StatTypes.POTION_AFFINITY: 1,
        }

    def get_map_identifier(self):
        return ("S", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.medium_shadow


class FrogBossTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Beast")

    def get_sprites(self):
        return spriteref.Bosses.frog_idle_1

    def get_moving_sprites(self):
        return spriteref.Bosses.frog_idle_2

    def get_types(self):
        return [EnemyTypes.ANIMAL, EnemyTypes.BOSS]

    def get_map_identifier(self):
        return ("F", colors.RED)

    def get_shadow_offset(self):
        return (0, -constants.CELLSIZE // 8)

    def get_shadow_sprite(self):
        return spriteref.enormous_shadow

    def get_level_range(self):
        return [7]

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 30,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 6,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3,
            StatTypes.FLINCH_RESIST: 3,
        }


class RoboTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "B.O.S.S.")

    def get_sprites(self):
        return spriteref.Bosses.robo_idle

    def get_types(self):
        return [EnemyTypes.UNDEAD, EnemyTypes.BOSS]

    def get_map_identifier(self):
        return ("S", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.enormous_shadow

    def get_level_range(self):
        return [11]

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 40,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 7,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 10,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 5,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.UNARMED_IS_PROJECTILE: 1,
            StatTypes.UNFLINCHING: 1,
        }


class HuskTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Husk")

    def get_sprites(self):
        return spriteref.enemy_husk_idle_all

    def get_types(self):
        return [EnemyTypes.UNDEAD, EnemyTypes.ANIMAL]

    def get_moving_sprites(self):
        return spriteref.enemy_husk_moving_all

    def get_map_identifier(self):
        return ("h", colors.RED)

    def get_level_range(self):
        return [15]

    def get_stat_overrides(self):
        player_base_stats = stats.default_player_stats()

        return {
            StatTypes.VIT: player_base_stats.stat_value(StatTypes.VIT),
            StatTypes.SPEED: player_base_stats.stat_value(StatTypes.SPEED),
            StatTypes.ATT: player_base_stats.stat_value(StatTypes.ATT),
            StatTypes.UNARMED_ATT: player_base_stats.stat_value(StatTypes.UNARMED_ATT),
            StatTypes.DEF: player_base_stats.stat_value(StatTypes.DEF),
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 0,  # no item farming off these guys
        }


class InfectedHuskTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Infected Husk")

    def get_sprites(self):
        return spriteref.Bosses.infected_husk_idle

    def get_types(self):
        return [EnemyTypes.UNDEAD, EnemyTypes.ANIMAL, EnemyTypes.FUNGUS]

    def get_map_identifier(self):
        return ("h", colors.RED)

    def get_level_range(self):
        return [15]

    def get_stat_overrides(self):
        player_base_stats = stats.default_player_stats()

        return {
            StatTypes.VIT: player_base_stats.stat_value(StatTypes.VIT) * 2,
            StatTypes.SPEED: player_base_stats.stat_value(StatTypes.SPEED),
            StatTypes.ATT: player_base_stats.stat_value(StatTypes.ATT),
            StatTypes.UNARMED_ATT: player_base_stats.stat_value(StatTypes.UNARMED_ATT) * 2,
            StatTypes.DEF: player_base_stats.stat_value(StatTypes.DEF) + 2,

            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 0,
        }


class CrawlingLepiotaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Lepiota")

    def get_sprites(self):
        return spriteref.enemy_crawling_lepiota

    def get_types(self):
        return [EnemyTypes.FUNGUS]

    def get_map_identifier(self):
        return ("L", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(15, 20)

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 35,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 5,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3,
            StatTypes.GRASP_ON_MELEE_HIT: 2,
            StatTypes.UNFLINCHING: 1
        }


class SpiderBossTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Halfling Spider")

    def get_sprites(self):
        return spriteref.Bosses.spider_idle

    def get_types(self):
        return [EnemyTypes.ANIMAL, EnemyTypes.BOSS]

    def get_map_identifier(self):
        return ("H", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return [3]

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 24,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 3,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 2,
        }


class MedusaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Medusa")

    def get_sprites(self):
        return spriteref.Bosses.medusa_idle

    def get_types(self):
        return [EnemyTypes.FUNGUS, EnemyTypes.BOSS]

    def get_map_identifier(self):
        return ("?", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return []  # special enemy

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 50,
            StatTypes.SPEED: 8,  # sorry..
            StatTypes.ATT: 6,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.UNFLINCHING: 1,
            StatTypes.WEALTH: 3,
        }

    def get_idle_anim_rate(self):
        return 8

    def get_moving_anim_rate(self):
        return 8


class CaveHorrorTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Colossal Horror")

    def get_sprites(self):
        return spriteref.CaveHorror.cave_horror_idle

    def get_types(self):
        return [EnemyTypes.FUNGUS]

    def get_map_identifier(self):
        return ("H", colors.RED)

    def _limb_length(self):
        return 96  # dist from base of its body to the bottom of the sprite

    def get_sprite_offset(self):
        return (0, self._limb_length())

    def get_bar_offset(self):
        return (0, -self._limb_length())

    def can_xflip(self):
        # the directional shadows on its face look weird flipping back and forth
        return False

    def get_shadow_sprite(self):
        return None

    def get_level_range(self):
        return [15]

    def get_stat_overrides(self):
        return {
            StatTypes.VIT: 80,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 10,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 6,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 6,
            StatTypes.LIGHT_LEVEL: 2,  # so it stays visible
            StatTypes.SUMMONING_SICKNESS_ON_SUMMON: 4,
            StatTypes.UNSWAPPABLE: 1,  # would be tragic if this thing moved
            StatTypes.FLINCH_RESIST: 3,
        }

    def get_controller(self):
        import src.game.gameengine as gameengine
        return gameengine.NullController()


# regular enemies
TEMPLATE_TRILLA = TrillaTemplate()
TEMPLATE_TRILLITE = TrilliteTemplate()
TEMPLATE_CAVE_CRAWLER = CaveCrawlerTemplate()
TEMPLATE_MUNCHER = MuncherTemplate(alt=False)
TEMPLATE_MUNCHER_ALT = MuncherTemplate(alt=True)
TEMPLATE_MUNCHER_SMALL = SmallMuncherTemplate(alt=False)
TEMPLATE_MUNCHER_SMALL_ALT = SmallMuncherTemplate(alt=True)
TEMPLATE_CYCLOPS = CyclopsTemplate()
TEMPLATE_DICEL = DicelTemplate()
TEMPLATE_WRAITH = WraithTemplate()
TEMPLATE_FUNGOI = FungoiTemplate()
TEMPLATE_SCORPION = ScorpionTemplate()
TEMPLATE_SMALL_FROG = SmallFrogTemplate()
TEMPLATE_GHAST = GhastTemplate()
TEMPLATE_SPORE = SporeTemplate()
TEMPLATE_SLUG = SlugTemplate()
TEMPLATE_GIANT = GiantTemplate()
TEMPLATE_CRAB = CrabTemplate()
TEMPLATE_WITCH = WitchTemplate()
TEMPLATE_OYSTER = OysterTemplate()
TEMPLATE_HUSK = HuskTemplate()
TEMPLATE_SKULKER = SkulkerTemplate()
TEMPLATE_LEPIOTA = CrawlingLepiotaTemplate()
TEMPLATE_INFECTED_HUSK = InfectedHuskTemplate()
TEMPLATE_WEB = WebTemplate()

# bosses
TEMPLATE_SPIDER = SpiderBossTemplate()
TEMPLATE_FROG = FrogBossTemplate()
TEMPLATE_ROBO = RoboTemplate()
TEMPLATE_CAVE_HORROR = CaveHorrorTemplate()
TEMPLATE_MEDUSA = MedusaTemplate()

RAND_SPAWN_TEMPLATES = [TEMPLATE_MUNCHER_SMALL,
                        TEMPLATE_MUNCHER,
                        TEMPLATE_WRAITH,
                        TEMPLATE_CYCLOPS,
                        TEMPLATE_SPORE,
                        TEMPLATE_CRAB,
                        TEMPLATE_CAVE_CRAWLER,
                        TEMPLATE_SLUG,
                        TEMPLATE_TRILLA,
                        TEMPLATE_TRILLITE,
                        TEMPLATE_SKULKER,
                        TEMPLATE_FROG,
                        TEMPLATE_SMALL_FROG,
                        TEMPLATE_SCORPION,
                        TEMPLATE_GHAST,
                        TEMPLATE_GIANT,
                        TEMPLATE_WITCH,
                        TEMPLATE_OYSTER,
                        TEMPLATE_LEPIOTA,
                        TEMPLATE_INFECTED_HUSK]


def get_all_rand_spawn_templates(level=None, cond=None):
    res = []
    for template in RAND_SPAWN_TEMPLATES:
        if level is not None:
            lvl_range = template.get_level_range()
            if level not in lvl_range:
                continue

        if cond is not None:
            if not cond(template):
                continue

        res.append(template)

    return res


class EnemyFactory:

    @staticmethod
    def get_state(template, level):
        inv = inventory.InventoryState()

        for spawn_item in template.get_spawn_items(level, randval=random.random()):
            if spawn_item is not None:
                inv.add_to_inv(spawn_item)

        stat_lookup = template.get_stats()
        wealth = stat_lookup.stat_value(StatTypes.WEALTH)
        for _ in range(0, wealth):
            if random.random() < balance.ENEMY_ITEM_CHANCE_PER_WEALTH:
                loot_item = itemgen.ItemFactory.gen_item(level, item_type=None)
                if loot_item is not None:
                    inv.add_to_inv(loot_item)

        import src.game.gameengine as gameengine
        a_state = gameengine.ActorState(template.get_name(), level, stat_lookup, inv, 1, False)
        a_state.set_energy(0 if random.random() < 0.5 else 4)

        return a_state

    @staticmethod
    def gen_enemy(template, level, controller=None):
        return EnemyFactory.gen_enemies(template, level, n=1, controller=controller)[0]

    @staticmethod
    def gen_enemies(template, level, n=1, controller=None):
        if template is None:
            valid_templates = get_all_rand_spawn_templates(level=level)
            if len(valid_templates) == 0:
                template = TEMPLATE_CAVE_CRAWLER
                print("WARN: no valid enemy templates for level {}, falling back to {}s".format(
                    level, template.get_name()))
            else:
                # TODO - weights on the enemy types?
                template = random.choice(valid_templates)

        res = []
        for _ in range(0, n):
            res.append(Enemy(0, 0, EnemyFactory.get_state(template, level), template.get_sprites(),
                             template.get_map_identifier(),
                             controller if controller is not None else template.get_controller(),
                             idle_anim_rate=template.get_idle_anim_rate(),
                             moving_anim_rate=template.get_moving_anim_rate(),
                             sprite_offset=template.get_sprite_offset(),
                             shadow_sprite=template.get_shadow_sprite(),
                             shadow_offset=template.get_shadow_offset(),
                             bar_offset=template.get_bar_offset(),
                             can_xflip=template.can_xflip(),
                             moving_sprites=template.get_moving_sprites(),
                             show_zees=template.show_zees(),
                             enemy_types=template.get_types()))

        return res


if __name__ == "__main__":

    print("INFO: #  BASIC SPAWN RANGES  #\n")
    for i in range(0, 16):
        line = "{}:\t".format(i)
        temps = [t for t in RAND_SPAWN_TEMPLATES if i in t.get_level_range()]
        temps.sort(key=lambda t: t.get_level_range()[0])
        line = line + "[" + ", ".join([t.get_name() for t in temps]) + "]"
        print("INFO: {}".format(line))

    import src.worldgen.zones as zones
    zones.init_zones()

    print("\n\nINFO: #  STORY SPAWN RANGES  #\n")
    for story_id in zones.all_storyline_zone_ids():
        z = zones.get_zone(story_id)
        if z.is_boss_zone():
            print("INFO: {}:\t~BOSS ZONE~".format(z.get_level()))
        else:
            i = z.get_level()
            line = "{}:\t".format(i)
            temps = [t for t in RAND_SPAWN_TEMPLATES if i in t.get_level_range()]
            temps.sort(key=lambda t: t.get_level_range()[0])
            line = line + "[" + ", ".join([t.get_name() for t in temps]) + "]"

            if z.get_file() is not None:
                print("INFO: {} (FROM FILE)".format(line))
            else:
                print("INFO: {}".format(line))

