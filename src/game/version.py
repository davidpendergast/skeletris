import src.utils.util as util
import traceback

_VERSION_PATH = "info/version.json"

_VERSION = (-1, -1, -1, "")


def load_version_info(force_nodev=False):
    try:
        resource_path = util.Utils.resource_path(_VERSION_PATH)
        version_info = util.Utils.load_json_from_path(resource_path)
        major = int(version_info["major"])
        minor = int(version_info["minor"])
        bugfix = int(version_info["bugfix"])
        desc = str(version_info["desc"])

        if not force_nodev:
            import src.game.debug as debug
            if debug.is_dev():
                desc = "DEV"

        global _VERSION
        _VERSION = (major, minor, bugfix, desc)
    except FileNotFoundError:
        print("ERROR: failed to load version info, version.json is missing")
        traceback.print_exc()
    except (ValueError, KeyError):
        print("ERROR: failed to load version info, version.json couldn't be parsed")
        traceback.print_exc()


def get_version():
    return _VERSION


def get_pretty_version_string():
    global _VERSION

    v = [_VERSION[i] if _VERSION[i] >= 0 else "?" for i in range(0, 3)]

    if len(_VERSION[3]) > 0:
        return "{}.{}.{}-{}".format(v[0], v[1], v[2], _VERSION[3])
    else:
        return "{}.{}.{}".format(v[0], v[1], v[2])


