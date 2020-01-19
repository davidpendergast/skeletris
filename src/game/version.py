import src.utils.util as util
import traceback
import pathlib
import os


_VERSION_PATH = pathlib.Path("info/version.json")
_VERSION_DESC_OVERRIDE_PATH = pathlib.Path("info/version_override.json")


_VERSION = (-1, -1, -1, "")


MAJOR_KEY = "major"
MINOR_KEY = "minor"
BUGFIX_KEY = "bugfix"
DESC_KEY = "desc"


def _try_parse_version_info(filepath, do_err_logging=True):
    try:
        resource_path = util.Utils.resource_path(filepath)
        version_info = util.Utils.load_json_from_path(resource_path)

        return version_info

    except FileNotFoundError:
        if do_err_logging:
            print("ERROR: failed to load version info, {} is missing".format(filepath))
            traceback.print_exc()
    except Exception:
        if do_err_logging:
            print("ERROR: failed to load version info, {} couldn't be parsed".format(filepath))
            traceback.print_exc()

    return None


def load_version_info(force_nodev=False, ignore_override=False):
    global _VERSION

    version_info = _try_parse_version_info(_VERSION_PATH, do_err_logging=True)

    major = -1
    minor = -1
    bugfix = -1
    desc = "MOD"

    if version_info is not None:
        try:
            desc = str(version_info[DESC_KEY])
            major = int(version_info[MAJOR_KEY])
            minor = int(version_info[MINOR_KEY])
            bugfix = int(version_info[BUGFIX_KEY])

        except (ValueError, KeyError):
            print("ERROR: malformed version json in {}: {}".format(_VERSION, version_info))

    if not ignore_override:
        desc_override = _try_parse_version_info(_VERSION_DESC_OVERRIDE_PATH, do_err_logging=False)
        if desc_override is not None:
            try:
                desc = str(desc_override[DESC_KEY])
            except (ValueError, KeyError):
                print("ERROR: malformed json in {}: {}".format(_VERSION_DESC_OVERRIDE_PATH, desc_override))

    if not force_nodev:
        import src.game.debug as debug
        if debug.is_dev():
            desc = "DEV"

    _VERSION = (major, minor, bugfix, desc)


def get_version_as_json():
    return {
        MAJOR_KEY: _VERSION[0],
        MINOR_KEY: _VERSION[1],
        BUGFIX_KEY: _VERSION[2],
        DESC_KEY: _VERSION[3]
    }


def get_version():
    return _VERSION


def get_pretty_version_string(for_version=None):
    if for_version is None:
        for_version = get_version()

    v = [for_version[i] if for_version[i] >= 0 else "?" for i in range(0, 3)]

    return "{}.{}.{}-{}".format(v[0], v[1], v[2], for_version[3])


def _create_version_desc_override_file(desc="MOD"):
    json_blob = {DESC_KEY: desc}
    util.Utils.save_json_to_path(json_blob, _VERSION_DESC_OVERRIDE_PATH)


def _remove_version_desc_override_file():
    if os.path.exists(str(_VERSION_DESC_OVERRIDE_PATH)):
        os.remove(str(_VERSION_DESC_OVERRIDE_PATH))


