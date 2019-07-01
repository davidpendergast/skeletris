import os

_IS_DEV = os.path.exists("this_is_dev.txt")

# flip to toggle all debug settings
_DEBUG = False

# these flags can be manually flipped before launching to alter the game's behavior
_IGNORE_LOOT_LEVELS = True
_PLAYER_CANT_DIE = True


def is_dev():
    return _IS_DEV


def is_debug():
    return _DEBUG and is_dev()


def ignore_loot_levels():
    return is_debug() and _IGNORE_LOOT_LEVELS


def player_cant_die():
    return is_debug() and _PLAYER_CANT_DIE
