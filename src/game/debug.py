import os

_IS_DEV = os.path.exists("this_is_dev.txt")

# these flags can be manually flipped before launching to alter the game's behavior
_DEBUG = True
_IGNORE_LEVEL_RESTRICTIONS_ON_CHEST_DROPS = True


def is_dev():
    return _IS_DEV


def is_debug():
    return _DEBUG and is_dev()


def ignore_level_restrictions_on_chest_drops():
    return is_debug() and _IGNORE_LEVEL_RESTRICTIONS_ON_CHEST_DROPS
