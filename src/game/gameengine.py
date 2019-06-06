from enum import Enum
from src.utils.util import Utils

import src.game.globalstate as gs
import src.game.spriteref as spriteref
from src.game.stats import StatTypes
import src.utils.colors as colors
import src.game.dialog as dialog
import src.game.statuseffects as statuseffects
import src.game.balance as balance
from src.game.stats import StatProvider

import random


class ActorState(StatProvider):

    def __init__(self, name, level, base_stats, inventory, alignment):
        self.name_ = name
        self.level = level
        self.base_stats = base_stats

        self.inventory_ = inventory

        self.permanent_effects = []

        self.status_effects = {}  # StatusEffect -> turns remaining

        self.current_hp = self.max_hp()
        self.current_energy = 0

        self._ready_to_act = False

        self.alignment = alignment  # what "team" the actor is on.

        self.held_item = None  # item on the mouse cursor TODO - this doesn't belong here~

    def all_stat_providers(self):
        yield self.base_stats
        for item in self.inventory().all_equipped_items():
            yield item
        for perm_effect in self.permanent_effects:
            yield perm_effect
        for status_effect in self.status_effects:
            yield status_effect

    def get_all_mappable_action_providers(self):
        yield ItemActions.UNARMED_ATTACK
        for item in self.inventory().all_equipped_items():
            for action_provider in item.all_actions():
                if action_provider.is_mappable():
                    yield ItemActionProvider(item, action_provider)
        for item in self.inventory().all_inv_items():
            for action_provider in item.all_actions():
                if action_provider.is_mappable() and not action_provider.needs_to_be_equipped:
                    yield ItemActionProvider(item, action_provider)

    def stat_value(self, stat_type, local=False):
        res = 0
        for provider in self.all_stat_providers():
            res += provider.stat_value(stat_type, local=local)
        return res

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

    def intelligence(self):
        return Utils.bound(self.stat_value(StatTypes.INTELLIGENCE), 1, 5)

    def speed(self):
        raw_val = self.stat_value(StatTypes.SPEED)
        return Utils.bound(raw_val, 1, self.max_energy())

    def set_ready_to_act(self, val):
        self._ready_to_act = val

    def ready_to_act(self):
        return self._ready_to_act

    def activations_after_n_rounds(self, n):
        e = self.energy()
        res = 0
        for i in range(0, n):
            e += self.speed()
            if e >= self.max_energy():
                res += 1
                e = e % self.max_energy()
        return res

    def turns_until_next_activation(self):
        missing_energy = self.max_energy() - self.energy()
        return round(missing_energy / self.speed() + 0.49999)

    def max_energy(self):
        return 8

    def is_alive(self):
        return self.current_hp > 0

    def set_energy(self, val):
        self.current_energy = Utils.bound(val, 0, self.max_energy())

    def max_hp(self):
        raw_value = self.stat_value(StatTypes.VIT)
        return Utils.bound(raw_value, 1, 999)

    def light_level(self):
        min_level = self.stat_value(StatTypes.MIN_LIGHT_LEVEL)
        cur_level = self.stat_value(StatTypes.LIGHT_LEVEL)

        return Utils.bound(max(min_level, cur_level), 0, 16)

    def inventory(self):
        return self.inventory_

    def name(self):
        return self.name_

    def add_status_effect(self, status_effect):
        self.status_effects[status_effect] = status_effect.get_duration()

        # TODO - the player's actor state should probably know it's the player's actor state.
        if self == gs.get_instance().player_state() and status_effect.get_player_text() is not None:
            dia = dialog.PlayerDialog(status_effect.get_player_text())
            gs.get_instance().dialog_manager().set_dialog(dia)

    def get_turns_remaining(self, status_effect):
        if status_effect not in self.status_effects:
            return 0
        else:
            return self.status_effects[status_effect]

    def all_status_effects(self):
        res = [s for s in self.status_effects]
        res.sort(key=lambda s: self.status_effects[s], reverse=True)
        return res

    def countdown_status_effects(self):
        all_effects = self.all_status_effects()
        for e in all_effects:
            if self.status_effects[e] <= 1:
                del self.status_effects[e]
            else:
                self.status_effects[e] = self.status_effects[e] - 1


class ActorController:

    def get_next_action(self, actor, world):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, position=pos)


