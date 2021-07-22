import pygame
import os
import threading
import time
from src.utils.util import Utils


_SILENCE_ID = "<silence>"
_CONTINUE_ID = "<continue>"


class Song:

    def __init__(self, name, filename, volume=1.0):
        self.name = name
        self.filename = filename
        self.volume = volume

    def is_silence(self):
        return self.filename == _SILENCE_ID

    def is_continue(self):
        return self.filename == _CONTINUE_ID

    def __repr__(self):
        return "{}[name={}, filename={}]".format(
            type(self).__name__, self.name, self.filename)

    def __eq__(self, other):
        if isinstance(other, Song):
            return self.name == other.name and self.filename == other.filename
        else:
            return False

    def __hash__(self):
        return hash(self.name) + hash(self.filename)


class Songs:

    MENU_THEME = Song("Menu Theme", "menu_theme.ogg")

    # Boss themes
    AMPHIBIAN = Song("Amphibian", "amphibian.ogg")
    TREE_THEME = Song("Horror", "horde.ogg", volume=0.9)
    DEAD_CITY = Song("Robot", "robot.ogg")
    MEDUSA_THEME = Song("Medusa", "medusa.ogg")
    ARACHNID = Song("Arachnid", "arachnid.ogg")

    # Regular Zone Themes
    UNEARTHED = Song("Undergrowth", "unearthed.ogg")
    CAVES = Song("Caves", "caves.ogg", volume=0.66)
    CITY = Song("City", "city.ogg", volume=0.66)
    SWAMPS = Song("Swamps", "swamps.ogg", volume=0.66)
    CORE = Song("Core", "core.ogg", volume=0.66)

    SILENCE = Song("Silence", _SILENCE_ID)
    CONTINUE_CURRENT = Song("Continue", _CONTINUE_ID)

    @staticmethod
    def get_basic_caves_song():
        return Songs.CAVES

    @staticmethod
    def get_basic_swamp_song():
        return Songs.SWAMPS

    @staticmethod
    def get_basic_city_song():
        return Songs.CITY

    @staticmethod
    def get_basic_catacombs_song():
        return Songs.CORE


CURRENT_SONG = Songs.SILENCE


_MASTER_VOLUME = 1.0


def set_master_volume(val):
    global _MASTER_VOLUME, CURRENT_SONG
    if val != _MASTER_VOLUME:
        print("INFO: setting master music volume to {}".format(val))
        _MASTER_VOLUME = Utils.bound(val, 0.0, 1.0)
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(_MASTER_VOLUME * CURRENT_SONG.volume)


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
    if pygame.mixer.get_init():
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


def play_song(song):
    if song is None:
        song = Songs.SILENCE

    if song.is_continue():
        return

    global CURRENT_SONG, _IS_FADING_LOCK, _IS_FADING, _NEXT_SONG_AFTER_FADE

    _IS_FADING_LOCK.acquire()
    try:
        if _IS_FADING:
            # intercept the active fadeout and insert the new song
            _NEXT_SONG_AFTER_FADE = song

        elif song == CURRENT_SONG:
            pass

        elif not CURRENT_SONG.is_silence():
            _IS_FADING = True
            _NEXT_SONG_AFTER_FADE = song
            print("INFO: starting fadeout thread")
            x = threading.Thread(target=_do_fadeout, args=(2000,))
            x.start()

        else:
            _play_song_forcefully(song)

    finally:
        _IS_FADING_LOCK.release()


def _play_song_forcefully(song):
    if song is None or song.is_continue():
        raise ValueError("_play_song_forcefully needs a real song, instead got: {}".format(song))

    global _MASTER_VOLUME, CURRENT_SONG
    if not CURRENT_SONG.is_silence():
        if CURRENT_SONG != song:
            print("INFO: stopping song {}".format(CURRENT_SONG))
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    if song.is_silence():
        CURRENT_SONG = Songs.SILENCE
    else:
        if CURRENT_SONG == song:
            print("WARN: starting song that's already playing {}".format(song))
        else:
            print("INFO: starting song {}".format(song))

        if pygame.mixer.get_init():
            real_filename = Utils.resource_path(os.path.join("assets", "songs", song.filename))
            pygame.mixer.music.set_volume(_MASTER_VOLUME * song.volume)
            pygame.mixer.music.load(real_filename)
            pygame.mixer.music.play(-1, 0)

        CURRENT_SONG = song



