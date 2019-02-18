from enum import Enum

from src.utils.util import Utils

_StoryStateBools = set()
_StoryStateInts = set()
_StoryStateStrings = set()


def _int_key(key):
    _StoryStateInts.add(key)
    return key


def _bool_key(key):
    _StoryStateBools.add(key)
    return key


def _string_key(key):
    _StoryStateStrings.add(key)
    return key


class StoryStateKey(str, Enum):
    OPENING_CUTSCENE_SHOWN = _bool_key("opening_cutscene_shown")
    FROG_BOSS_DEAD = _bool_key("frog_boss_dead")

    @staticmethod
    def is_bool(key):
        return key in _StoryStateBools

    @staticmethod
    def is_int(key):
        return key in _StoryStateInts

    @staticmethod
    def is_string(key):
        return key in _StoryStateStrings


class StoryState:

    def __init__(self):
        self.map = {
            StoryStateKey.OPENING_CUTSCENE_SHOWN: False,
            StoryStateKey.FROG_BOSS_DEAD: False
        }

        for ssk in StoryStateKey:
            if ssk.value not in self.map:
                raise ValueError("no default value for story state key {}".format(ssk.value))

    @staticmethod
    def validate(key, value):
        if StoryStateKey.is_bool(key):
            if not isinstance(value, bool):
                raise ValueError("story state key {} must be type bool, instead received: {}".format(key, value))
        elif StoryStateKey.is_int(key):
            if not isinstance(value, int):
                raise ValueError("story state key {} must be type int, instead received: {}".format(key, value))
        elif StoryStateKey.is_string(key):
            if not isinstance(value, str):
                raise ValueError("story state key {} must be type str, instead received: {}".format(key, value))
        else:
            raise ValueError("unrecognized story state key: {}".format(key))

    def set(self, key, value):
        StoryState.validate(key, value)
        print("INFO: setting story state {} to: {}".format(key, value))
        self.map[key] = value

    def get(self, key):
        if key in self.map:
            return self.map[key]
        else:
            raise ValueError("unrecognized story state key: {}".format(key))

    def to_json(self):
        return self.map

    @staticmethod
    def from_json(blob):
        story_state = StoryState()
        for ssk in StoryStateKey:
            key = ssk.value
            loaded_value = None
            if StoryStateKey.is_bool(key):
                loaded_value = Utils.read_bool(blob, key, None)
            elif StoryStateKey.is_int(key):
                loaded_value = Utils.read_int(blob, key, None)
            elif StoryStateKey.is_string(key):
                loaded_value = Utils.read_string(blob, key, None)

            if loaded_value is None:
                print("WARN: failed to load storystate key {}; using default value: {}".format(key, story_state.get(key)))
            else:
                story_state.set(key, loaded_value)

        return story_state