class PlayerController(ActorController):

    HIGHEST_PRIORITY = 0
    BASE_PRIORITY = 1
    LOWEST_PRIORITY = 3

    INPUT_BUFFER = 5  # how old requests can be before expiring

    def __init__(self):
        self.current_requests_tick = 0
        self.current_requests = []  # list of (int: priority, Action: action)

    def clear_requests(self):
        self.current_requests.clear()

    def add_requests(self, actions, priority=1):
        cur_tick = gs.get_instance().tick_counter
        if cur_tick != self.current_requests_tick:
            self.current_requests.clear()
            self.current_requests_tick = cur_tick

        actions = Utils.listify(actions)
        for a in actions:
            self.current_requests.append((priority, a))

        # note this relies on python's sort being stable, which I think it always should be?
        self.current_requests.sort(key=lambda v: v[0])

    def get_next_action(self, actor, world):
        current_tick = gs.get_instance().tick_counter
        if current_tick - self.current_requests_tick <= PlayerController.INPUT_BUFFER:
            for (prio, action) in self.current_requests:
                if action.get_actor() is None:
                    # TODO sometimes UI-triggered actions don't have access to the world/player
                    # TODO so they just pass None as a placeholder... it's fine..
                    action.actor_entity = world.get_player()
                if action.get_actor() != actor:
                    print("WARN: player controller given an action for a different actor: {}".format(action.get_actor()))
                    continue
                elif action.is_possible(world):
                    self.current_requests.clear()
                    return action
        else:
            self.current_requests.clear()

        return PlayerWaitAction(actor)


class EnemyController(ActorController):

    def __init__(self):
        ActorController.__init__(self)

    def _get_attack_action(self, actor, world):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
        random.shuffle(neighbors)

        for n in neighbors:
            res = AttackAction(actor, None, n)
            if res.is_possible(world):
                return res

    def _get_pathing_action(self, actor, world):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        skilled_enough = random.random() < balance.ENEMY_PATHING_SKILL[actor.get_actor_state().intelligence() - 1]

        if not world.get_hidden(*pos) and skilled_enough:
            p = world.get_player()
            if p is not None:
                p_pos = world.to_grid_coords(*p.center())
                path = world.get_path_between(pos, p_pos, max_length=balance.ENEMY_SMART_PATHING_RANGE,
                                              cond=lambda xy: (xy == p_pos or xy == pos
                                                               or not world.is_solid(*xy, including_entities=True)))
                if path is not None and len(path) >= 2:
                    res = MoveToAction(actor, path[1])
                    if res.is_possible(world):
                        return res
                    else:
                        print("WARN: world gave {} an impossible path? {}".format(actor.get_actor_state().name, path))

        # otherwise just fallback to dumb movement
        neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
        random.shuffle(neighbors)
        for n in neighbors:
            res = MoveToAction(actor, n)
            if res.is_possible(world):
                return res

    def get_next_action(self, actor, world):
        attack_action = self._get_attack_action(actor, world)
        if attack_action is not None and attack_action.is_possible(world):
            return attack_action

        pathing_action = self._get_pathing_action(actor, world)
        if pathing_action is not None and pathing_action.is_possible(world):
            return pathing_action

        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, position=pos)


