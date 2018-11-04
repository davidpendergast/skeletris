
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
        tmp = self.events
        self.events = self.next_events
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
        EventType event_type: type of event to listen for
        Event -> bool predicate: predicate for events to accept
        Event, World, GlobalState -> () action: runnable action to perform when event occurs
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
    def __init__(self, uid):
        Event.__init__(self, EventType.DIALOG_EXIT, uid, description="exited dialog with uid: " + str(uid))

    def get_uid(self):
        return self.get_data()
