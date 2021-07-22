import pygame
import os
from src.utils.util import Utils
import traceback


class Effects:
    DOOR_OPEN = Utils.resource_path(os.path.join("assets", "sounds", "door_open.ogg"))
    LOAD = Utils.resource_path(os.path.join("assets", "sounds", "load.ogg"))
    MISC_MENU_= Utils.resource_path(os.path.join("assets", "sounds", "misc_menu.ogg"))
    MISC_MENU_2 = Utils.resource_path(os.path.join("assets", "sounds", "misc_menu_2.ogg"))
    MISC_MENU_3 = Utils.resource_path(os.path.join("assets", "sounds", "misc_menu_3.ogg"))
    MISC_MENU_4 = Utils.resource_path(os.path.join("assets", "sounds", "misc_menu_4.ogg"))


_MASTER_VOLUME = 1.0

_LOADED_EFFECTS = {}  # effect_id -> Effect object

_RECENTLY_PLAYED = {}  # effect_id -> ticks since last play

RECENCY_LIMIT = 4  # if an effect was already played X ticks ago, don't play it again


def set_volume(volume):
    global _MASTER_VOLUME
    _MASTER_VOLUME = Utils.bound(volume, 0.0, 1.0)


def update():
    to_remove = []
    for effect in _RECENTLY_PLAYED:
        if _RECENTLY_PLAYED[effect] >= RECENCY_LIMIT:
            to_remove.append(effect)
        else:
            _RECENTLY_PLAYED[effect] = _RECENTLY_PLAYED[effect] + 1
    for effect in to_remove:
        del _RECENTLY_PLAYED[effect]


def play_sound(sound):
    """
    :param sound: either an effect_path, or a tuple (effect_path, volume)
    """
    if sound is None:
        return

    if isinstance(sound, tuple):
        effect_path = sound[0]
        volume = sound[1]
    else:
        effect_path = sound
        volume = 1.0

    if _MASTER_VOLUME == 0 or volume <= 0 or effect_path is None:
        return

    if effect_path in _RECENTLY_PLAYED:
        return

    if effect_path in _LOADED_EFFECTS:
        effect = _LOADED_EFFECTS[effect_path]
        if effect is not None:
            effect.set_volume(_MASTER_VOLUME * volume)
    elif pygame.mixer.get_init():
        try:
            effect = pygame.mixer.Sound(effect_path)
            effect.set_volume(_MASTER_VOLUME * volume)
        except Exception:
            print("ERROR: failed to load sound effect {}".format(effect_path))
            traceback.print_exc()
            effect = None
        _LOADED_EFFECTS[effect_path] = effect
    else:
        _LOADED_EFFECTS[effect_path] = effect = None

    _RECENTLY_PLAYED[effect_path] = 0
    if effect is not None:
        effect.play()

