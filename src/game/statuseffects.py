from src.game.stats import StatProvider, BasicStatLookup
from src.game.stats import StatTypes
import src.utils.colors as colors
import src.game.spriteref as spriteref

_UNIQUE_KEY = 0
def _new_unique_key():
    global _UNIQUE_KEY
    _UNIQUE_KEY += 1
    return _UNIQUE_KEY - 1


class StatusEffect(StatProvider):

    def __init__(self, name, duration, color, icon, stat_dict, unique_key=None):
        self.name = name
        self.duration = duration
        self.color = color
        self.icon = icon
        self.stat_lookup = BasicStatLookup(stat_dict)
        self.unique_key = unique_key if unique_key is not None else _new_unique_key()

    def stat_value(self, stat_type, local=False):
        return self.stat_lookup.stat_value(stat_type, local=local)

    def set_stat_value(self, stat_type, val):
        raise ValueError("can't change stat values of a StatusEffect after the fact.")

    def get_name(self):
        return self.name

    def get_duration(self):
        return self.duration

    def get_color(self):
        return self.color

    def get_icon(self):
        return self.icon

    def get_unique_key(self):
        return self.unique_key

    def __str__(self):
        return "{}({})".format(self.name, self.duration)

    def __eq__(self, other):
        if isinstance(other, StatusEffect):
            return self.unique_key == other.unique_key
        else:
            return False

    def __hash__(self):
        return hash(self.unique_key)


def new_night_vision_effect(val, duration):
    stats = {StatTypes.LIGHT_LEVEL: val}
    return StatusEffect("Night Vision", duration, colors.WHITE,
                        spriteref.status_eye_icon, stats, unique_key="vision")


def new_iron_defenses_effect(duration):
    stats = {StatTypes.DEF: 3}
    return StatusEffect("Iron Defenses", duration, colors.BLUE,
                        spriteref.status_shield_icon, stats, unique_key="shield_def_bonus")