class ActionType(Enum):
    MOVE_TO = "MOVE_TO"
    SKIP_DIALOG = "SKIP_DIALOG"
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

    def get_type(self):
        return self.cmd_type

    def get_position(self):
        return self.position

    def get_item(self):
        return self.item

    def get_actor(self):
        return self.actor_entity

    def causes_turn(self):
        """whether the actor should turn towards the target position at the start of this action."""
        return True

    def is_fake_player_wait_action(self):
        return self.get_type() == ActionType.PLAYER_WAIT

    def is_possible(self, world):
        return True

    def animate_in_world(self, progress, world):
        pass

    def get_duration(self):
        return self.anim_duration

    def pre_start(self, world):  # pre-start? this is dumb
        if self.causes_turn() and self.get_position() is not None:
            pos = self.get_actor().center()
            grid_pos = world.to_grid_coords(*pos)
            if grid_pos[0] < self.get_position()[0]:
                self.get_actor().set_facing_right(True)
            elif grid_pos[0] > self.get_position()[0]:
                self.get_actor().set_facing_right(False)

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

        if Utils.dist_manhattan(self.position, pos) != 1:
            return False
        elif world.is_solid(self.position[0], self.position[1], including_entities=True):
            return False

        return True

    def start(self, world):
        self.start_pos = self.actor_entity.center()

    def animate_in_world(self, progress, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))

        new_pos = Utils.linear_interp(self.start_pos, end_pos, progress)
        self.actor_entity.move_to(round(new_pos[0]), round(new_pos[1]))

    def finalize(self, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.actor_entity.set_center(end_pos[0], end_pos[1])


class ConsumeItemAction(Action):

    def __init__(self, actor, item):
        Action.__init__(self, ActionType.CONSUME_ITEM, 40, actor, item=item)
        self._did_anim = False

    def is_possible(self, world):
        if self.item is None or not self.item.can_consume():
            return False

        a_state = self.actor_entity.get_actor_state()
        if self.item not in a_state.inventory():
            return False

        return True

    def start(self, world):
        a_state = self.actor_entity.get_actor_state()
        removed = a_state.inventory().remove(self.item)
        if not removed:
            print("WARN: failed to remove consumable?: {}".format(self.item))

    def animate_in_world(self, progress, world):
        if progress >= 0.6 and not self._did_anim:
            self._did_anim = True
            consume_effect = self.item.get_consume_effect()
            if consume_effect is not None:
                self.actor_entity.perturb_color(consume_effect.get_color(), 30)
                self.actor_entity.set_visually_held_item_override(False)

    def finalize(self, world):
        print("INFO: {} consumed item {}".format(self.actor_entity, self.item))
        consume_effect = self.item.get_consume_effect()
        if consume_effect is not None:
            self.actor_entity.get_actor_state().add_status_effect(consume_effect)
        self.actor_entity.set_visually_held_item_override(None)


class OpenDoorAction(MoveToAction):

    def __init__(self, actor, position):
        MoveToAction.__init__(self, actor, position)
        self.door_entity = None

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])

        if Utils.dist_manhattan(self.position, pos) != 1:
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


def determine_damage_dealt(attacker, defender, item_used=None):
    t_def = defender.stat_value(StatTypes.DEF)
    a_att = attacker.stat_value_with_item(StatTypes.ATT, item_used)

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

    return len(atts)


def apply_damage_and_hit_effects(damage, attacker, defender,
                                 world=None, attacker_entity=None, defender_entity=None, item_used=False):
    if damage <= 0:
        if defender_entity is not None and world is not None:
            world.show_floating_text("miss", colors.B_TEXT_COLOR, 3, defender_entity)
    else:
        defender.set_hp(defender.hp() - damage)

        if defender_entity is not None and world is not None:
            world.show_floating_text("-{}".format(damage), colors.R_TEXT_COLOR, 3, defender_entity)
            defender_entity.perturb_color(colors.R_TEXT_COLOR, 25)
            defender_entity.perturb(20, 18)

        new_status_effects_for_attacker = []

        plus_spd_duration = attacker.stat_value_with_item(StatTypes.PLUS_SPEED_ON_HIT, item_used)
        if plus_spd_duration > 0:
            new_status_effects_for_attacker.append(statuseffects.new_speed_effect(balance.STATUS_EFFECT_PLUS_SPEED_VAL,
                                                                                  plus_spd_duration))

        plus_def_duration = attacker.stat_value_with_item(StatTypes.PLUS_DEFENSE_ON_HIT, item_used)
        if plus_def_duration > 0:
            new_status_effects_for_attacker.append(statuseffects.new_plus_defenses_effect(plus_def_duration))

        if attacker_entity is not None:
            for s in new_status_effects_for_attacker:
                attacker_entity.get_actor_state().add_status_effect(s)

                # TODO - would probably be cool to pulse multiple colors if you get >1 effects
                if s.get_color() is not None:
                    attacker_entity.perturb_color(s.get_color(), 30)


