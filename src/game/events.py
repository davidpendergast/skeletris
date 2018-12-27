
from enum import Enum
from src.utils.util import Utils


class EventQueue:

    def __init__(self):
        self.events = []
        self._type_lookup = {}  # EventType -> list(Event)
        self.next_events = []

    def add(self, event):
        self.next_events.append(event)

    def flip(self):
        self.events.clear()
        self._type_lookup.clear()

        tmp = self.events
        self.events = self.next_events

        for e in self.events:
            if e.get_type() not in self._type_lookup:
                self._type_lookup[e.get_type()] = []
            self._type_lookup[e.get_type()].append(e)

        self.next_events = tmp

    def all_events_with_type(self, single_type):
        if single_type in self._type_lookup:
            for e in self._type_lookup[single_type]:
                yield e

    def all_events(self, types=None, predicate=lambda x: True):
        if types is not None:
            types = Utils.listify(types)
            for t in types:
                for e in self.all_events_with_type(t):
                    if predicate(e):
                        yield e
        else:
            for e in self.events:
                if predicate(e):
                    yield e

    def has_event(self, types=None, predicate=None):
        if types is not None:
            types = Utils.listify(types)
            for t in types:
                for e in self.all_events_with_type(t):
                    if predicate(e):
                        return True
        else:
            for e in self.events:
                if predicate(e):
                    return True

        return False


class EventType(Enum):
    # these are "something happened" events
    ENEMY_KILLED = "ENEMY_KILLED",
    STORY_EVENT = "STORY_EVENT",
    PLAYER_DIED = "PLAYER_DIED",
    DOOR_OPENED = "DOOR_OPENED",
    NPC_INTERACT = "NPC_INTERACT",
    ENTITY_INTERACT = "ENTITY_INTERACT",
    DIALOG_EXIT = "DIALOG_EXIT",
    ENTERED_BOX = "ENTERED_BOX",
    EXITED_BOX = "EXITED_BOX",
    TRIGGERED_BOX = "TRIGGERED_BOX",

    # these are "please do something" events
    PLAY_SOUND = "PLAY_SOUND"
    NEW_ZONE = "NEW_ZONE"
    GAME_EXIT = "GAME_EXIT"
    NEW_GAME = "NEW_GAME"


class Event:
    def __init__(self, event_type, data, description=""):
        self._event_type = event_type
        self._data = data
        self.description = description

    def get_type(self):
        return self._event_type

    def get_data(self):
        return self._data

    def get_msg(self):
        return self.description

    def __repr__(self):
        return "Event({}, {}, {})".format(self._event_type, self._data, self.description)


class EventListenerScope(Enum):
    ZONE = 1
    PERMANENT = 2


class EventListener:

    def __init__(self, action, event_type, predicate, scope=EventListenerScope.ZONE, single_use=False):
        """
        Event, World, GlobalState -> () action: runnable action to perform when event occurs
        EventType event_type: type of event to listen for
        Event -> bool predicate: predicate for events to accept
        EventListenerScope scope: scope of listener
        bool single_use: whether to auto-remove listener after one trigger
        """
        self.event_type = event_type
        self.predicate = predicate if predicate is not None else lambda x: True
        self.action = action
        self.scope = scope
        self.single_use = single_use


class DoorOpenEvent(Event):
    def __init__(self, grid_x, grid_y):
        Event.__init__(self, EventType.DOOR_OPENED, (grid_x, grid_y), "door opened at ({}, {})".format(grid_x, grid_y))

    def get_position(self):
        return self.get_data()


class NpcInteractEvent(Event):
    def __init__(self, npc_id):
        Event.__init__(self, EventType.NPC_INTERACT, npc_id, "interacted with npc: {}".format(npc_id))

    def get_npc_id(self):
        return self.get_data()


class EntityInteractEvent(Event):
    def __init__(self, entity):
        Event.__init__(self, EventType.ENTITY_INTERACT, entity, "interacted with entity: {}".format(entity))

    def get_entity(self):
        return self.get_data()


class TriggerBoxEvent(Event):
    def __init__(self, box_id, event_type, desc):
        Event.__init__(self, event_type, box_id, description=desc)

    def get_box_id(self):
        return self.get_data()

    @staticmethod
    def new_enter_event(box_id):
        return TriggerBoxEvent(box_id, EventType.ENTERED_BOX, "entered box with id: {}".format(box_id))

    @staticmethod
    def new_exit_event(box_id):
        return TriggerBoxEvent(box_id, EventType.EXITED_BOX, "exited box with id: {}".format(box_id))

    @staticmethod
    def new_trigger_event(box_id):
        return TriggerBoxEvent(box_id, EventType.TRIGGERED_BOX, "triggered box with id: {}".format(box_id))


class DialogExitEvent(Event):
    def __init__(self, uid, opt_idx):
        Event.__init__(self, EventType.DIALOG_EXIT, (uid, opt_idx), description="exited dialog with uid: " + str(uid))

    def get_uid(self):
        return self.get_data()[0]

    def get_option_idx(self):
        return self.get_data()[1]


class NewZoneEvent(Event):

    NORMAL = "NORMAL"
    RETURNING = "RETURNING"
    SAVE_STATION = "SAVE_STATION"

    def __init__(self, next_zone, current_zone, transfer_type=NORMAL):
        data = (next_zone, current_zone, transfer_type)
        desc = "moved from zone {} to {} via {}".format(current_zone, next_zone, transfer_type)
        Event.__init__(self, EventType.NEW_ZONE, data, description=desc)

    def get_next_zone(self):
        return self.get_data()[0]

    def get_current_zone(self):
        return self.get_data()[1]

    def get_transfer_type(self):
        return self.get_data()[2]


class GameExitEvent(Event):

    def __init__(self):
        Event.__init__(self, EventType.GAME_EXIT, None, description="exit game")


class NewGameEvent(Event):

    def __init__(self, instant_start=True):
        Event.__init__(self, EventType.NEW_GAME, instant_start, description="new game")

    def get_instant_start(self):
        return self.get_data()


class PlayerDiedEvent(Event):

    def __init__(self):
        Event.__init__(self, EventType.PLAYER_DIED, None, description="player died")


class EnemyDiedEvent(Event):

    def __init__(self, enemy_uid, template, location):
        data = (enemy_uid, template, location)
        Event.__init__(self, EventType.ENEMY_KILLED, data, description="enemy killed")

    def get_uid(self):
        return self.get_data()[0]

    def get_template(self):
        return self.get_data()[1]

    def get_position(self):
        return self.get_data()[2]
