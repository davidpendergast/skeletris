import os
import traceback
import pathlib

import appdirs


_USE_WORKING_DIR_FOR_SAVE_DATA = None
_USE_WORKING_DIR_FLAG_NAME = "put_save_data_here.txt"

_SAVE_DATA_DIR = "save_data"

_MY_NAME = "Ghast"
_GAME_NAME = "Skeletris"


def use_workingdir_for_save_data(force_reload=False):
    global _USE_WORKING_DIR_FOR_SAVE_DATA
    if _USE_WORKING_DIR_FOR_SAVE_DATA is None or force_reload:
        try:
            flag_file_exists = os.path.isfile(_USE_WORKING_DIR_FLAG_NAME)
            print("INFO: looked for \"{}\", result was: {}".format(_USE_WORKING_DIR_FLAG_NAME, flag_file_exists))
        except OSError:
            print("ERROR: failed to check for existence of put_save_data_here.txt")
            traceback.print_exc()
            flag_file_exists = False

        _USE_WORKING_DIR_FOR_SAVE_DATA = flag_file_exists

    return _USE_WORKING_DIR_FOR_SAVE_DATA


def get_user_appdata_path():
    try:
        # just some package I got from the internet. i have no idea if it can fail or
        # throw exceptions or whatnot. i hope not
        return appdirs.user_data_dir(appname=_GAME_NAME, appauthor=_MY_NAME)
    except Exception:
        print("ERROR: failed to get user's AppData directory")
        traceback.print_exc()
        return None


def get_save_data_path(with_subpath=None):
    base_path = None
    if not use_workingdir_for_save_data():
        appdata_path = get_user_appdata_path()
        if appdata_path is not None:
            base_path = pathlib.Path(appdata_path, _SAVE_DATA_DIR)
        else:
            print("WARN: couldn't get appdata path, falling back to working directory for save_data")

    if base_path is None:
        base_path = pathlib.Path(_SAVE_DATA_DIR)

    if with_subpath is not None:
        return pathlib.Path(base_path, with_subpath)
    else:
        return base_path

