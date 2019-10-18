from src.game.stats import StatProvider, BasicStatLookup
from src.game.stats import StatTypes
from src.items.item import AppliedStat
import src.utils.colors as colors
import src.game.spriteref as spriteref
import src.game.balance as balance

_UNIQUE_KEY = 0


def _new_unique_key():
    global _UNIQUE_KEY
    _UNIQUE_KEY += 1
    return _UNIQUE_KEY - 1


class StatusEffect(StatProvider):

    def __init__(self, name, duration, color, icon, applied_stats, unique_key=None, player_text=None,
                 ignore_nullification=False, is_debuff=False, circle_art_type=None):
        self.name = name
        self.duration = duration
        self.color = color
        self.circle_art_type = circle_art_type
        self.icon = icon
        self.applied_stats = applied_stats
        self.player_text = player_text
        self._ignore_nullifcation = ignore_nullification
        self._is_debuff = is_debuff
        self.unique_key = unique_key if unique_key is not None else _new_unique_key()

    def stat_value(self, stat_type, local=False):
        res = 0
        for stat in self.all_applied_stats():
            if stat.stat_type == stat_type and stat.local == local:
                res += stat.value
        return res

    def set_stat_value(self, stat_type, val):
        raise ValueError("can't change stat values of a StatusEffect after the fact.")

    def get_player_text(self):
        """returns: dialog that's shown when the player becomes afflicted with this status."""
        return self.player_text

    def all_applied_stats(self):
        return self.applied_stats

    def is_debuff(self):
        return self._is_debuff

    def ignores_nullification(self):
        return self._ignore_nullifcation

    def get_name(self):
        return self.name

    def get_duration(self):
        return self.duration

    def get_color(self):
        return self.color

    def get_effect_circle_art_type(self):
        return self.circle_art_type

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


def new_night_vision_effect(val, duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.LIGHT_LEVEL, val)]
    return StatusEffect("Night Vision", duration, StatTypes.LIGHT_LEVEL.get_color(),
                        spriteref.UI.status_eye_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=False,
                        circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)


def new_plus_defenses_effect(duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.DEF, balance.STATUS_EFFECT_PLUS_DEFENSE_VAL)]
    return StatusEffect("Increased Defenses", duration, StatTypes.DEF.get_color(),
                        spriteref.UI.status_shield_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=False,
                        circle_art_type=spriteref.EffectCircleTypes.FOUR_CIRCLES)


def new_regen_effect(val, duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.HP_REGEN, val)]
    return StatusEffect("Regeneration", duration, StatTypes.HP_REGEN.get_color(),
                        spriteref.UI.status_sparkles_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=False,
                        circle_art_type=spriteref.EffectCircleTypes.SHRINKING_CIRCLES)


def new_poison_effect(val, duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.POISON, val)]
    return StatusEffect("Poison", duration, StatTypes.POISON.get_color(),
                        spriteref.UI.status_drop_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)


def new_speed_effect(val, duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.SPEED, val)]
    return StatusEffect("Increased Speed", duration, StatTypes.SPEED.get_color(),
                        spriteref.UI.status_up_arrow_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=False,
                        circle_art_type=spriteref.EffectCircleTypes.SHRINKING_CIRCLES)


def new_slow_effect(val, duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.SPEED, -val)]
    return StatusEffect("Reduced Speed", duration, colors.DARK_YELLOW,
                        spriteref.UI.status_down_arrow_icon, stats, unique_key=unique_key,
                        player_text=player_text, is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.STAR_5_ENCLOSED)


def new_nullification_effect(duration, player_text=None, unique_key=None):
    stats = [AppliedStat(StatTypes.NULLIFICATION, 1)]
    return StatusEffect("Nullification", duration, colors.WHITE,
                        spriteref.UI.status_diagonal_lines_icon, stats,
                        player_text=player_text, unique_key=unique_key,
                        ignore_nullification=True, is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.GROWING_CIRCLES)


def new_confusion_effect(duration, player_text=None):
    stats = [AppliedStat(StatTypes.CONFUSION, 1)]
    return StatusEffect("Confusion", duration, colors.RED,
                        spriteref.UI.status_sparkles_icon, stats,
                        player_text=player_text, unique_key="confusion", is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)


def new_grasped_effect(duration, player_text=None):
    stats = [AppliedStat(StatTypes.GRASPED, 1)]
    return StatusEffect("Grasped", duration, colors.ORANGE,
                        spriteref.UI.status_hand_icon, stats,
                        player_text=player_text, unique_key="grasped", is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.SQUARE_VS_STAR)


def new_blindness_effect(duration, player_text=None):
    stats = [AppliedStat(StatTypes.LIGHT_LEVEL, -4)]
    return StatusEffect("Blindness", duration, colors.DARK_BLUE,
                        spriteref.UI.status_eye_xed_icon, stats,
                        player_text=player_text, unique_key="blinded", is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)


def new_flinch_effect(player_text=None):
    stats = [AppliedStat(StatTypes.FLINCHED, 1)]
    return StatusEffect("Flinched", 1, StatTypes.FLINCHED.get_color(),
                        spriteref.UI.status_x_icon, stats,
                        player_text=player_text, unique_key="flinched", is_debuff=True,
                        ignore_nullification=True,
                        circle_art_type=spriteref.EffectCircleTypes.SQUARE_VS_STAR)


def new_flinch_recovery_effect(duration, player_text=None):
    stats = [AppliedStat(StatTypes.UNFLINCHING, 1)]
    return StatusEffect("Unflinching", duration, StatTypes.UNFLINCHING.get_color(),
                        spriteref.UI.status_x_icon, stats,
                        player_text=player_text, unique_key="unflinching", is_debuff=False,
                        ignore_nullification=True)


def new_chilled_effect(duration, val, player_text=None):
    stats = [AppliedStat(StatTypes.SPEED, -val),
             AppliedStat(StatTypes.ATT, -val),
             AppliedStat(StatTypes.DEF, val)]
    return StatusEffect("Chilled", duration, StatTypes.CHILL_ON_HIT.get_color(),
                        spriteref.UI.status_snowflake_icon, stats, player_text=player_text,
                        unique_key="chilled", is_debuff=True,
                        circle_art_type=spriteref.EffectCircleTypes.STAR_5_ENCLOSED)


def new_summoning_sickness_effect(duration, player_text=None):
    stats = [AppliedStat(StatTypes.SUMMONING_SICKNESS, 1)]
    return StatusEffect("Summoning Sickness", duration, StatTypes.SUMMONING_SICKNESS.get_color(),
                        spriteref.UI.status_skull_icon, stats,
                        player_text=player_text, unique_key="summoning_sickness",
                        is_debuff=True)
