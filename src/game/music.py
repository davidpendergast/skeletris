import pygame
import os
from src.utils.util import Utils


class Songs:
    MENU_THEME = "01_menu_theme.ogg"
    AN_ADVENTURE_UNFOLDS = "02_an_adventure_unfolds.ogg"
    AMPHIBIAN = "03_amphibian.ogg"
    TREE_THEME = "04_tree_theme.ogg"
    SILENCE = "<silence>"
    CONTINUE_CURRENT = "<continue>"


CURRENT_SONG = None


def play_song(song_filename):
    global CURRENT_SONG
    if CURRENT_SONG == song_filename:
        print("INFO: already playing song {}".format(song_filename))
        return
    elif song_filename is None or song_filename == Songs.CONTINUE_CURRENT:
        return
    elif song_filename == Songs.SILENCE:
        if pygame.mixer.music.get_busy():
            # TODO this thing blocks...
            # pygame.mixer.music.fadeout(1500)
            pygame.mixer.music.stop()
            print("INFO: stopping song {}".format(CURRENT_SONG))

        CURRENT_SONG = None
    else:
        print("INFO: playing song {}".format(song_filename))
        real_filename = Utils.resource_path(os.path.join("assets", "songs", song_filename))
        pygame.mixer.music.load(real_filename)
        pygame.mixer.music.play(-1, 0)
        CURRENT_SONG = song_filename

