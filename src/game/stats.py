import math

from enum import Enum


class StatType(str, Enum):
    ATT = "ATT",                    # +ATT to *all* attacks
    DEF = "DEF",
    VIT = "VIT",
    SPEED = "SPEED"

    LOCAL_ATT = "LOCAL_ATT"         # +ATT with *this* item
    UNARMED_ATT = "UNARMED_ATT"     # +ATT with no item
    MIN_LIGHT_LEVEL = "MIN_LIGHT_LEVEL"
    LIGHT_LEVEL = "LIGHT_LEVEL"


class StatProvider:

    def stat_value(self, stat_type):
        return 0


def default_player_stats():
    return BasicStatLookup({
        StatType.ATT: 0,
        StatType.VIT: 8,
        StatType.DEF: 1,
        StatType.UNARMED_ATT: 2,
        StatType.LIGHT_LEVEL: 5,
        StatType.MIN_LIGHT_LEVEL: 2,
        StatType.SPEED: 4
    })


class BasicStatLookup(StatProvider):

    def __init__(self, lookup_dict):
        self.lookup = lookup_dict

    def stat_value(self, stat_type):
        if stat_type in self.lookup:
            return self.lookup[stat_type]
        else:
            return 0

    def set_stat_value(self, stat_type, val):
        self.lookup[stat_type] = val


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


MIN_LVL_PRIMARY_RANGE = [3, 7]
MAX_LVL_PRIMARY_RANGE = [22, 32]

PRIMARY_RANGES = (_exp_map(64, MIN_LVL_PRIMARY_RANGE[0], MAX_LVL_PRIMARY_RANGE[0]),
                    _exp_map(64, MIN_LVL_PRIMARY_RANGE[1], MAX_LVL_PRIMARY_RANGE[1]))

MIN_LVL_PCNT_RANGE = [5, 9]
MAX_LVL_PCNT_RANGE = [18, 25]

PCNT_RANGES = (_exp_map(64, MIN_LVL_PCNT_RANGE[0], MAX_LVL_PCNT_RANGE[0]),
                _exp_map(64, MIN_LVL_PCNT_RANGE[1], MAX_LVL_PCNT_RANGE[1]))

MOVE_SPEED_RANGE = (_exp_map(64, 5, 15), _exp_map(64, 12, 18))
SECONDARY_RANGES = (_exp_map(64, 6, 44), _exp_map(64, 14, 64))

LIFE_ON_HIT_RANGE = (_exp_map(64, 1, 6), _exp_map(64, 3, 16))
LIFE_REGEN_RANGE = (_exp_map(64, 1, 5), _exp_map(64, 7, 35))
LIFE_LEECH_RANGE = (_exp_map(64, 1, 2), _exp_map(64, 2, 4))


class ItemStatRanges:
    RANGES = {
        StatType.ATT: PRIMARY_RANGES,
        StatType.DEF: PRIMARY_RANGES,
        StatType.VIT: PRIMARY_RANGES,
    }

    @staticmethod
    def get_range(stat_type, lvl):
        return (ItemStatRanges.RANGES[stat_type][0][lvl],
                ItemStatRanges.RANGES[stat_type][1][lvl])
