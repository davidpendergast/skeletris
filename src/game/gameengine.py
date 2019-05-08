from enum import Enum
from src.utils.util import Utils

import src.game.globalstate as gs
import src.game.spriteref as spriteref
from src.game.stats import StatType

import random


class ActorState:

    def __init__(self, name, level, base_stats, inventory, alignment):
        self.name_ = name
        self.level = level
        self.base_stats = base_stats

        self.inventory_ = inventory

        self.permanent_effects = []
        self.status_effects = []

        self.current_hp = self.max_hp()
        self.current_energy = 0
        self._last_turn_tick = 0  # used to determine energization order

        self.alignment = alignment  # what "team" the actor is on.

        self.held_item = None  # item being held above the actor's head

    def all_stat_providers(self):
        yield self.base_stats
        for item in self.inventory().all_equipped_items():
            yield item
        for perm_effect in self.permanent_effects:
            yield perm_effect
        for status_effect in self.status_effects:
            yield status_effect

    def stat_value(self, stat_type):
        res = 0
        for provider in self.all_stat_providers():
            res += provider.stat_value(stat_type)
        return res

    def att_value_with_item(self, item):
        res = self.stat_value(StatType.ATT)
        if item is None:
           res += self.stat_value(StatType.UNARMED_ATT)
        else:
            res += item.stat_value(StatType.LOCAL_ATT)
        return Utils.bound(res, 0, None)

    def hp(self):
        return self.current_hp

    def turn_duration_modifier(self):
        if self.alignment == 0:
            return 1.0
        else:
            return 0.66

    def set_hp(self, val):
        self.current_hp = min(val, self.max_hp())

    def energy(self):
        return self.current_energy

    def speed(self):
        raw_val = self.stat_value(StatType.SPEED)
        return Utils.bound(raw_val, 1, self.max_energy())

    def max_energy(self):
        return 8

    def is_alive(self):
        return self.current_hp > 0

    def last_turn_tick(self):
        return self._last_turn_tick

    def set_energy(self, val):
        self.current_energy = Utils.bound(val, 0, self.max_energy())

    def update_last_turn_tick(self):
        self._last_turn_tick = gs.get_instance().tick_counter

    def max_hp(self):
        raw_value = self.stat_value(StatType.VIT)
        return Utils.bound(raw_value, 1, 999)

    def light_level(self):
        min_level = self.stat_value(StatType.MIN_LIGHT_LEVEL)
        cur_level = self.stat_value(StatType.LIGHT_LEVEL)

        return Utils.bound(max(min_level, cur_level), 0, 16)

    def inventory(self):
        return self.inventory_

    def name(self):
        return self.name_

    def handle_death(self, world, actor_entity):
        pos = actor_entity.center()
        for item in self.inventory().all_items():
            world.add_item_as_entity(item, pos, direction=None)

        from src.world.entities import AnimationEntity

        splosion = AnimationEntity(pos[0], pos[1] - 24, spriteref.explosions, 40, spriteref.ENTITY_LAYER, scale=4)
        splosion.set_color((0, 0, 0))
        world.add(splosion)

        world.remove(actor_entity)


class ActorController:

    def get_next_action(self, actor, world, input_state):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, position=pos)


class PlayerController(ActorController):

    def get_next_action(self, actor, world, input_state):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])

        target_pos = None
        if input_state.is_held(gs.get_instance().settings().left_key()):
            target_pos = (pos[0] - 1, pos[1])
        elif input_state.is_held(gs.get_instance().settings().up_key()):
            target_pos = (pos[0], pos[1] - 1)
        elif input_state.is_held(gs.get_instance().settings().right_key()):
            target_pos = (pos[0] + 1, pos[1])
        elif input_state.is_held(gs.get_instance().settings().down_key()):
            target_pos = (pos[0], pos[1] + 1)

        res_list = []
        if target_pos is not None:
            res_list.append(AttackAction(actor, None, target_pos))
            res_list.append(OpenDoorAction(actor, target_pos))
            res_list.append(MoveToAction(actor, target_pos))

        if input_state.is_held(gs.get_instance().settings().enter_key()):
            res_list.append(SkipTurnAction(actor, position=pos))

        for action in res_list:
            if action.is_possible(world):
                return action

        turn_left = input_state.was_pressed(gs.get_instance().settings().left_key())
        turn_right = input_state.was_pressed(gs.get_instance().settings().right_key())
        turn = None if (turn_left == turn_right) else turn_right
        return PlayerWaitAction(actor, turn_right=turn)


class EnemyController(ActorController):

    def get_next_action(self, actor, world, input_state):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])

        neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
        random.shuffle(neighbors)

        for n in neighbors:
            res = AttackAction(actor, None, n)
            if res.is_possible(world):
                return res

        for n in neighbors:
            res = MoveToAction(actor, n)
            if res.is_possible(world):
                return res

        return SkipTurnAction(actor, position=pos)


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
    OPEN_CHEST = "OPEN_CHEST"


