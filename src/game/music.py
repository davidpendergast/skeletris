import pygame
import os
import threading
import time
from src.utils.util import Utils


class Songs:
    MENU_THEME = "01_menu_theme.ogg"
    AN_ADVENTURE_UNFOLDS = "02_an_adventure_unfolds.ogg"
    AMPHIBIAN = "03_amphibian.ogg"
    TREE_THEME = "04_tree_theme.ogg"
    DEAD_CITY = "06_dead_city.ogg"
    SILENCE = "<silence>"
    CONTINUE_CURRENT = "<continue>"


CURRENT_SONG = Songs.SILENCE

# y'all better acquire the lock before you do anything involving fading
_IS_FADING_LOCK = threading.Lock()
_IS_FADING = False
_NEXT_SONG_AFTER_FADE = Songs.SILENCE


def _do_fadeout(fade_duration_millis):

    # XXX according to the pygame docs, music.fadeout is supposed to block (which is why we've
    # set up all this async stuff). However, it seems to return instantly on my system (linux),
    # and according to the internet it seems like it's inconsistent on other OSes (depending on
    # whether another song is playing or something along those lines). So we basically detect
    # whether it's actually blocked or not, and block the thread for the correct duration ourselves
    # if needed. Otherwise we'll slam away the fading song too soon.

    old_time_millis = int(round(time.time() * 1000))
    pygame.mixer.music.fadeout(fade_duration_millis)
    cur_time_millis = int(round(time.time() * 1000))

    if cur_time_millis - old_time_millis < fade_duration_millis:
        rem_time_millis = fade_duration_millis - (cur_time_millis - old_time_millis)
        time.sleep(rem_time_millis / 1000.0)

    global _IS_FADING, _IS_FADING_LOCK, _NEXT_SONG_AFTER_FADE
    _IS_FADING_LOCK.acquire()
    try:
        _IS_FADING = False
        if _NEXT_SONG_AFTER_FADE is not None:
            _play_song_forcefully(_NEXT_SONG_AFTER_FADE)
            _NEXT_SONG_AFTER_FADE = None
    finally:
        _IS_FADING_LOCK.release()


def play_song(song_filename):
    if song_filename is None:
        song_filename = Songs.SILENCE

    global CURRENT_SONG, _IS_FADING_LOCK, _IS_FADING, _NEXT_SONG_AFTER_FADE
    _IS_FADING_LOCK.acquire()
    try:
        if _IS_FADING:
            # we're already fading, so just pop the new song into the fade thread
            if song_filename != Songs.CONTINUE_CURRENT:
                _NEXT_SONG_AFTER_FADE = song_filename
            else:
                return

        if CURRENT_SONG == song_filename:
            print("INFO: already playing song {}".format(song_filename))
            return
        elif song_filename is None or song_filename == Songs.CONTINUE_CURRENT:
            return
        elif CURRENT_SONG != Songs.SILENCE:
            _IS_FADING = True
            _NEXT_SONG_AFTER_FADE = song_filename
            print("INFO: starting fadeout thread")
            x = threading.Thread(target=_do_fadeout, args=(1500,))
            x.start()
        else:
            _play_song_forcefully(song_filename)
    finally:
        _IS_FADING_LOCK.release()


def _play_song_forcefully(song_filename):
    if song_filename == Songs.CONTINUE_CURRENT or song_filename is None:
        raise ValueError("_play_song_forcefully needs a real song, instead got: {}".format(song_filename))

    global CURRENT_SONG
    if song_filename == Songs.SILENCE:
        if CURRENT_SONG is not Songs.SILENCE:
            print("INFO: stopping song {}".format(CURRENT_SONG))
            pygame.mixer.music.stop()
            CURRENT_SONG = None
    else:
        print("INFO: playing song {}".format(song_filename))
        real_filename = Utils.resource_path(os.path.join("assets", "songs", song_filename))
        pygame.mixer.music.load(real_filename)
        pygame.mixer.music.play(-1, 0)

        CURRENT_SONG = song_filename



