import random
import src.game.spriteref as spriteref
from src.world.entities import Enemy
from src.game.actorstate import EnemyState
from src.game.stats import StatType
import src.game.stats as stats

NUM_EXTRA_STATS_RANGE = [
    stats._exp_map(64, 1, 3),
    stats._exp_map(64, 2, 7)
]

STATS_MULTIPLIER_RANGE = [stats._exp_map(64, 1, 3, integral=False),
                          stats._exp_map(64, 1.5, 6, integral=False)]

ENEMY_STATS = [StatType.ATT,
               StatType.DEF,
               StatType.VIT,
               StatType.ATTACK_RADIUS,
               StatType.ATTACK_SPEED,
               StatType.MOVEMENT_SPEED,
               StatType.DODGE,
               StatType.ACCURACY,
               StatType.LIFE_REGEN,
               StatType.MAX_HEALTH
]


class EnemyFactory:

    @staticmethod
    def gen_enemy(level):
        i = int(random.random() * len(spriteref.enemies_all))
        enemy_stats = {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10
        }

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

        state = EnemyState("enem1", spriteref.enemies_all[i], level, enemy_stats)

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

