import os

_IS_DEV = None


def init():
    global _IS_DEV
    _IS_DEV = os.path.isfile("this_is_dev.txt")


def is_dev():
    if _IS_DEV is None:
        init()
    return _IS_DEV


def _lookup_val(setting, or_else):
    import src.game.globalstate as gs
    if not gs.is_initialized():
        return or_else
    else:
        return gs.get_instance().settings().get(setting)


def is_debug():
    import src.game.settings as settings
    return is_dev() and _lookup_val(settings.DebugSettings.DEBUG_ENABLED, False)


def ignore_loot_levels():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.IGNORE_LOOT_LEVELS, False)


def player_cant_die():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.PLAYER_CANT_DIE, False)


def insta_kill():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.INSTA_KILL, False)


def map_sees_all():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.MAP_SEES_ALL, False)


def holy_artifacts_100x_more_likely():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.HOLY_ARTIFACTS_100x_MORE_LIKELY, False)


def unlimited_trades():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.UNLIMITED_TRADES, False)


def never_show_tutorials():
    import src.game.settings as settings
    return is_debug() and _lookup_val(settings.DebugSettings.NEVER_SHOW_TUTORIALS, False)
