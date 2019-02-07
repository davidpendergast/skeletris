import pygame
import os
from src.utils.util import Utils
import traceback
import random


class Effects:
    DOOR_SLIDE = "door_slide.ogg"
    DOOR_OPEN = "door_open.ogg"
    ENEMY_DEATH = ["enemy_death1.ogg", "enemy_death2.ogg", "enemy_death3.ogg"]
    CLICK = "click.ogg"
    CLICK2 = "click_2.ogg"
    LOAD = "load.ogg"
    MISC_MENU_2 = "misc_menu_2.ogg"
    MISC_MENU_3 = "misc_menu_3.ogg"
    MISC_MENU_4 = "misc_menu_4.ogg"
    NEGATIVE_2 = "negative_2.ogg"
    SAVE = "save.ogg"


_LOADED_EFFECTS = {}


def play_sound(effect_filename):
    if isinstance(effect_filename, list):
        effect_filename = random.choice(effect_filename)

    if effect_filename in _LOADED_EFFECTS:
        effect = _LOADED_EFFECTS[effect_filename]
    else:
        try:
            path = Utils.resource_path(os.path.join("assets", "sounds", effect_filename))
            effect = pygame.mixer.Sound(path)
        except:
            print("ERROR: failed to load sound effect {}".format(effect_filename))
            traceback.print_exc()
            effect = None
        _LOADED_EFFECTS[effect_filename] = effect

    if effect is not None:
        effect.play()
