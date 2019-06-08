import os

_IS_DEV = os.path.exists("this_is_dev.txt")

# flip to enable / disable the following debug settings
_DEBUG = True

# these flags can be manually flipped before launching to alter the game's behavior
_IGNORE_LEVEL_RESTRICTIONS_ON_DROPS = True
_PLAYER_CANT_DIE = False


def is_dev():
    return _IS_DEV


def is_debug():
    return _DEBUG and is_dev()


def ignore_level_restrictions_on_drops():
    return is_debug() and _IGNORE_LEVEL_RESTRICTIONS_ON_DROPS


def player_cant_die():
    return is_debug() and _PLAYER_CANT_DIE
