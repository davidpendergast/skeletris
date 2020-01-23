from src.game.stats import StatProvider, BasicStatLookup
from src.game.stats import StatTypes
from src.items.item import AppliedStat
import src.utils.colors as colors
import src.game.spriteref as spriteref
import src.game.balance as balance
import src.utils.util as util

_UNIQUE_KEY = 0


def _new_unique_key():
    global _UNIQUE_KEY
    _UNIQUE_KEY += 1
    return _UNIQUE_KEY - 1


class StatusEffectType(StatProvider):

    def __init__(self, name, color, icon, applied_stats, is_debuff=False, circle_art_type=None, blocked_by=None, bonus_text=None):
        """
        blocked_by: list of StatusEffectTypes that block this one.
        bonus_text: list of (str, color) that will shown in tooltips alongside the effect's stats.
        """
        self.name = name
        self.color = color
        self.circle_art_type = circle_art_type
        self.icon = icon
        self.applied_stats = applied_stats
        self._is_debuff = is_debuff

        # weakly-typed languages were a mistake
        if bonus_text is not None:
            if not isinstance(bonus_text, list):
                raise ValueError("Illegal value for bonus_text: {}".format(bonus_text))
            for t in bonus_text:
                if not isinstance(t, tuple) or not len(t) == 2:
                    raise ValueError("Illegal value for bonus_text: {}".format(bonus_text))

        self.bonus_text = [] if bonus_text is None else bonus_text

        if blocked_by is not None and not isinstance(blocked_by, list):
            raise ValueError("Illegal value for blocked_by: {}".format(blocked_by))

        self._blocked_by = [] if blocked_by is None else blocked_by

    def stat_value(self, stat_type, local=False):
        res = 0
        for stat in self.all_applied_stats():
            if stat.stat_type == stat_type and stat.local == local:
                res += stat.value
        return res

    def set_stat_value(self, stat_type, val):
        raise ValueError("can't change stat values of a StatusEffect after the fact.")

    def is_debuff(self):
        return self._is_debuff

    def is_blocked_by(self, other_type):
        return other_type in self._blocked_by

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_effect_circle_art_type(self):
        return self.circle_art_type

    def get_icon(self):
        return self.icon

    def all_bonus_text(self):
        return self.bonus_text

    def all_applied_stats(self):
        return self.applied_stats

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class StatusEffectTypes:

    NULLIFICATION = StatusEffectType("Nullification", colors.WHITE, spriteref.UI.status_diagonal_lines_icon,
                                     [AppliedStat(StatTypes.NULLIFICATION, 1)],
                                     is_debuff=True,
                                     circle_art_type=spriteref.EffectCircleTypes.GROWING_CIRCLES)

    PLUS_DEFENSES = StatusEffectType("Defense", StatTypes.DEF.get_color(), spriteref.UI.status_shield_icon,
                                     [AppliedStat(StatTypes.DEF, balance.STATUS_EFFECT_PLUS_DEFENSE_VAL)],
                                     is_debuff=False, blocked_by=[NULLIFICATION],
                                     circle_art_type=spriteref.EffectCircleTypes.FOUR_CIRCLES)

    HP_REGEN_1 = StatusEffectType("Regeneration", StatTypes.HP_REGEN.get_color(), spriteref.UI.status_sparkles_icon,
                                  [AppliedStat(StatTypes.HP_REGEN, balance.POTION_SMALL_HEAL_VAL)],
                                  is_debuff=False, blocked_by=[NULLIFICATION],
                                  circle_art_type=spriteref.EffectCircleTypes.SHRINKING_CIRCLES)

    HP_REGEN_2 = StatusEffectType("Regeneration II", StatTypes.HP_REGEN.get_color(), spriteref.UI.status_sparkles_icon,
                                  [AppliedStat(StatTypes.HP_REGEN, balance.POTION_MED_HEAL_VAL)],
                                  is_debuff=False, blocked_by=[NULLIFICATION],
                                  circle_art_type=spriteref.EffectCircleTypes.SHRINKING_CIRCLES)

    POISON = StatusEffectType("Poison", StatTypes.POISON.get_color(), spriteref.UI.status_drop_icon,
                              [AppliedStat(StatTypes.POISON, balance.POTION_POIS_VAL)],
                              is_debuff=True, blocked_by=[NULLIFICATION],
                              circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)

    SPEED = StatusEffectType("Speed", StatTypes.SPEED.get_color(), spriteref.UI.status_up_arrow_icon,
                             [AppliedStat(StatTypes.SPEED, balance.POTION_SPEED_VAL)],
                             is_debuff=False, blocked_by=[NULLIFICATION],
                             circle_art_type=spriteref.EffectCircleTypes.SHRINKING_CIRCLES)

    SLOWNESS = StatusEffectType("Slowness", colors.DARK_YELLOW, spriteref.UI.status_down_arrow_icon,
                                [AppliedStat(StatTypes.SPEED, -balance.POTION_SLOW_VAL)],
                                is_debuff=True, blocked_by=[NULLIFICATION],
                                circle_art_type=spriteref.EffectCircleTypes.STAR_5_ENCLOSED)

    CONFUSION = StatusEffectType("Confusion", colors.RED, spriteref.UI.status_sparkles_icon,
                                 [AppliedStat(StatTypes.CONFUSION, 1)],
                                 is_debuff=True, blocked_by=[NULLIFICATION],
                                 circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)

    GRASPED = StatusEffectType("Grasped", colors.ORANGE, spriteref.UI.status_hand_icon,
                               [AppliedStat(StatTypes.GRASPED, 1)],
                               is_debuff=True, blocked_by=[NULLIFICATION],
                               circle_art_type=spriteref.EffectCircleTypes.SQUARE_VS_STAR)

    NIGHT_VISION = StatusEffectType("Night Vision", StatTypes.LIGHT_LEVEL.get_color(), spriteref.UI.status_eye_icon,
                                    [AppliedStat(StatTypes.LIGHT_LEVEL, balance.POTION_NIGHT_VISION_VAL)],
                                    is_debuff=False, blocked_by=[NULLIFICATION],
                                    circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES,
                                    bonus_text=[("Prevents Blindness", StatTypes.LIGHT_LEVEL.get_color())])

    BLINDNESS = StatusEffectType("Blindness", colors.DARK_BLUE, spriteref.UI.status_eye_xed_icon,
                                 [AppliedStat(StatTypes.LIGHT_LEVEL, -4)],
                                 is_debuff=True, blocked_by=[NULLIFICATION, NIGHT_VISION],
                                 circle_art_type=spriteref.EffectCircleTypes.TRIANGLE_WITH_CIRCLES)

    SUMMON_SICKNESS = StatusEffectType("Summoning Sickness", StatTypes.SUMMONING_SICKNESS.get_color(), spriteref.UI.status_skull_icon,
                                       [AppliedStat(StatTypes.SUMMONING_SICKNESS, 1)],
                                       is_debuff=True, blocked_by=[NULLIFICATION])

    CHILLED = StatusEffectType("Chilled", StatTypes.CHILL_ON_HIT.get_color(), spriteref.UI.status_snowflake_icon,
                               [AppliedStat(StatTypes.SPEED, -2), AppliedStat(StatTypes.ATT, -2), AppliedStat(StatTypes.DEF, 2)],
                               is_debuff=True, blocked_by=[NULLIFICATION],
                               circle_art_type=spriteref.EffectCircleTypes.STAR_5_ENCLOSED)

    FLINCH_RESIST = StatusEffectType("Unflinching", StatTypes.UNFLINCHING.get_color(), spriteref.UI.status_x_icon,
                                     [AppliedStat(StatTypes.UNFLINCHING, 1)],
                                     is_debuff=False, blocked_by=[NULLIFICATION])

    FLINCHED = StatusEffectType("Flinched", StatTypes.FLINCHED.get_color(), spriteref.UI.status_x_icon,
                                [AppliedStat(StatTypes.FLINCHED, 1)],
                                is_debuff=True, blocked_by=[FLINCH_RESIST, NULLIFICATION],
                                circle_art_type=spriteref.EffectCircleTypes.SQUARE_VS_STAR)


def new_instant_heal_effect(val, name="Instant Heal"):
    return StatusEffectType(name, StatusEffectTypes.HP_REGEN_1.get_color(), StatusEffectTypes.HP_REGEN_1.get_icon(),
                            [AppliedStat(StatTypes.HP_REGEN, val)], is_debuff=False, blocked_by=[],
                            circle_art_type=StatusEffectTypes.HP_REGEN_1.get_effect_circle_art_type())
