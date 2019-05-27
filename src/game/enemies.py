import random

import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.droprates import EnemyRates
from src.game.stats import StatTypes
import src.game.stats as stats
from src.game.loot import LootFactory
from src.utils.util import Utils
import src.game.inventory as inventory
import src.items.item as item


class EnemyTemplate:

    def __init__(self, name, shadow_sprite):
        self._name = name
        self._shadow_sprite = shadow_sprite

    def get_sprites(self):
        return spriteref.player_idle_arms_up_all

    def get_shadow_sprite(self):
        return self._shadow_sprite

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
            StatTypes.DEF: 1
        })


class FlappumTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Crawler", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_flappum_all

    def get_level_range(self):
        return range(0, 4)


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Masked Adult", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_trilla_all

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 6,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 2,
            StatTypes.UNARMED_ATT: 0,
            StatTypes.DEF: 1
        })

    def get_level_range(self):
        return range(6, 16)


class TrilliteTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Masked Child", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_small_trilla_all

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 2,
            StatTypes.SPEED: 4,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 1,
            StatTypes.DEF: 1
        })

    def get_level_range(self):
        return range(0, 6)


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Small Muncher"
        EnemyTemplate.__init__(self, name, spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_small_alt_all if self._is_alt else spriteref.enemy_muncher_small_all

    def get_level_range(self):
        return range(10, 16)

    def get_base_stats(self):
        return stats.BasicStatLookup({
            StatTypes.VIT: 2,
            StatTypes.SPEED: 3,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 2,
            StatTypes.DEF: 1
        })


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Muncher"
        EnemyTemplate.__init__(self, name, spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_alt_all if self._is_alt else spriteref.enemy_muncher_all

    def get_level_range(self):
        return range(10, 16)


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
            StatTypes.SPEED: 6,
            StatTypes.ATT: 0,
            StatTypes.UNARMED_ATT: 6,
            StatTypes.DEF: 2
        })


# TODO these suck, consider deleting
class DicelTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Dicel", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_dicel_all

    def get_level_range(self):
        return ()


class FallenTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "The Fallen", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_the_fallen_all

    def get_level_range(self):
        return range(14, 16)


# TODO - these also suck really bad
class FungoiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Fungoi", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_fungoi_all

    def get_level_range(self):
        return ()


class FrogBoss(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Beast", spriteref.enormous_shadow)
        print("my_sprites={}".format(self.get_sprites()))

    def get_sprites(self):
        return spriteref.Bosses.frog_idle_1

    def get_base_stats(self):
        return EnemyTemplate.get_base_stats(self)

    def get_level_range(self):
        return ()


TEMPLATE_TRILLA = TrillaTemplate()
TEMPLATE_TRILLITE = TrilliteTemplate()
TEMPLATE_FLAPPUM = FlappumTemplate()
TEMPLATE_MUNCHER = MuncherTemplate(alt=False)
TEMPLATE_MUNCHER_ALT = MuncherTemplate(alt=True)
TEMPLATE_MUNCHER_SMALL = SmallMuncherTemplate(alt=False)
TEMPLATE_MUNCHER_SMALL_ALT = SmallMuncherTemplate(alt=True)
TEMPLATE_CYCLOI = CycloiTemplate()
TEMPLATE_DICEL = DicelTemplate()
TEMPLATE_THE_FALLEN = FallenTemplate()
TEMPLATE_FUNGOI = FungoiTemplate()

TEMPLATE_FROG_BOSS = FrogBoss()

RAND_SPAWN_TEMPLATES = [TEMPLATE_MUNCHER_SMALL,
                        TEMPLATE_MUNCHER,
                        TEMPLATE_DICEL,
                        TEMPLATE_THE_FALLEN,
                        TEMPLATE_CYCLOI,
                        TEMPLATE_FLAPPUM,
                        TEMPLATE_TRILLA,
                        TEMPLATE_TRILLITE]

EASY_CAVE_ENEMIES = [TEMPLATE_FLAPPUM]
HARDER_CAVE_ENEMIES = EASY_CAVE_ENEMIES + [TEMPLATE_MUNCHER_SMALL]

FOREST_ENEMIES = [TEMPLATE_FLAPPUM, TEMPLATE_MUNCHER_SMALL_ALT, TEMPLATE_FUNGOI]
HARDER_FOREST_ENEMIES = FOREST_ENEMIES + [TEMPLATE_THE_FALLEN]


def get_rand_template_for_level(level, rand_val):
    choices = []
    for template in RAND_SPAWN_TEMPLATES:
        lvl_range = template.get_level_range()
        if level in lvl_range:
            choices.append(template)

    if len(choices) == 0:
        print("WARN: no enemy templates for level: {}".format(level))
        return TEMPLATE_FLAPPUM
    else:
        return choices[int(rand_val * len(choices))]


class EnemyFactory:

    @staticmethod
    def get_state(template, level):
        inv = inventory.FakeInventoryState()

        item_type = random.choice(item.ItemTypes.all_types())
        loot_item = item.ItemFactory.gen_item(level, item_type)
        inv.add_to_inv(loot_item)

        import src.game.gameengine as gameengine
        a_state = gameengine.ActorState(template.get_name(), level, template.get_base_stats(), inv, 1)
        a_state.set_energy(0 if random.random() < 0.5 else 4)

        return a_state

    @staticmethod
    def gen_enemy(template, level):
        return EnemyFactory.gen_enemies(template, level, n=1)[0]

    @staticmethod
    def gen_enemies(template, level, n=1):
        template = template if template is not None else get_rand_template_for_level(level, random.random())

        res = []
        for _ in range(0, n):
            res.append(Enemy(0, 0, EnemyFactory.get_state(template, level), template.get_sprites()))
        return res