class AttackAction(Action):

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.ATTACK, 24, actor, item=item, position=position)
        self._did_animations = False
        self._results = None  # (int: dmg, ActorEntity: target)

    def is_possible(self, world):
        actor = self.actor_entity
        if self.item is not None:
            if not actor.get_actor_state().inventory().is_equipped(self.item):
                return False

        actor_pos = world.to_grid_coords(actor.center()[0], actor.center()[1])

        attack_range = None
        if self.item is not None:
            for action_prov in self.item.all_actions():
                if action_prov.get_type() == ActionType.ATTACK:
                    # TODO - indicative of bad organization that we're going *back into* the action provider
                    # TODO - to figure out the attack range... but gotta go fast..
                    attack_range = action_prov.get_targets(pos=actor_pos)

        if attack_range is None:
            attack_range = [n for n in Utils.neighbors(*actor_pos)]

        if self.position not in attack_range:
            return False

        if world.is_solid(*self.position):
            return False

        for cell in Utils.cells_between(actor_pos, self.position, include_endpoints=False):
            # can't be attacking through walls and actors and such
            if world.is_solid(cell[0], cell[1], including_entities=True):
                return False

        target = world.get_actor_in_cell(self.position[0], self.position[1])
        if target is None or target.get_actor_state().alignment == actor.get_actor_state().alignment:
            return False

        return True

    def _apply_attack_and_add_animations_if_necessary(self, world):
        if not self._did_animations:
            self._did_animations = True
            damage = self._results[0]
            target = self._results[1]
            attacker = self.get_actor().get_actor_state()
            defender = target.get_actor_state()

            apply_damage_and_hit_effects(damage, attacker, defender,
                                         attacker_entity=self.get_actor(), defender_entity=target,
                                         world=world, item_used=self.item)

    def start(self, world):
        target = world.get_actor_in_cell(self.position[0], self.position[1])
        t_state = target.get_actor_state()
        a_state = self.get_actor().get_actor_state()
        dmg_dealt = determine_damage_dealt(a_state, t_state, item_used=self.item)

        self._results = (dmg_dealt, target)

    def animate_in_world(self, progress, world):
        run_at_pct = 0.3
        recover_pcnt = 1 - run_at_pct

        start_at = self.actor_entity.center()
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

        pre_move_offset = self.actor_entity.get_draw_offset()
        new_move_offset = Utils.sub(new_pos, self.actor_entity.center())
        vel = Utils.sub(new_move_offset, pre_move_offset)

        self.actor_entity.set_draw_offset(*new_move_offset)
        self.actor_entity.set_vel(vel)

    def finalize(self, world):
        self._apply_attack_and_add_animations_if_necessary(world)
        self.actor_entity.set_draw_offset(0, 0)
        self.actor_entity.set_vel((0, 0))

        attack_vec = Utils.sub(self._results[1].center(), self.actor_entity.center())

        if attack_vec[0] < -world.cellsize() // 2:
            self.actor_entity.set_facing_right(False)
            if self._results[0] > 0:
                self._results[1].set_facing_right(True)

        elif attack_vec[0] > world.cellsize() // 2:
            self.actor_entity.set_facing_right(True)
            if self._results[0] > 0:
                self._results[1].set_facing_right(False)


