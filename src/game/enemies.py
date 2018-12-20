import random
import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.actorstate import EnemyState, PathfindingType
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
               StatType.LIFE_REGEN,
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

    def __init__(self, name, sprites, shadow_sprite):
        self._name = name
        self._sprites = sprites
        self._shadow_sprite = shadow_sprite

    def get_sprites(self):
        return self._sprites

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

    def get_loot(self, level, potential_attack=None):
        return LootFactory.gen_loot(level, potential_attack=potential_attack)

    def get_base_stats(self):
        return dict(TRUE_BASE_STATS)

    def special_death_action(self, level, entity, world):
        pass

    def get_possible_special_attacks(self):
        return attacks.ALL_SPECIAL_ATTACKS

    def can_drop_special_attack(self):
        return True

    def show_death_explosion(self):
        return True

    def increment_kill_count_on_death(self):
        return True

    def can_attack(self):
        return True


class FlappumTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Flappum", spriteref.enemy_flappum_all, spriteref.medium_shadow)

    def get_lunges(self):
        return True


class TrillaTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Trilla", spriteref.enemy_trilla_all, spriteref.large_shadow)

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

    def can_drop_special_attack(self):
        return False

    def get_loot(self, level, potential_attack=None):
        return []


class SmallMuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Muncher"
        sprite = spriteref.enemy_muncher_small_alt_all if alt else spriteref.enemy_muncher_small_all
        EnemyTemplate.__init__(self, name, sprite, spriteref.medium_shadow)

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

    def can_drop_special_attack(self):
        return False

    def get_loot(self, level, potential_attack=None):
        return []

    def show_death_explosion(self):
        return False

    def increment_kill_count_on_death(self):
        return False


class MuncherTemplate(EnemyTemplate):

    def __init__(self, alt=False):
        self._is_alt = alt
        name = "Dark Muncher" if alt else "Muncher"
        sprite = spriteref.enemy_muncher_alt_all if alt else spriteref.enemy_muncher_all
        EnemyTemplate.__init__(self, name, sprite, spriteref.large_shadow)

    def get_lunges(self):
        return True


class CycloiTemplate(EnemyTemplate):

    def __init__(self):
        EnemyTemplate.__init__(self, "Cycloi", spriteref.enemy_cyclops_all, spriteref.large_shadow)

    def get_lunges(self):
        return True

    def get_pathfinding(self):
        return PathfindingType.BASIC_CUT_OFF

    def get_base_stats(self):
        base_stats = EnemyTemplate.get_base_stats(self)
        base_stats[StatType.DEF] += 15

        return base_stats


TEMPLATE_TRILLA = TrillaTemplate()
TEMPLATE_TRILLITE = EnemyTemplate("Trillite", spriteref.enemy_small_trilla_all, spriteref.medium_shadow)
TEMPLATE_FLAPPUM = FlappumTemplate()
TEMPLATE_MUNCHER = MuncherTemplate(alt=False)
TEMPLATE_MUNCHER_ALT = MuncherTemplate(alt=True)
TEMPLATE_MUNCHER_SMALL = SmallMuncherTemplate(alt=False)
TEMPLATE_MUNCHER_SMALL_ALT = SmallMuncherTemplate(alt=True)
TEMPLATE_CYCLOI = CycloiTemplate()

RAND_SPAWN_TEMPLATES = [TEMPLATE_MUNCHER_SMALL,
                        TEMPLATE_MUNCHER_SMALL_ALT,
                        EnemyTemplate("Dicel", spriteref.enemy_dicel_all, spriteref.medium_shadow),
                        EnemyTemplate("The Fallen", spriteref.enemy_the_fallen_all, spriteref.medium_shadow),
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
    def gen_enemy(level):
        template = get_rand_template_for_level(level, random.random())

        enemy_stats = template.get_base_stats()

        n_extra = random.randint(NUM_EXTRA_STATS_RANGE[0][level],
                                       NUM_EXTRA_STATS_RANGE[1][level])

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

        state = EnemyState(template, level, enemy_stats)

        if random.random() < EnemyRates.CHANCE_TO_HAVE_ATTACK:
            sp_atts = template.get_possible_special_attacks()
            if len(sp_atts) > 0:
                idx = int(random.random() * len(sp_atts))
                state.set_special_attack(sp_atts[idx])

        return Enemy(0, 0, state)

    @staticmethod
    def gen_enemies(level, n=None):
        if n is None:
            n = int(1 + random.random()*4)

        first = EnemyFactory.gen_enemy(level)
        res = [first]
        for _ in range(1, n):
            res.append(Enemy(0, 0, first.state.duplicate()))

        return res

