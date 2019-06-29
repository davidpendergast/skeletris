import random

import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.stats import StatTypes
import src.game.stats as stats
import src.game.inventory as inventory
import src.items.item as item
import src.items.itemgen as itemgen
import src.game.balance as balance


class EnemyTemplate:

    def __init__(self, name, shadow_sprite):
        self._name = name
        self._shadow_sprite = shadow_sprite

    def get_sprites(self):
        return spriteref.player_idle_arms_up_all

    def get_shadow_sprite(self):
        return self._shadow_sprite

    def get_projectile_sprite(self):
        return None

    def get_sprite_offset(self):
        return (0, 0)

    def get_shadow_offset(self):
        return (0, 0)

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
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1,
        })


class CaveCrawlerTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Crawler", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_cave_crawler_all

    def get_level_range(self):
        return range(1, 3)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 6,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 0,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1
        })


class SmallFrogTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Frog", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_frog_all

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 3,
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
        EnemyTemplate.__init__(self, "Mask", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_small_trilla_all

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 8,
            StatTypes.SPEED: 6,
            StatTypes.ATT: 1,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 1,
            StatTypes.INTELLIGENCE: 1,
            StatTypes.WEALTH: 1
        })

    def get_level_range(self):
        return range(5, 9)


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Multi-Mask", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_trilla_all

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 12,
            StatTypes.SPEED: 8,
            StatTypes.ATT: 2,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1
        })

    def get_level_range(self):
        return range(9, 16)


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Small Muncher"
        EnemyTemplate.__init__(self, name, spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_small_alt_all if self._is_alt else spriteref.enemy_muncher_small_all

    def get_level_range(self):
        return range(2, 5)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 8,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 1
        })


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Muncher"
        EnemyTemplate.__init__(self, name, spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_alt_all if self._is_alt else spriteref.enemy_muncher_all

    def get_level_range(self):
        return range(10, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 16,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 8,
            StatTypes.DEF: 6,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 1
        })


class CycloiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cyclops", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_cyclops_all

    def get_level_range(self):
        return range(6, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 10,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 6,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 3,
            StatTypes.WEALTH: 2
        })


# TODO these suck, consider deleting
class DicelTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Dicel", spriteref.medium_shadow)

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
        EnemyTemplate.__init__(self, "Ghast", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_ghast_all

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
            StatTypes.UNARMED_RANGE: 2
        })

    def get_projectile_sprite(self):
        return spriteref.Items.projectile_small


class ScorpionTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wanderer", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_scorpion_all

    def get_level_range(self):
        return range(9, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 8,
            StatTypes.SPEED: 6,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 2,
            StatTypes.INTELLIGENCE: 4,
            StatTypes.WEALTH: 2
            # StatTypes.LIGHT_LEVEL: 1,  # TODO - can't yet, "slows down" game when these guys are offscreen but nearby
        })


class FallenTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Wraith", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_the_fallen_all

    def get_level_range(self):
        return range(8, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 16,
            StatTypes.SPEED: 2,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 4,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 5,
            StatTypes.WEALTH: 2
        })


class FungoiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Fungal Bundle", spriteref.medium_shadow)

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


class FrogTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Beast", spriteref.enormous_shadow)

    def get_sprites(self):
        return spriteref.Bosses.frog_idle_1

    def get_sprite_offset(self):
        return (0, 8)

    def get_shadow_offset(self):
        return (0, -4)

    def get_shadow_sprite(self):
        return spriteref.enormous_shadow

    def get_level_range(self):
        return range(7, 8)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 15,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 2,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 4,
            StatTypes.INTELLIGENCE: 2,
            StatTypes.WEALTH: 3
        })


TEMPLATE_TRILLA = TrillaTemplate()
TEMPLATE_TRILLITE = TrilliteTemplate()
TEMPLATE_CAVE_CRAWLER = CaveCrawlerTemplate()
TEMPLATE_MUNCHER = MuncherTemplate(alt=False)
TEMPLATE_MUNCHER_ALT = MuncherTemplate(alt=True)
TEMPLATE_MUNCHER_SMALL = SmallMuncherTemplate(alt=False)
TEMPLATE_MUNCHER_SMALL_ALT = SmallMuncherTemplate(alt=True)
TEMPLATE_CYCLOI = CycloiTemplate()
TEMPLATE_DICEL = DicelTemplate()
TEMPLATE_THE_FALLEN = FallenTemplate()
TEMPLATE_FUNGOI = FungoiTemplate()
TEMPLATE_FROG = FrogTemplate()
TEMPLATE_SCORPION = ScorpionTemplate()
TEMPLATE_SMALL_FROG = SmallFrogTemplate()
TEMPLATE_GHAST = GhastTemplate()

RAND_SPAWN_TEMPLATES = [TEMPLATE_MUNCHER_SMALL,
                        TEMPLATE_MUNCHER,
                        # TEMPLATE_DICEL,
                        TEMPLATE_THE_FALLEN,
                        TEMPLATE_CYCLOI,
                        TEMPLATE_CAVE_CRAWLER,
                        TEMPLATE_TRILLA,
                        TEMPLATE_TRILLITE,
                        TEMPLATE_FROG,
                        TEMPLATE_SMALL_FROG,
                        TEMPLATE_FUNGOI,
                        TEMPLATE_SCORPION,
                        TEMPLATE_GHAST]


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
        inv = inventory.FakeInventoryState()

        wealth = template.get_base_stats().stat_value(StatTypes.WEALTH)

        for _ in range(0, wealth):
            if random.random() < balance.ENEMY_ITEM_CHANCE_PER_WEALTH:
                loot_item = itemgen.ItemFactory.gen_item(level, item_type=None)
                if loot_item is not None:
                    inv.add_to_inv(loot_item)

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
            res.append(Enemy(0, 0, EnemyFactory.get_state(template, level), template.get_sprites(),
                             sprite_offset=template.get_sprite_offset(),
                             shadow_sprite=template.get_shadow_sprite(),
                             shadow_offset=template.get_shadow_offset()))

        return res


if __name__ == "__main__":
    print("INFO: enemy spawn ranges:")
    for i in range(0, 16):
        line = "{}:\t".format(i)
        temps = [t for t in RAND_SPAWN_TEMPLATES if i in t.get_level_range()]
        line = line + "[" + ", ".join([t.get_name() for t in temps]) + "]"
        print("INFO: {}".format(line))