class ThrowItemAction(Action):

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.THROW_ITEM, 40, actor, item=item, position=position)
        self._results = None
        self._did_animations = False

        self._thrown_item_entity = None

    def is_possible(self, world):
        if self.item is None or not self.item.can_throw():
            return False

        actor = self.actor_entity
        a_state = actor.get_actor_state()
        if not (self.item in a_state.inventory() or a_state.held_item == self.item):
            return False

        actor_pos = world.to_grid_coords(actor.center()[0], actor.center()[1])

        throw_range = [n for n in Utils.neighbors(*actor_pos)] + \
                      [n for n in Utils.neighbors(*actor_pos, dist=2)]

        if self.position not in throw_range:
            return False

        if world.is_solid(*self.position):
            return False

        for cell in Utils.cells_between(actor_pos, self.position, include_endpoints=False):
            # can't be attacking through walls and actors and such
            if world.is_solid(cell[0], cell[1], including_entities=True):
                return False

        target = world.get_actor_in_cell(self.position[0], self.position[1])
        if target is None or target.get_actor_state().alignment == actor.get_actor_state().alignment:
            return False

        return True

    def _apply_attack_and_add_animations_if_necessary(self, world):
        if not self._did_animations:
            self._did_animations = True
            damage = self._results[0]
            target = self._results[1]
            attacker = self.get_item()  # again, pretending the "attacker" is only wearing the item.
            defender = target.get_actor_state()

            apply_damage_and_hit_effects(damage, attacker, defender,
                                         attacker_entity=None, defender_entity=target,
                                         world=world, item_used=self.item)

            consume_effect = self.item.get_consume_effect()
            if damage >= 0 and consume_effect is not None:
                target.perturb_color(consume_effect.get_color(), 30)
                target.get_actor_state().add_status_effect(consume_effect)

    def start(self, world):
        a_state = self.actor_entity.get_actor_state()

        removed = a_state.inventory().remove(self.item)
        if not removed:
            if a_state.held_item == self.item:
                a_state.held_item = None
                removed = True

        if not removed:
            print("WARN: failed to remove thrown item: {}".format(self.item))

        target = world.get_actor_in_cell(self.position[0], self.position[1])
        t_state = target.get_actor_state()

        # here's how a thrown's item damage is calculated:
        # it's as if the "attacker" is an actor with only the item equipped and nothing else,
        # attacking the target using the item. so basically it uses the global and local stats
        # on the thrown item and nothing else to apply damage.
        dummy_attack_state = self.item

        dmg_dealt = determine_damage_dealt(dummy_attack_state, t_state, item_used=self.item)

        # although, all that being said, we do want to force damage to be non-zero.
        # otherwise on-hit effects won't trigger because it'd be a miss.
        dmg_dealt = max(1, dmg_dealt)

        self._results = (dmg_dealt, target)

    def animate_in_world(self, progress, world):
        release_time = 0.3

        if progress >= release_time:
            item_sprite = self.get_item().get_entity_sprite()
            if item_sprite is None:
                return  # items should probably always have sprites but idk

            # can't be holding the item while it's flying through the air
            self.actor_entity.set_visually_held_item_override(False)

            start_pos = self.actor_entity.center()
            end_pos = Utils.mult(Utils.add(self.get_position(), (0.5, 0.5)), world.cellsize())

            if self._thrown_item_entity is None:
                from src.world.entities import AnimationEntity
                self._thrown_item_entity = AnimationEntity(start_pos[0], start_pos[1], [item_sprite], 1,
                                                           spriteref.ENTITY_LAYER, scale=2)
                self._thrown_item_entity.set_finish_behavior(AnimationEntity.FREEZE_ON_FINISH)
                self._thrown_item_entity.set_color(self.get_item().get_color())
                self._thrown_item_entity.set_shadow_sprite(spriteref.small_shadow)
                world.add(self._thrown_item_entity)

            airtime_prog = (progress - release_time) / (1 - release_time)

            pos = Utils.linear_interp(start_pos, end_pos, airtime_prog)
            self._thrown_item_entity.move_to(pos[0], pos[1])

            x = airtime_prog

            # heights at x = 0.0, 0.5, and 1.0 respectively
            y1 = 48  # TODO - start at actor's actual height
            y2 = 64
            y3 = 16

            # trust me on this
            a = 2*y1 - 4*y2 + 2*y3
            b = -3*y1 + 4*y2 - y3
            c = y1

            h = a*x*x + b*x + c

            self._thrown_item_entity.set_sprite_offset((0, -h))

            # make it spin through the air
            rot = (self.get_item().sprite_rotation() + int(airtime_prog * 6)) % 4
            self._thrown_item_entity.set_rotation(rot)

    def finalize(self, world):
        if self._thrown_item_entity is not None:
            from src.world.entities import AnimationEntity
            pos = self._thrown_item_entity.center()
            splosion = AnimationEntity(pos[0], pos[1], spriteref.explosions, 20, spriteref.ENTITY_LAYER, scale=3)
            splosion.set_color(self.get_item().get_color())
            splosion.set_sprite_offset((0, -16))

            world.remove(self._thrown_item_entity)
            world.add(splosion)

        self._apply_attack_and_add_animations_if_necessary(world)
        self.actor_entity.set_draw_offset(0, 0)
        self.actor_entity.set_vel((0, 0))

        attack_vec = Utils.sub(self._results[1].center(), self.actor_entity.center())

        if attack_vec[0] < -world.cellsize() // 2:
            self.actor_entity.set_facing_right(False)
            if self._results[0] > 0:
                self._results[1].set_facing_right(True)

        elif attack_vec[0] > world.cellsize() // 2:
            self.actor_entity.set_facing_right(True)
            if self._results[0] > 0:
                self._results[1].set_facing_right(False)

        self.actor_entity.set_visually_held_item_override(None)


class SkipTurnAction(Action):

    def __init__(self, actor, position):
        Action.__init__(self, ActionType.SKIP_TURN, 10, actor, position=position)

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])
        return pos == self.position


class InteractAction(Action):

    def __init__(self, actor, position):
        Action.__init__(self, ActionType.INTERACT, 10, actor, position=position)
        self.target = None

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])
        if Utils.dist_manhattan(pos, self.position) != 1:
            return False

        return world.get_interactable_in_cell(self.position[0], self.position[1]) is not None

    def start(self, world):
        self.target = world.get_interactable_in_cell(self.position[0], self.position[1])
        print("INFO: interacted with {}".format(self.target))
        self.target.interact(world)

    def animate_in_world(self, world, progress):
        pass

    def finalize(self, world):
        pass


