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


class EnemyTemplate:

    def __init__(self, name):
        self._name = name

    def get_sprites(self):
        return spriteref.player_idle_arms_up_all

    def get_shadow_sprite(self):
        return spriteref.medium_shadow

    def get_projectile_sprite(self):
        return None

    def get_sprite_offset(self):
        return (0, 0)

    def get_shadow_offset(self):
        return (0, 0)

    def get_map_identifier(self):
        return ("m", colors.RED)

    def get_name(self):
        return self._name

    def get_level_range(self):
        return range(0, 64)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 3,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1,
        })

    def get_controller(self):
        from src.game.gameengine import EnemyController
        return EnemyController()

    def is_always_updating(self):
        return False


class CaveCrawlerTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Crawler")

    def get_sprites(self):
        return spriteref.enemy_cave_crawler_all

    def get_level_range(self):
        return range(1, 3)

    def get_map_identifier(self):
        return ("c", colors.RED)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 8,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1,
            StatTypes.THROW_AFFINITY: 1
        })


class SmallFrogTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Frog")

    def get_sprites(self):
        return spriteref.enemy_frog_all

    def get_map_identifier(self):
        return ("f", colors.RED)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 6,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1
        })

    def get_level_range(self):
        return range(0, 5)


class TrilliteTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trillite")

    def get_sprites(self):
        return spriteref.enemy_small_trilla_all

    def get_map_identifier(self):
        return ("t", colors.RED)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 10,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1
        })

    def get_level_range(self):
        return range(5, 8)


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trilla")

    def get_sprites(self):
        return spriteref.enemy_trilla_all

    def get_map_identifier(self):
        return ("T", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 16,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3
        })

    def get_level_range(self):
        return range(8, 11)


class SporeTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Spore")

    def get_sprites(self):
        return spriteref.enemy_spore_all

    def get_map_identifier(self):
        return ("s", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.small_shadow

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1,
            StatTypes.CONFUSION_ON_HIT: 1
        })

    def get_level_range(self):
        return range(8, 13)


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Small Muncher"
        EnemyTemplate.__init__(self, name)

    def get_sprites(self):
        return spriteref.enemy_muncher_small_alt_all if self._is_alt else spriteref.enemy_muncher_small_all

    def get_map_identifier(self):
        return ("m", colors.RED)

    def get_level_range(self):
        return range(2, 5)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 2
        })


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Muncher"
        EnemyTemplate.__init__(self, name)

    def get_sprites(self):
        return spriteref.enemy_muncher_alt_all if self._is_alt else spriteref.enemy_muncher_all

    def get_map_identifier(self):
        return ("M", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(10, 14)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 20,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 8,
            StatTypes.DEF: 6,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3
        })


class SlugTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Slug")

    def get_sprites(self):
        return spriteref.enemy_slug_all

    def get_map_identifier(self):
        return ("S", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(5, 8)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 20,
            StatTypes.SPEED: 1,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 6,
            StatTypes.DEF: 6,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.SLOW_ON_HIT: 3,
            StatTypes.WEALTH: 2
        })


class WitchTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Witch")

    def get_sprites(self):
        return spriteref.enemy_witch_all

    def get_shadow_sprite(self):
        return spriteref.medium_shadow

    def get_map_identifier(self):
        return ("W", colors.RED)

    def get_level_range(self):
        return range(12, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 15,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 3,
            StatTypes.DEF: 5,
            StatTypes.INTELLIGENCE: 4,
            StatTypes.WEALTH: 3,
            StatTypes.POTION_AFFINITY: 2
        })


class GiantTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Putrid Host")

    def get_sprites(self):
        return spriteref.enemy_giant_all

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("G", colors.RED)

    def get_level_range(self):
        return range(12, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 28,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 6,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.HP_REGEN: 2,
            StatTypes.WEALTH: 4
        })


class CrabTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Crab")

    def get_sprites(self):
        return spriteref.enemy_crab_all

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("c", colors.RED)

    def get_shadow_offset(self):
        return (0, -5)

    def get_level_range(self):
        return range(4, 7)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 16,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 3,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1,
            StatTypes.GRASP_ON_MELEE_HIT: 2,
        })


class CyclopsTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cyclops")

    def get_sprites(self):
        return spriteref.enemy_cyclops_all

    def get_map_identifier(self):
        return ("C", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return range(6, 10)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 10,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2
        })


# TODO these suck, consider deleting
class DicelTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Dicel")

    def get_sprites(self):
        return spriteref.enemy_dicel_all

    def get_level_range(self):
        return range(4, 7)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1
        })


class GhastTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Ghast")

    def get_sprites(self):
        return spriteref.enemy_ghast_all

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_map_identifier(self):
        return ("g", colors.RED)

    def get_level_range(self):
        return range(4, 8)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.UNARMED_IS_PROJECTILE: 1
        })

    def get_projectile_sprite(self):
        return spriteref.Items.projectile_small


class ScorpionTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wanderer")

    def get_sprites(self):
        return spriteref.enemy_scorpion_all

    def get_map_identifier(self):
        return ("w", colors.RED)

    def get_level_range(self):
        return range(9, 14)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 3,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.POISON_ON_HIT: 2,
            StatTypes.GRASP_ON_MELEE_HIT: 1,
        })


class WraithTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wraith")

    def get_sprites(self):
        return spriteref.enemy_wraith_all

    def get_map_identifier(self):
        return ("W", colors.RED)

    def get_level_range(self):
        return range(11, 16)

    def get_projectile_sprite(self):
        return spriteref.Items.projectile_small

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 16,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2,
            StatTypes.UNARMED_RANGE: 3,
            StatTypes.UNARMED_IS_PROJECTILE: 1,
            StatTypes.CONFUSION_ON_HIT: 5
        })


# TODO - not currently used
class FungoiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Fungal Bundle")

    def get_sprites(self):
        return spriteref.enemy_fungoi_all

    def get_level_range(self):
        return range(10, 15)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 10,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2
        })


class OysterTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Screeching Oyster")

    def get_sprites(self):
        return spriteref.enemy_oyster_all

    def get_level_range(self):
        return range(13, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 6,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 5,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.BLINDNESS_ON_HIT: 3
        })

    def get_map_identifier(self):
        return ("O", colors.RED)


class FrogBossTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Beast")

    def get_sprites(self):
        return spriteref.Bosses.frog_idle_1

    def get_map_identifier(self):
        return ("F", colors.RED)

    def get_sprite_offset(self):
        return (0, 8)

    def get_shadow_offset(self):
        return (0, -4)

    def get_shadow_sprite(self):
        return spriteref.enormous_shadow

    def get_level_range(self):
        return [7]

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 30,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 6,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 3
        })


class RoboTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "S.K.U.L.")

    def get_sprites(self):
        return spriteref.Bosses.robo_idle

    def get_map_identifier(self):
        return ("S", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.enormous_shadow

    def get_level_range(self):
        return [11]

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 40,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 7,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 10,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 5,
            StatTypes.UNARMED_RANGE: 2,
            StatTypes.UNARMED_IS_PROJECTILE: 1
        })


class NamelessTemplate(EnemyTemplate):

    def __init__(self, invincible):
        EnemyTemplate.__init__(self, "???")
        self._invincible = invincible

    def get_sprites(self):
        return spriteref.Bosses.nameless_idle

    def get_map_identifier(self):
        return ("?", colors.RED)

    def get_shadow_sprite(self):
        return spriteref.large_shadow

    def get_level_range(self):
        return []  # special enemy

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 999 if self._invincible else 60,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 99 if self._invincible else 8,
            StatTypes.DEF: 99 if self._invincible else 5,
            StatTypes.INTELLIGENCE: 5,
            StatTypes.SUPER_PATHING: 1,
            StatTypes.NULLIFICATION: 1 if self._invincible else 0,
            StatTypes.WEALTH: 0,
        })

    def is_always_updating(self):
        return self._invincible


class CaveHorrorTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Horror")

    def get_sprites(self):
        return spriteref.Bosses.cave_horror_idle

    def get_map_identifier(self):
        return ("H", colors.RED)

    def get_sprite_offset(self):
        return (0, 148 + 32)

    def get_shadow_sprite(self):
        return None

    def get_level_range(self):
        return [15]

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 60,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 10,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 16,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 6
        })

    def get_controller(self):
        import src.game.gameengine as gameengine

        class _CaveHorrorController(gameengine.ActorController):

            def get_next_action(self, actor, world):
                pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
                return gameengine.SkipTurnAction(actor, pos)

        return _CaveHorrorController()


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
TEMPLATE_NAMELESS = NamelessTemplate(False)
TEMPLATE_NAMELESS_INVINCIBLE = NamelessTemplate(True)

# bosses
TEMPLATE_FROG = FrogBossTemplate()
TEMPLATE_ROBO = RoboTemplate()
TEMPLATE_CAVE_HORROR = CaveHorrorTemplate()

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
                        TEMPLATE_FROG,
                        TEMPLATE_SMALL_FROG,
                        TEMPLATE_SCORPION,
                        TEMPLATE_GHAST,
                        TEMPLATE_GIANT,
                        TEMPLATE_WITCH,
                        TEMPLATE_OYSTER]


def get_rand_template_for_level(level, rand_val):
    choices = []
    for template in RAND_SPAWN_TEMPLATES:
        lvl_range = template.get_level_range()
        if level in lvl_range:
            choices.append(template)

    if len(choices) == 0:
        print("WARN: no enemy templates for level: {}".format(level))
        return TEMPLATE_CAVE_CRAWLER
    else:
        return choices[int(rand_val * len(choices))]


class EnemyFactory:

    @staticmethod
    def get_state(template, level):
        inv = inventory.InventoryState()

        wealth = template.get_base_stats().stat_value(StatTypes.WEALTH)
        for _ in range(0, wealth):
            if random.random() < balance.ENEMY_ITEM_CHANCE_PER_WEALTH:
                loot_item = itemgen.ItemFactory.gen_item(level, item_type=None)
                if loot_item is not None:
                    inv.add_to_inv(loot_item)

        # spawn with one random, unique potion per potion_affinity point.
        potion_affinity = template.get_base_stats().stat_value(StatTypes.POTION_AFFINITY)
        for _ in range(0, potion_affinity):
            templates_to_use = itemgen.PotionTemplates.all_templates(level)
            if len(templates_to_use) > potion_affinity:
                templates_to_use = random.choices(templates_to_use, k=potion_affinity)

            for t in templates_to_use:
                potion = itemgen.PotionItemFactory.gen_item(level, t)
                if potion is not None:
                    inv.add_to_inv(potion)

        # gets a free dagger if it can throw them
        if template.get_base_stats().stat_value(StatTypes.THROW_AFFINITY) > 0:
            dagger = itemgen.WeaponItemFactory.gen_item(level, item.ItemTypes.DAGGER_WEAPON)
            inv.add_to_inv(dagger)

        import src.game.gameengine as gameengine
        a_state = gameengine.ActorState(template.get_name(), level, template.get_base_stats(), inv, 1)
        a_state.set_energy(0 if random.random() < 0.5 else 4)
        a_state.unarmed_projectile_sprite = template.get_projectile_sprite()

        return a_state

    @staticmethod
    def gen_enemy(template, level):
        return EnemyFactory.gen_enemies(template, level, n=1)[0]

    @staticmethod
    def gen_enemies(template, level, n=1):
        template = template if template is not None else get_rand_template_for_level(level, random.random())

        res = []
        for _ in range(0, n):
            res.append(Enemy(0, 0, EnemyFactory.get_state(template, level), template.get_sprites(), template.get_map_identifier(), template.get_controller(),
                             sprite_offset=template.get_sprite_offset(),
                             shadow_sprite=template.get_shadow_sprite(),
                             shadow_offset=template.get_shadow_offset()))

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
            print("INFO: BOSS ZONE")
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

