import math

import src.utils.colors as colors


class StatType:

    def __init__(self, stat_id, color=colors.LIGHT_GRAY, desc=None, local_desc=None):
        self._stat_id = stat_id
        self._color = color
        self._desc = desc
        self._local_desc = local_desc

    def get_color(self):
        return self._color

    def get_id(self):
        return self._stat_id

    def __repr__(self):
        return str(self.get_id())

    def is_hidden(self, local=False):
        if local:
            return self._local_desc is None
        else:
            return self._desc is None

    def get_description(self, value, local=False):
        if not local:
            if self._desc is None:
                return "{}: {}".format(self.get_id(), value)
            else:
                return self._desc.format(value)
        else:
            if self._local_desc is None:
                return "{}: {} (local)".format(self.get_id(), value)
            else:
                return self._local_desc.format(value)

    def __eq__(self, other):
        if isinstance(other, StatType):
            return self.get_id() == other.get_id()
        else:
            return False

    def __hash__(self):
        return hash(self.get_id())


class StatTypes:
    ATT = StatType("ATT", color=colors.RED, desc="+{} to All Attacks")
    DEF = StatType("DEF", color=colors.BLUE, desc="+{} Defense")
    VIT = StatType("VIT", color=colors.GREEN, desc="+{} Vitality")
    SPEED = StatType("SPEED", color=colors.YELLOW, desc="+{} Speed")

    UNARMED_ATT = StatType("UNARMED_ATT", color=colors.RED, desc="+{} to Unarmed Attacks")
    MIN_LIGHT_LEVEL = StatType("MIN_LIGHT_LEVEL")
    LIGHT_LEVEL = StatType("LIGHT_LEVEL", desc="+{} Light Level")

    ENERGY_DRAIN = StatType("ENERGY_DRAIN", desc="+{} Energy Drain on Hit",
                            local_desc="Drains +{} Energy on Hit")


class StatProvider:

    def stat_value(self, stat_type, local=False):
        return 0


def default_player_stats():
    return BasicStatLookup({
        StatTypes.ATT: 0,
        StatTypes.VIT: 8,
        StatTypes.DEF: 1,
        StatTypes.UNARMED_ATT: 2,
        StatTypes.LIGHT_LEVEL: 4,
        StatTypes.MIN_LIGHT_LEVEL: 2,
        StatTypes.SPEED: 4
    })


class BasicStatLookup(StatProvider):

    def __init__(self, lookup_dict):
        self.lookup = lookup_dict

    def stat_value(self, stat_type, local=False):
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
        StatTypes.ATT: PRIMARY_RANGES,
        StatTypes.DEF: PRIMARY_RANGES,
        StatTypes.VIT: PRIMARY_RANGES,
    }

    @staticmethod
    def get_range(stat_type, lvl):
        return (ItemStatRanges.RANGES[stat_type][0][lvl],
                ItemStatRanges.RANGES[stat_type][1][lvl])