class PlayerWaitAction(Action):

    def __init__(self, actor, position=None):
        Action.__init__(self, ActionType.PLAYER_WAIT, 1, actor, position=position)

    def causes_turn(self):
        return True

    def is_possible(self, world):
        return True


class ActionProvider:

    def __init__(self, name, action_type, target_dists=(0,), icon_sprite=None, color=(1, 1, 1),
                 needs_to_be_equipped=False):
        self.name = name
        self.color = color
        self.action_type = action_type
        self.target_dists = target_dists
        self.icon_sprite = icon_sprite
        self.needs_to_be_equipped = needs_to_be_equipped

    def is_mappable(self):
        """Whether the action can be mapped to the action hotbar."""
        return False

    def needs_equipped(self):
        return False

    def get_icon(self):
        return self.icon_sprite

    def get_item(self):
        return None

    def get_type(self):
        return self.action_type

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_target_dists(self):
        return self.target_dists

    def get_targets(self, pos=(0, 0)):
        for r in self.target_dists:
            if r == 0:
                yield (pos[0], pos[1])
            else:
                for n in Utils.neighbors(pos[0], pos[1], dist=r):
                    yield n

    def get_action(self, actor, position=None, item=None):
        return SkipTurnAction()


class ItemActionProvider(ActionProvider):

    def __init__(self, item, action_provider):
        ActionProvider.__init__(self, None, None)
        self.item = item
        self.action_provider = action_provider

    def __eq__(self, other):
        if isinstance(other, ItemActionProvider):
            return self.item == other.item and self.action_provider == other.action_provider
        else:
            return False

    def is_mappable(self):
        """Whether the action can be mapped to the action hotbar."""
        return self.action_provider.is_mappable()

    def get_type(self):
        return self.action_provider.get_type()

    def get_item(self):
        return self.item

    def needs_equipped(self):
        return self.action_provider.needs_equipped()

    def get_icon(self):
        return self.action_provider.get_icon()

    def get_name(self):
        return self.action_provider.get_name()

    def get_color(self):
        return self.action_provider.get_color()

    def get_target_dists(self):
        return self.action_provider.get_target_dists()

    def get_targets(self, pos=(0, 0)):
        return self.action_provider.get_targets(pos=pos)

    def get_action(self, actor, position=None, item=None):
        if item is not None:
            raise ValueError("Cannot pass an item to an ItemActionProvider: {}".format(item))
        return self.action_provider.get_action(actor, position=position, item=self.item)


class ConsumeItemActionProvider(ActionProvider):

    def __init__(self):
        ActionProvider.__init__(self, "Drink", ActionType.CONSUME_ITEM, color=(0.5, 1, 0.5))

    def get_action(self, actor, position=None, item=None):
        return ConsumeItemAction(actor, item)


class AttackItemActionProvider(ActionProvider):

    def __init__(self, name, icon, target_dists, color=colors.RED):
        ActionProvider.__init__(self, name, ActionType.ATTACK, icon_sprite=icon,
                                target_dists=target_dists, color=color, needs_to_be_equipped=True)

    def is_mappable(self):
        return True

    def needs_equipped(self):
        return True

    def get_action(self, actor, position=None, item=None):
        return AttackAction(actor, item, position)


class ItemActions:
    CONSUME_ITEM = ConsumeItemActionProvider()
    SWORD_ATTACK = AttackItemActionProvider("Sword Attack", spriteref.Items.sword_icon, (1,))
    SPEAR_ATTACK = AttackItemActionProvider("Spear Attack", spriteref.Items.spear_icon, (1, 2))
    WHIP_ATTACK = AttackItemActionProvider("Whip Attack", spriteref.Items.whip_icon, (1,))
    SHIELD_ATTACK = AttackItemActionProvider("Shield Bash", spriteref.Items.shield_icon, (1,))
    DAGGER_ATTACK = AttackItemActionProvider("Dagger Attack", spriteref.Items.dagger_icon, (1,))
    BOW_ATTACK = AttackItemActionProvider("Bow Shot", spriteref.Items.bow_icon, (2, 3))
    AXE_ATTACK = AttackItemActionProvider("Axe Attack", spriteref.Items.axe_icon, (1,))
    UNARMED_ATTACK = AttackItemActionProvider("Slap", spriteref.Items.unarmed_icon, (1,))