class Action:
    def __init__(self, cmd_type, anim_duration, actor_entity, item=None, position=None):
        self.cmd_type = cmd_type
        self.anim_duration = anim_duration
        self.actor_entity = actor_entity
        self.item = item
        self.position = position

    def get_type(self):
        return self.cmd_type

    def get_position(self):
        return self.position

    def is_fake_player_wait_action(self):
        return self.get_type() == ActionType.PLAYER_WAIT

    def is_possible(self, world):
        return True

    def animate_in_world(self, progress, world):
        pass

    def get_duration(self):
        return self.anim_duration

    def start(self, world):
        pass

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

    def start(self, world):
        self.start_pos = self.actor_entity.center()

    def animate_in_world(self, progress, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))

        cur_pos = self.actor_entity.center()
        new_pos = Utils.linear_interp(self.start_pos, end_pos, progress)
        self.actor_entity.move(new_pos[0] - cur_pos[0], new_pos[1] - cur_pos[1])

    def finalize(self, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.actor_entity.set_center(end_pos[0], end_pos[1])


class OpenDoorAction(MoveToAction):

    def __init__(self, actor, position):
        MoveToAction.__init__(self, actor, position)
        self.door_entity = None

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])

        dx = abs(self.position[0] - pos[0])
        dy = abs(self.position[1] - pos[1])
        if dx + dy != 1:
            return False

        if world.get_actor_in_cell(self.position[0], self.position[1]) is not None:
            return False

        from src.world.worldstate import World
        if world.get_geo(self.position[0], self.position[1]) != World.DOOR:
            return False

        if world.get_door_in_cell(*self.position) is None:
            return False

        return True

    def start(self, world):
        super().start(world)
        self.door_entity = world.get_door_in_cell(*self.position)

    def animate_in_world(self, progress, world):
        super().animate_in_world(progress, world)
        self.door_entity.set_open_progress_for_render(progress)

    def finalize(self, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.door_entity.remove_self_from_world(world)
        self.actor_entity.set_center(end_pos[0], end_pos[1])


class AttackAction(Action):
    R_TEXT_COLOR = (0.65, 0.1, 0.1)
    G_TEXT_COLOR = (0.2, 0.85, 0.2)
    B_TEXT_COLOR = (0.1, 0.1, 0.65)

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.ATTACK, 24, actor, item=item, position=position)
        self._did_animations = False
        self._results = None  # (int: dmg, ActorEntity: target)
        self._start_pos = None

    def is_possible(self, world):
        actor = self.actor_entity
        if self.item is not None:
            if not actor.get_actor_state().inventory().is_equipped(self.item):
                return False

        in_range = False
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        for n in Utils.neighbors(pos[0], pos[1]):
            # TODO - items will have their own ranges
            if n == self.position:
                in_range = True
                break
        if not in_range:
            return False

        target = world.get_actor_in_cell(self.position[0], self.position[1])
        if target is None or target.get_actor_state().alignment == actor.get_actor_state().alignment:
            return False

        return True

    def _determine_attack_result(self, world):
        target = world.get_actor_in_cell(self.position[0], self.position[1])
        t_state = target.get_actor_state()

        t_def = t_state.stat_value(StatType.DEF)
        a_att = self.actor_entity.get_actor_state().att_value_with_item(self.item)

        # explanation:
        #   attacker rolls a D6 for each ATT value they have.
        #   defender rolls a D4 for each DEF value they have.
        #   defender uses each of their die to 'block' as many attacker dice as possible.
        #       a die can only block a die with value less than or equal to it's own.
        #   the number of unblocked attackers is the amount of damage dealt.

        atts = [random.randint(1, 6) for _ in range(0, a_att)]
        defs = [random.randint(1, 4) for _ in range(0, t_def)]

        atts.sort()
        defs.sort()

        while len(atts) > 0 and len(defs) > 0:
            defender = defs.pop(0)
            if atts[0] <= defender:
                atts.pop(0)

        self._results = (len(atts), target)

    def _apply_attack_and_add_animations_if_necessary(self, world):
        if not self._did_animations:
            self._did_animations = True
            damage = self._results[0]
            target = self._results[1]
            t_state = target.get_actor_state()
            if damage <= 0:
                world.show_floating_text("miss", AttackAction.B_TEXT_COLOR, 3, target)
            else:
                t_state.set_hp(t_state.hp() - damage)
                world.show_floating_text("-{}".format(damage), AttackAction.R_TEXT_COLOR, 3, target)
                target.perturb_color(AttackAction.R_TEXT_COLOR, 25)
                target.perturb(20, 18)

    def start(self, world):
        self._determine_attack_result(world)
        self._start_pos = self.actor_entity.center()

    def animate_in_world(self, progress, world):
        run_at_pct = 0.3
        recover_pcnt = 1 - run_at_pct

        start_at = self._start_pos
        target_at = self._results[1].center()
        stop_at = target_at

        vec = Utils.sub(target_at, start_at)
        dist = Utils.mag(vec)
        if dist > 16:
            vec = Utils.set_length(vec, dist - 16)
            stop_at = Utils.add(start_at, vec)

        if progress <= run_at_pct:
            new_pos = Utils.linear_interp(start_at, stop_at, progress / run_at_pct)
        else:
            self._apply_attack_and_add_animations_if_necessary(world)
            new_pos = Utils.linear_interp(stop_at, start_at, (progress - run_at_pct) / recover_pcnt)

        dxy = Utils.sub(new_pos, self.actor_entity.center())
        self.actor_entity.move(dxy[0], dxy[1])

    def finalize(self, world):
        self._apply_attack_and_add_animations_if_necessary(world)
        self.actor_entity.set_center(self._start_pos[0], self._start_pos[1])

        face_dir = Utils.sub(self._results[1].center(), self._start_pos)
        if face_dir[0] < 3:
            self.actor_entity.facing_right = False
        elif face_dir[0] > 3:
            self.actor_entity.facing_right = True

        # make victim face attacker iff attack landed
        if self._results[0] > 0:
            if face_dir[0] < 3:
                self._results[1].facing_right = True
            elif face_dir[0] > 3:
                self._results[1].facing_right = False


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
            self.actor_entity.facing_right = self.turn_right

