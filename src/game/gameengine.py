from src.game.stats import ActorStatType, StatType
from enum import Enum
from src.utils.util import Utils
from src.world.worldstate import World

import src.game.inputs as inputs
import src.game.globalstate as gs
import src.game.settings as settings


class ActorStateNew:

    def __init__(self, name, level, base_stats, inventory, alignment):
        self.name_ = name
        self.level = level
        self.base_stats = base_stats

        self.inventory_ = inventory

        self.permanent_effects = []
        self.status_effects = []

        self.current_hp = 5  # self.stat_value(ActorStatType.MAX_HP)
        self.current_energy = 0

        self.alignment = alignment  # what "team" the actor is on.

        self.held_item = None  # item being held above the actor's head

    def stat_value(self, stat_type):
        if stat_type == ActorStatType.MAX_ENERGY:
            return 5
        else:
            return 2

    def hp(self):
        return self.current_hp

    def set_hp(self, val):
        self.current_hp = min(val, self.max_hp())

    def max_hp(self):
        return 5

    def is_dead(self):
        return self.hp() <= 0

    def inventory(self):
        return self.inventory_

    def name(self):
        return self.name_


class ActorController:

    def get_next_action(self, actor, world, input_state):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, position=pos)


class PlayerController(ActorController):

    def get_next_action(self, actor, world, input_state):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])

        if input_state.is_held(gs.get_instance().settings().left_key()):
            res = MoveToAction(actor, (pos[0] - 1, pos[1]))
        elif input_state.is_held(gs.get_instance().settings().up_key()):
            res = MoveToAction(actor, (pos[0], pos[1] - 1))
        elif input_state.is_held(gs.get_instance().settings().right_key()):
            res = MoveToAction(actor, (pos[0] + 1, pos[1]))
        elif input_state.is_held(gs.get_instance().settings().down_key()):
            res = MoveToAction(actor, (pos[0], pos[1] + 1))
        elif input_state.is_held(gs.get_instance().settings().enter_key()):
            res = SkipTurnAction(actor, position=pos)
        else:
            res = None

        if res is not None and res.is_possible(world):
            return res
        else:
            turn_left = input_state.was_pressed(gs.get_instance().settings().left_key())
            turn_right = input_state.was_pressed(gs.get_instance().settings().right_key())
            turn = None if (turn_left == turn_right) else turn_right
            return PlayerWaitAction(actor, turn_right=turn)


class ActionType(Enum):
    MOVE_TO = "MOVE_TO"
    PICKUP_ITEM = "PICKUP_ITEM"
    DROP_ITEM = "DROP_ITEM"
    THROW_ITEM = "THROW_ITEM"
    ATTACK = "ATTACK"
    INTERACT = "INTERACT"
    PLAYER_WAIT = "PLAYER_WAIT"  # special command used by player to indicate they're still deciding
    SKIP_TURN = "SKIP_TURN"
    CONSUME_ITEM = "CONSUME_ITEM"
    OPEN_DOOR = "OPEN_DOOR"


class Action:
    def __init__(self, cmd_type, anim_duration, actor_entity, item=None, position=None):
        self.cmd_type = cmd_type
        self.anim_duration = anim_duration
        self.actor_entity = actor_entity
        self.item = item
        self.position = position

    def is_possible(self, world):
        return True

    def animate_in_world(self, progress, world):
        pass

    def get_duration(self):
        return self.anim_duration

    def finalize(self, world):
        pass

    def __str__(self):
        return "{}:[actor={}, item={}, position={}]".format(self.cmd_type, self.actor_entity, self.item, self.position)


class MoveToAction(Action):
    def __init__(self, actor, position):
        Action.__init__(self, ActionType.MOVE_TO, 25, actor, position=position)
        self.start_pos = None  # this is a pixel position, used for animating

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])

        dx = abs(self.position[0] - pos[0])
        dy = abs(self.position[1] - pos[1])
        if dx + dy != 1:
            return False
        elif world.is_solid(self.position[0], self.position[1]):
            return False
        elif world.get_actor_in_cell(self.position[0], self.position[1]) is not None:
            return False

        return True

    def animate_in_world(self, progress, world):
        if self.start_pos is None:
            self.start_pos = self.actor_entity.center()

        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))

        cur_pos = self.actor_entity.center()
        new_pos = Utils.linear_interp(self.start_pos, end_pos, progress)
        self.actor_entity.move(new_pos[0] - cur_pos[0], new_pos[1] - cur_pos[1])

    def finalize(self, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.actor_entity.set_center(end_pos[0], end_pos[1])


class SkipTurnAction(Action):

    def __init__(self, actor, position):
        Action.__init__(self, ActionType.SKIP_TURN, 10, actor, position=position)

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])
        return pos == self.position


class PlayerWaitAction(Action):

    def __init__(self, actor, turn_right=None):
        Action.__init__(self, ActionType.PLAYER_WAIT, 1, actor)
        self.turn_right = turn_right

    def is_possible(self, world):
        return True

    def finalize(self, world):
        if self.turn_right is not None:
            print("turning actor")
            self.actor_entity.facing_right = self.turn_right

