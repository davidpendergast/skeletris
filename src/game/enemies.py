import random

import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.actorstate import EnemyState, PathfindingType
import src.game.bosses as bosses
from src.game.droprates import EnemyRates
from src.game.stats import StatType
import src.game.stats as stats
import src.attacks.attacks as attacks
from src.game.loot import LootFactory
from src.utils.util import Utils


NUM_EXTRA_STATS_RANGE = [
    stats._exp_map(64, 1, 3),
    stats._exp_map(64, 2, 7)
]

STATS_MULTIPLIER_RANGE = [stats._exp_map(64, 1, 3, integral=False),
                          stats._exp_map(64, 1.5, 6, integral=False)]

ENEMY_STATS = [StatType.ATT,
               StatType.DEF,
               StatType.VIT,
               StatType.ATTACK_DAMAGE,
               StatType.ATTACK_RADIUS,
               StatType.ATTACK_SPEED,
               StatType.MOVEMENT_SPEED,
               StatType.DODGE,
               StatType.ACCURACY,
               # StatType.LIFE_REGEN,  # probably too OP
               StatType.MAX_HEALTH
]

TRUE_BASE_STATS = {
    StatType.ATT: 10,
    StatType.DEF: 10,
    StatType.VIT: 10,
    StatType.MOVEMENT_SPEED: -35,
    StatType.ATTACK_RADIUS: -25
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
        return attacks.TOUCH_ATTACK

    def get_lunges(self):
        return False

    def get_loot(self, level):
        return LootFactory.gen_loot(level)

    def get_base_stats(self):
        return dict(TRUE_BASE_STATS)

    def special_death_action(self, level, entity, world):
        pass

    def get_possible_special_attacks(self):
        return attacks.ALL_SPECIAL_ATTACKS

    def show_death_explosion(self):
        return True

    def increment_kill_count_on_death(self):
        return True

    def can_attack(self):
        return True

    def get_hurtbox(self):
        return 5


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
        base_stats[StatType.MOVEMENT_SPEED] += 20
        return base_stats

    def special_death_action(self, level, entity, world):
        base_stats = entity.state.get_base_stats()

        att_dmg = base_stats[StatType.ATTACK_DAMAGE]
        hp_bonus = base_stats[StatType.MAX_HEALTH]

        base_stats[StatType.ATTACK_DAMAGE] = max(-90, att_dmg - 35)
        base_stats[StatType.MAX_HEALTH] = max(-90, hp_bonus - 50)
        base_stats[StatType.MOVEMENT_SPEED] += 10

        pos = entity.center()
        for _ in range(0, 3):
            e_state = EnemyState(TEMPLATE_TRILLITE, level, dict(base_stats))
            # kind of a hack to get them to scoot outwards lol
            e_state.dmg_color = (1, 1, 1)
            e_state.took_damage_x_ticks_ago = 0
            e_state.set_color_x_ticks_ago = 0
            e_state.push(Utils.rand_vec(3), 15)
            e_state.set_special_attack(entity.state.special_attack)
            world.add(Enemy(pos[0], pos[1], e_state))

    def get_loot(self, level):
        return []


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
        base_stats[StatType.MOVEMENT_SPEED] -= 35
        base_stats[StatType.VIT] = 1  # one hit kill
        base_stats[StatType.LIFE_ON_HIT] = -4  # transforms upon successful attack
        return base_stats

    def special_death_action(self, level, entity, world):
        base_stats = entity.state.get_base_stats()

        base_stats[StatType.VIT] = EnemyTemplate.get_base_stats(self)[StatType.VIT]
        base_stats[StatType.ATTACK_DAMAGE] += 35
        base_stats[StatType.MOVEMENT_SPEED] += 65  # fast boys
        base_stats[StatType.LIFE_ON_HIT] += 4  # gotta undo the negative LoH

        template = TEMPLATE_MUNCHER_ALT if self._is_alt else TEMPLATE_MUNCHER
        e_state = EnemyState(template, level, dict(base_stats))
        e_state.set_special_attack(entity.state.special_attack)

        new_muncher = Enemy(0, 0, e_state)
        pos = entity.center()
        new_muncher.set_center(pos[0], pos[1])
        world.add(new_muncher)

    def get_loot(self, level):
        return []

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
        base_stats[StatType.MOVEMENT_SPEED] += 65
        base_stats[StatType.ATTACK_RADIUS] += 15

        return base_stats

    def get_possible_special_attacks(self):
        return []

    def get_hurtbox(self):
        return 15


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

TEMPLATE_FROG_BOSS = FrogBoss()

RAND_SPAWN_TEMPLATES = [TEMPLATE_MUNCHER_SMALL,
                        TEMPLATE_MUNCHER_SMALL_ALT,
                        TEMPLATE_DICEL,
                        TEMPLATE_THE_FALLEN,
                        TEMPLATE_CYCLOI,
                        TEMPLATE_FLAPPUM,
                        TEMPLATE_TRILLA]


def get_rand_template_for_level(level, rand_val):
    choices = []
    for template in RAND_SPAWN_TEMPLATES:
        lvl_range = template.get_level_range()
        if lvl_range[0] <= level <= lvl_range[1]:
            choices.append(template)

    return choices[int(rand_val * len(choices))]


class EnemyFactory:

    @staticmethod
    def get_state(template, level, stats):
        if template is TEMPLATE_FROG_BOSS:
            return bosses.FrogBossState(template, level, stats)
        else:
            return EnemyState(template, level, stats)

    @staticmethod
    def gen_enemy(level, force_template=None):
        if force_template is not None:
            template = force_template
        else:
            template = get_rand_template_for_level(level, random.random())

        enemy_stats = template.get_base_stats()

        n_extra = random.randint(NUM_EXTRA_STATS_RANGE[0][level], NUM_EXTRA_STATS_RANGE[1][level])

        for _ in range(0, n_extra):
            stat_type = ENEMY_STATS[int(random.random() * len(ENEMY_STATS))]
            mult_low, mult_high = STATS_MULTIPLIER_RANGE[0][level], STATS_MULTIPLIER_RANGE[1][level]
            mult = mult_low + random.random()*(mult_high - mult_low)
            value_low, value_high = stats.ItemStatRanges.get_range(stat_type, level)
            stat_value = int(mult * random.randint(value_low, value_high))
            if stat_type in enemy_stats:
                enemy_stats[stat_type] += stat_value
            else:
                enemy_stats[stat_type] = stat_value

        state = EnemyFactory.get_state(template, level, enemy_stats)

        if random.random() < EnemyRates.CHANCE_TO_HAVE_ATTACK:
            sp_atts = template.get_possible_special_attacks()
            if len(sp_atts) > 0:
                idx = int(random.random() * len(sp_atts))
                state.set_special_attack(sp_atts[idx])

        res = Enemy(0, 0, state)
        res.set_hurtbox(template.get_hurtbox())

        return res

    @staticmethod
    def gen_enemies(level, n=None):
        if n is None:
            n = int(1 + random.random()*4)

        first = EnemyFactory.gen_enemy(level)
        res = [first]
        for _ in range(1, n):
            res.append(Enemy(0, 0, first.state.duplicate()))

        return res

