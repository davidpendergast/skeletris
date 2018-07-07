import math

from enum import Enum


class PlayerStatType(Enum):
    HP = "HP",
    DPS = "DPS",
    MOVESPEED = "MOVE_SPEED",
    ATTACK_RADIUS = "ATTACK_RADIUS",


class StatType(Enum):
    ATT = "ATT",
    DEF = "DEF",
    VIT = "VIT",
    ATTACK_RADIUS = "ATTACK_RADIUS",
    ATTACK_SPEED = "ATTACK_SPEED",
    ATTACK_DAMAGE = "ATTACK_DAMAGE",
    MOVEMENT_SPEED = "MOVEMENT_SPEED",
    DODGE = "DODGE",
    ACCURACY = "ACCURACY",
    LIFE_REGEN = "LIFE_REGEN",
    LIFE_ON_HIT = "LIFE_ON_HIT",
    LIFE_LEECH = "LIFE_LEECH",
    MAX_HEALTH = "MAX_HEALTH",
    POTION_HEALING = "POTION_HEALING",
    POTION_COOLDOWN = "POTION_COOLDOWN",

    HOLE_BONUS = "HOLE_BONUS"


def _exp_map(x1, y0, y1, intensity=0):
    """
        intensity: float in [0.0, 1.0). bigger = harsher slope near max
    """
    b = intensity
    a = (1 / x1) * math.log((y1 - y0*b) / (y0 * (1 - b)))
    return [round((y0 * b) + y0 * (1 - b) * math.exp(a * x)) for x in range(0, x1+1)]


def _linear_map(x1, y0, y1):
    return [round(y0 + (x / x1) * (y1 - y0)) for x in range(0, x1+1)]


MIN_LVL_PRIMARY_RANGE = [3, 7]
MAX_LVL_PRIMARY_RANGE = [22, 32]

PRIMARY_RANGES = (_exp_map(64, MIN_LVL_PRIMARY_RANGE[0], MAX_LVL_PRIMARY_RANGE[0]),
                    _exp_map(64, MIN_LVL_PRIMARY_RANGE[1], MAX_LVL_PRIMARY_RANGE[1]))

MIN_LVL_PCNT_RANGE = [1, 3]
MAX_LVL_PCNT_RANGE = [15, 25]

PCNT_RANGES = (_exp_map(64, MIN_LVL_PCNT_RANGE[0], MAX_LVL_PCNT_RANGE[0]),
                _exp_map(64, MIN_LVL_PCNT_RANGE[1], MAX_LVL_PCNT_RANGE[1]))

MOVE_SPEED_RANGE = (_exp_map(64, 5, 15), _exp_map(64, 12, 18))
SECONDARY_RANGES = (_exp_map(64, 6, 14), _exp_map(64, 44, 64))

LIFE_REGEN_RANGE = (_exp_map(64, 1, 5), _exp_map(64, 3, 22))
LIFE_LEECH_RANGE = (_exp_map(64, 1, 2), _exp_map(64, 2, 4))


class ItemStatRanges:
    RANGES = {
        StatType.ATT: PRIMARY_RANGES,
        StatType.DEF: PRIMARY_RANGES,
        StatType.VIT: PRIMARY_RANGES,

        StatType.ATTACK_RADIUS: PCNT_RANGES,
        StatType.ATTACK_SPEED: PCNT_RANGES,
        StatType.ATTACK_DAMAGE: PCNT_RANGES,
        StatType.MOVEMENT_SPEED: MOVE_SPEED_RANGE,
        StatType.DODGE: SECONDARY_RANGES,
        StatType.ACCURACY: SECONDARY_RANGES,
        StatType.LIFE_REGEN: LIFE_REGEN_RANGE,
        StatType.LIFE_ON_HIT: SECONDARY_RANGES,
        StatType.LIFE_LEECH: LIFE_LEECH_RANGE,
        StatType.MAX_HEALTH: PCNT_RANGES,
        StatType.POTION_HEALING: PCNT_RANGES,
        StatType.POTION_COOLDOWN: PCNT_RANGES
    }

    @staticmethod
    def get_range(stat_type, lvl):
        return (ItemStatRanges.RANGES[stat_type][0][lvl],
                ItemStatRanges.RANGES[stat_type][1][lvl])


if __name__ == "__main__":
    x1 = 64
    y0 = 7
    y1 = 64
    intensity = 0.0
    print("_exp_map({}, {}, {}) = {}".format(x1, y0, y1, _exp_map(x1, y0, y1, intensity=intensity)))
    intensity = 0.5
    print("_exp_map({}, {}, {}) = {}".format(x1, y0, y1, _exp_map(x1, y0, y1, intensity=intensity)))
    intensity = 0.99
    print("_exp_map({}, {}, {}) = {}".format(x1, y0, y1, _exp_map(x1, y0, y1, intensity=intensity)))

    print("_linear_map({}, {}, {}) = {}".format(x1, y0, y1, _linear_map(x1, y0, y1)))