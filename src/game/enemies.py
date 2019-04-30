import random

import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.droprates import EnemyRates
from src.game.stats import StatType
import src.game.stats as stats
from src.game.loot import LootFactory
from src.utils.util import Utils
import src.game.gameengine as gameengine
import src.game.inventory as inventory
import src.items.item as item


NUM_EXTRA_STATS_RANGE = [
    stats._exp_map(64, 1, 3),
    stats._exp_map(64, 2, 7)
]

STATS_MULTIPLIER_RANGE = [stats._exp_map(64, 1, 3, integral=False),
                          stats._exp_map(64, 1.5, 6, integral=False)]

ENEMY_STATS = [StatType.ATT,
               StatType.DEF,
               StatType.VIT,
]

TRUE_BASE_STATS = {
    StatType.ATT: 10,
    StatType.DEF: 10,
    StatType.VIT: 10,
}


for stat in ENEMY_STATS:
    if stat not in TRUE_BASE_STATS:
        TRUE_BASE_STATS[stat] = 0


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

    def get_pathfinding(self):
        return PathfindingType.BASIC_CHASE

    def get_level_range(self):
        return (0, 64)

    def get_attack(self):
        return None

    def get_lunges(self):
        return False

    def drops_loot(self):
        return True

    def get_base_stats(self):
        return dict(TRUE_BASE_STATS)

    def special_death_action(self, level, entity, world):
        pass

    def get_possible_special_attacks(self):
        return []

    def show_death_explosion(self):
        return True

    def increment_kill_count_on_death(self):
        return True

    def can_attack(self):
        return True


class FlappumTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Flappum", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_flappum_all

    def get_lunges(self):
        return True


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trilla", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_trilla_all

    def get_base_stats(self):
        base_stats = EnemyTemplate.get_base_stats(self)
        return base_stats

    def drops_loot(self):
        return False


class TrilliteTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trillite", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_small_trilla_all


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Muncher"
        EnemyTemplate.__init__(self, name, spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_small_alt_all if self._is_alt else spriteref.enemy_muncher_small_all

    def get_pathfinding(self):
        return PathfindingType.BASIC_CHASE

    def get_base_stats(self):
        base_stats = EnemyTemplate.get_base_stats(self)
        return base_stats

    def drops_loot(self):
        return False

    def show_death_explosion(self):
        return False

    def increment_kill_count_on_death(self):
        return False


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Muncher"
        EnemyTemplate.__init__(self, name, spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_muncher_alt_all if self._is_alt else spriteref.enemy_muncher_all

    def get_lunges(self):
        return True


class CycloiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cycloi", spriteref.large_shadow)

    def get_sprites(self):
        return spriteref.enemy_cyclops_all

    def get_lunges(self):
        return True

    def get_pathfinding(self):
        return PathfindingType.BASIC_CUT_OFF

    def get_base_stats(self):
        base_stats = EnemyTemplate.get_base_stats(self)
        base_stats[StatType.DEF] += 15

        return base_stats


class DicelTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Dicel", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_dicel_all


class FallenTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "The Fallen", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_the_fallen_all


class FungoiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Fungoi", spriteref.medium_shadow)

    def get_sprites(self):
        return spriteref.enemy_fungoi_all


class FrogBoss(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cave Beast", spriteref.enormous_shadow)
        print("my_sprites={}".format(self.get_sprites()))

    def get_sprites(self):
        return spriteref.Bosses.frog_idle_1

    def get_base_stats(self):
        base_stats = EnemyTemplate.get_base_stats(self)
        base_stats[StatType.DEF] += 15
        base_stats[StatType.VIT] += 35
        base_stats[StatType.ATT] += 5

        return base_stats

    def get_possible_special_attacks(self):
        return []


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
                        TEMPLATE_MUNCHER_SMALL_ALT,
                        TEMPLATE_DICEL,
                        TEMPLATE_THE_FALLEN,
                        TEMPLATE_CYCLOI,
                        TEMPLATE_FLAPPUM,
                        TEMPLATE_TRILLA]

EASY_CAVE_ENEMIES = [TEMPLATE_FLAPPUM]
HARDER_CAVE_ENEMIES = EASY_CAVE_ENEMIES + [TEMPLATE_MUNCHER_SMALL]

FOREST_ENEMIES = [TEMPLATE_FLAPPUM, TEMPLATE_MUNCHER_SMALL_ALT, TEMPLATE_FUNGOI]
HARDER_FOREST_ENEMIES = FOREST_ENEMIES + [TEMPLATE_THE_FALLEN]


def get_rand_template_for_level(level, rand_val):
    choices = []
    for template in RAND_SPAWN_TEMPLATES:
        lvl_range = template.get_level_range()
        if lvl_range[0] <= level <= lvl_range[1]:
            choices.append(template)

    return choices[int(rand_val * len(choices))]


class EnemyFactory:

    @staticmethod
    def get_state(template, level):
        inv = inventory.FakeInventoryState()

        item_type = random.choice(item.ItemTypes.all_types())
        loot_item = item.ItemFactory.gen_item(level, item_type)
        inv.add_to_inv(loot_item)

        return gameengine.ActorStateNew(template.get_name(), level, template.get_base_stats(), inv, 1)

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



