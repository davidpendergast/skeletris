import pygame
import os
import threading
import time
from src.utils.util import Utils


class Songs:
    MENU_THEME = "01_menu_theme.ogg"
    AMPHIBIAN = "03_amphibian.ogg"
    TREE_THEME = "04_tree_theme.ogg"
    DEAD_CITY = "06_dead_city.ogg"
    UNEARTHED = "07_unearthed.ogg"
    NAMELESS_THEME = "08_nameless.ogg"
    ARACHNID = "09_arachnid.ogg"
    CAVES = "13_caves.ogg"
    CITY = "14_city.ogg"
    SWAMPS = "15_swamps.ogg"

    SILENCE = "<silence>"
    CONTINUE_CURRENT = "<continue>"

    @staticmethod
    def get_basic_caves_song():
        return Songs.CAVES

    @staticmethod
    def get_basic_swamp_song():
        return Songs.SWAMPSd

    @staticmethod
    def get_basic_city_song():
        return Songs.CITY

    @staticmethod
    def get_basic_core_song():
        return Songs.SILENCE  # TODO - not ready yet


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
        if _NEXT_SONG_AFTER_FADE == Songs.CONTINUE_CURRENT:
            print("WARN: _NEXT_SONG was set to {} during fadeout, going silent instead".format(Songs.CONTINUE_CURRENT))
            _play_song_forcefully(Songs.SILENCE)
        else:
            _play_song_forcefully(_NEXT_SONG_AFTER_FADE)
        _NEXT_SONG_AFTER_FADE = Songs.SILENCE
    finally:
        _IS_FADING_LOCK.release()


def play_song(song_filename):
    if song_filename == Songs.CONTINUE_CURRENT:
        return

    if song_filename is None:
        song_filename = Songs.SILENCE

    global CURRENT_SONG, _IS_FADING_LOCK, _IS_FADING, _NEXT_SONG_AFTER_FADE
    _IS_FADING_LOCK.acquire()
    try:
        if _IS_FADING:
            # intercept the active fadeout and insert the new song
            _NEXT_SONG_AFTER_FADE = song_filename

        elif song_filename == CURRENT_SONG:
            pass

        elif CURRENT_SONG != Songs.SILENCE:
            _IS_FADING = True
            _NEXT_SONG_AFTER_FADE = song_filename
            print("INFO: starting fadeout thread")
            x = threading.Thread(target=_do_fadeout, args=(2000,))
            x.start()

        else:
            _play_song_forcefully(song_filename)

    finally:
        _IS_FADING_LOCK.release()


def _play_song_forcefully(song_filename):
    if song_filename == Songs.CONTINUE_CURRENT or song_filename is None:
        raise ValueError("_play_song_forcefully needs a real song, instead got: {}".format(song_filename))

    global CURRENT_SONG
    if CURRENT_SONG != Songs.SILENCE:
        if CURRENT_SONG != song_filename:
            print("INFO: stopping song {}".format(CURRENT_SONG))
        pygame.mixer.music.stop()

    if song_filename == Songs.SILENCE:
        CURRENT_SONG = Songs.SILENCE
    else:
        if CURRENT_SONG == song_filename:
            print("WARN: starting song that's already playing {}".format(song_filename))
        else:
            print("INFO: starting song {}".format(song_filename))

        real_filename = Utils.resource_path(os.path.join("assets", "songs", song_filename))
        pygame.mixer.music.load(real_filename)
        pygame.mixer.music.play(-1, 0)

        CURRENT_SONG = song_filename



