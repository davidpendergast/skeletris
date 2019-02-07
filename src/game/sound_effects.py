import pygame
import os
from src.utils.util import Utils
import traceback
import random


class Effects:
    DOOR_SLIDE = "door_slide.ogg"
    DOOR_OPEN = "door_open.ogg"
    ENEMY_DEATH = ("enemy_death1.ogg", "enemy_death2.ogg", "enemy_death3.ogg")
    CLICK = "click.ogg"
    CLICK2 = "click_2.ogg"
    LOAD = "load.ogg"
    MISC_MENU_= "misc_menu.ogg"
    MISC_MENU_2 = "misc_menu_2.ogg"
    MISC_MENU_3 = "misc_menu_3.ogg"
    MISC_MENU_4 = "misc_menu_4.ogg"
    NEGATIVE_2 = "negative_2.ogg"
    SAVE = "save.ogg"


_VOLUME_MULTIPLIER = {
    Effects.CLICK: 0.75
}


_LOADED_EFFECTS = {}  # effect_id -> Effect object

_RECENTLY_PLAYED = {}  # effect_id -> ticks since last play

RECENCY_LIMIT = 4  # if an effect was already played X ticks ago, don't play it again


def update():
    to_remove = []
    for effect in _RECENTLY_PLAYED:
        if _RECENTLY_PLAYED[effect] >= RECENCY_LIMIT:
            to_remove.append(effect)
        else:
            _RECENTLY_PLAYED[effect] = _RECENTLY_PLAYED[effect] + 1
    for effect in to_remove:
        del _RECENTLY_PLAYED[effect]


def play_sound(effect_id):
    if effect_id in _RECENTLY_PLAYED:
        return

    if isinstance(effect_id, list):
        effect_filename = random.choice(effect_id)
    else:
        effect_filename = effect_id

    if effect_filename in _LOADED_EFFECTS:
        effect = _LOADED_EFFECTS[effect_filename]
    else:
        try:
            path = Utils.resource_path(os.path.join("assets", "sounds", effect_filename))
            effect = pygame.mixer.Sound(path)
            if effect_id in _VOLUME_MULTIPLIER:
                effect.set_volume(_VOLUME_MULTIPLIER[effect_id])
        except:
            print("ERROR: failed to load sound effect {}".format(effect_filename))
            traceback.print_exc()
            effect = None
        _LOADED_EFFECTS[effect_filename] = effect

    if effect is not None:
        _RECENTLY_PLAYED[effect_id] = 0
        effect.play()

