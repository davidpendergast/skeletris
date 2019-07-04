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
import src.game.debug as debug


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

        self.unarmed_projectile_sprite = None

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
        res = self.base_stats.stat_value(stat_type, local=local)
        for item in self.inventory().all_equipped_items():
            res += item.stat_value(stat_type, local=local)

        # note that this will call back into this same method, gotta be careful not to blow the stack
        nullified = self.is_nullified() if stat_type != StatTypes.NULLIFICATION else False

        for perm_effect in self.permanent_effects:
            if not nullified or perm_effect.ignores_nullification():
                res += perm_effect.stat_value(stat_type, local=local)

        for status_effect in self.status_effects:
            if not nullified or status_effect.ignores_nullification():
                res += status_effect.stat_value(stat_type, local=local)

        return res

    def hp(self):
        return self.current_hp

    def turn_duration_modifier(self, action_type):
        if self.alignment == 0:
            return 1.0
        else:
            if action_type == ActionType.MOVE_TO:
                return 0.66
            else:
                return 0.85

    def set_hp(self, val):
        new_hp = min(val, self.max_hp())

        # just a debug thing, don't worry about it
        if self.alignment == 0 and debug.player_cant_die():
            new_hp = max(1, new_hp)

        self.current_hp = new_hp

    def energy(self):
        return self.current_energy

    def intelligence(self):
        return Utils.bound(self.stat_value(StatTypes.INTELLIGENCE), 1, 5)

    def unarmed_range(self):
        return Utils.bound(self.stat_value(StatTypes.UNARMED_RANGE), 1, 8)

    def is_confused(self):
        return self.stat_value(StatTypes.CONFUSION) > 0

    def get_projectile_sprite(self):
        return self.unarmed_projectile_sprite

    def speed(self):
        raw_val = self.stat_value(StatTypes.SPEED)
        return Utils.bound(raw_val, 1, self.max_energy())

    def is_nullified(self):
        return self.stat_value(StatTypes.NULLIFICATION) > 0

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
        nullified = self.is_nullified()

        for e in all_effects:
            if self.status_effects[e] <= 1 or (nullified and not e.ignores_nullification()):
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

    def get_best_actions_for_position(self, actor, world, position, using_keyboard=True):
        pass


class EnemyController(ActorController):

    def __init__(self):
        ActorController.__init__(self)

    def _get_positions_to_attack(self, actor, world):
        res = []
        for nearby_actor in world.entities_in_circle(actor.center(), 400,
                                                     onscreen=False, cond=lambda e: e.is_actor()):
            if nearby_actor.get_actor_state().alignment != actor.get_actor_state().alignment:
                nearby_actor_center = nearby_actor.center()
                res.append(world.to_grid_coords(nearby_actor_center[0], nearby_actor_center[1]))

        actor_pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        res.sort(key=lambda pos: Utils.dist_manhattan(pos, actor_pos))

        return res

    def _get_attack_action(self, actor, world):
        target_positions = self._get_positions_to_attack(actor, world)
        if len(target_positions) == 0:
            return None

        # smart enemies use their items to attack
        a_state = actor.get_actor_state()
        if a_state.intelligence() >= 5:
            import src.items.item as item
            weapons = []
            for it in a_state.inventory().all_equipped_items():
                if item.ItemTags.WEAPON in it.get_tags():
                    weapons.append(it)
            random.shuffle(weapons)

            for wep in weapons:
                for target in target_positions:
                    res = AttackAction(actor, wep, target)
                    if res.is_possible(world):
                        return res

        # falling back to an unarmed attack
        for target in target_positions:
            res = AttackAction(actor, None, target)
            if res.is_possible(world):
                return res

    def _get_movement_action(self, actor, world):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        skilled_enough = random.random() < balance.ENEMY_PATHING_SKILL[actor.get_actor_state().intelligence() - 1]

        if actor.get_actor_state().is_confused() and random.random() < balance.CONFUSION_CHANCE:
            skilled_enough = False

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

        movement_action = self._get_movement_action(actor, world)
        if movement_action is not None and movement_action.is_possible(world):
            return movement_action

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

    def __repr__(self):
        item_name = None if self.item is None else self.item.get_title()
        return "{}[actor={}, position={}, item={}]".format(
            type(self).__name__, self.actor_entity, self.position, item_name
        )

    def get_type(self):
        return self.cmd_type

    def get_position(self):
        return self.position

    def get_item(self):
        return self.item

    def get_actor(self):
        return self.actor_entity

    def get_targeting_color(self, for_mouse=False):
        """returns: the targeting color this action should use."""
        return None

    def causes_turn(self):
        """whether the actor should turn towards the target position at the start of this action."""
        return True

    def is_free(self):
        """Whether the action can be used without ending the actor's turn."""
        return False

    def is_possible(self, world):
        return True

    def is_move_action(self):
        return self.get_type() == ActionType.MOVE_TO

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
        Action.__init__(self, ActionType.MOVE_TO, 22, actor, position=position)
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

    def get_targeting_color(self, for_mouse=False):
        consume_effect = self.get_item().get_consume_effect()
        if consume_effect is not None:
            return consume_effect.get_color()
        else:
            return (1, 1, 1)

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

        door_to_open = world.get_door_in_cell(*self.position)

        if door_to_open is None or not door_to_open.can_open(world):
            return False

        return True

    def start(self, world):
        super().start(world)
        self.door_entity = world.   get_door_in_cell(*self.position)

    def animate_in_world(self, progress, world):
        super().animate_in_world(progress, world)
        self.door_entity.set_open_progress_for_render(progress)

    def finalize(self, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.door_entity.remove_self_from_world(world)
        self.actor_entity.set_center(end_pos[0], end_pos[1])


def determine_damage_dealt(attacker, defender, item_used=None, is_thrown=False):
    t_def = defender.stat_value(StatTypes.DEF)

    if not is_thrown:
        a_att = attacker.stat_value_with_item(StatTypes.ATT, item_used)
    elif item_used is not None:
        a_att = item_used.stat_value(StatTypes.ATT, local=False)
        a_att += item_used.stat_value(StatTypes.ATT, local=True)
        a_att += attacker.stat_value_with_item(StatTypes.THROWN_ATT, item_used)
    else:
        a_att = 0  # idk

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

            if defender.hp() > 0:
                # it looks pretty janky if the enemy perturbs a single frame before disappearing
                defender_entity.perturb_color(colors.R_TEXT_COLOR, 25)
                defender_entity.perturb(20, 18)

        new_status_effects_for_attacker = []

        plus_spd_duration = attacker.stat_value_with_item(StatTypes.PLUS_SPEED_ON_HIT, item_used)
        if plus_spd_duration > 0:
            new_status_effects_for_attacker.append(statuseffects.new_speed_effect(balance.STATUS_EFFECT_PLUS_SPEED_VAL,
                                                                                  plus_spd_duration,
                                                                                  unique_key="plus_speed_from_item"))

        plus_def_duration = attacker.stat_value_with_item(StatTypes.PLUS_DEFENSE_ON_HIT, item_used)
        if plus_def_duration > 0:
            new_status_effects_for_attacker.append(statuseffects.new_plus_defenses_effect(plus_def_duration,
                                                                                          unique_key="plus_defense_from_item"))

        if attacker_entity is not None:
            for s in new_status_effects_for_attacker:
                attacker_entity.get_actor_state().add_status_effect(s)

                # TODO - would probably be cool to pulse multiple colors if you get >1 effects
                if s.get_color() is not None:
                    attacker_entity.perturb_color(s.get_color(), 30)

        new_status_effects_for_defender = []

        pois_duration = attacker.stat_value_with_item(StatTypes.POISON_ON_HIT, item_used)
        pois_dmg = balance.POTION_POIS_VAL
        if pois_duration > 0 and pois_dmg > 0:
            new_status_effects_for_defender.append(statuseffects.new_poison_effect(pois_dmg, pois_duration))

        confuse_duration = attacker.stat_value_with_item(StatTypes.CONFUSION_ON_HIT, item_used)
        if confuse_duration > 0:
            new_status_effects_for_defender.append(statuseffects.new_confusion_effect(confuse_duration))

        if defender_entity is not None:
            for s in new_status_effects_for_defender:
                defender_entity.get_actor_state().add_status_effect(s)
                if s.get_color() is not None:
                    defender_entity.perturb_color(s.get_color(), 30)


class AttackAction(Action):

    def __init__(self, actor, item, position):
        self._projectile_sprite = AttackAction._calc_projectile_sprite(actor, item)
        duration = 24 if self._projectile_sprite is None else 40

        Action.__init__(self, ActionType.ATTACK, duration, actor, item=item, position=position)
        self._did_animations = False
        self._results = None  # (int: dmg, ActorEntity: target)

        self._projectile_animator = None  # only used when it's a projectile attack

    @staticmethod
    def _calc_projectile_sprite(actor, item):
        if item is None:
            return actor.get_actor_state().get_projectile_sprite()
        else:
            return item.get_projectile_sprite()

    def get_targeting_color(self, for_mouse=False):
        return colors.RED

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
            unarmed_range = actor.get_actor_state().unarmed_range()
            attack_range = []
            for i in range(1, unarmed_range + 1):
                for n in Utils.neighbors(*actor_pos, dist=i):
                    attack_range.append(n)

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
        dmg_dealt = determine_damage_dealt(a_state, t_state, item_used=self.item, is_thrown=False)

        self._results = (dmg_dealt, target)

    def animate_in_world(self, progress, world):
        if self._projectile_sprite is not None:
            if self._projectile_animator is None:

                # TODO obviously a dumb way to get the projectile's sprite
                from src.items.item import ItemTypes
                if self.get_item() is not None and self.get_item().get_type() == ItemTypes.BOW_WEAPON:
                    projectile_sprite = spriteref.Items.arrow_projectile_small
                else:
                    projectile_sprite = spriteref.Items.projectile_small

                self._projectile_animator = _ThrownItemAnimator(self.get_actor(),
                                                                self.get_position(),
                                                                self._projectile_sprite,
                                                                colors.WHITE,  # TODO - better color choosing
                                                                hide_actor_held_item=False)
            self._projectile_animator.animate_in_world(progress, world)
        else:
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
        if self._projectile_animator is not None:
            self._projectile_animator.finalize(world)

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


class _ThrownItemAnimator:

    def __init__(self, actor, position, item_sprite, item_color, hide_actor_held_item=False, item_start_rotation=0):
        self._actor = actor
        self._position = position
        self._hide_actor_held_item = hide_actor_held_item
        self._thrown_item_entity = None
        self._item_sprite = item_sprite
        self._item_color = item_color
        self._item_start_rotation = item_start_rotation

        self._did_jump = False

    def animate_in_world(self, progress, world):

        release_time = 0.3
        if progress >= release_time:
            if self._item_sprite is None:
                return  # items should probably always have sprites but idk

            # can't be holding the item while it's flying through the air
            if self._hide_actor_held_item:
                self._actor.set_visually_held_item_override(False)

            if not self._did_jump:
                self._did_jump = True
                self._actor.perturb_z(jump_height=20, jump_duration=15)

            start_pos = self._actor.center()
            end_pos = Utils.mult(Utils.add(self._position, (0.5, 0.5)), world.cellsize())

            if self._thrown_item_entity is None:
                from src.world.entities import AnimationEntity
                self._thrown_item_entity = AnimationEntity(start_pos[0], start_pos[1], [self._item_sprite], 1,
                                                           spriteref.ENTITY_LAYER, scale=2)
                self._thrown_item_entity.set_finish_behavior(AnimationEntity.FREEZE_ON_FINISH)
                self._thrown_item_entity.set_color(self._item_color)
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
            a = 2 * y1 - 4 * y2 + 2 * y3
            b = -3 * y1 + 4 * y2 - y3
            c = y1

            h = a * x * x + b * x + c

            self._thrown_item_entity.set_sprite_offset((0, -h))

            # make it spin through the air
            rot = (self._item_start_rotation + int(airtime_prog * 6)) % 4
            self._thrown_item_entity.set_rotation(rot)

    def finalize(self, world):
        if self._thrown_item_entity is not None:
            pos = self._thrown_item_entity.center()
            world.show_explosion(pos[0], pos[1], 20, color=self._item_color, offs=(0, -16), scale=3)

            world.remove(self._thrown_item_entity)


class ThrowItemAction(Action):

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.THROW_ITEM, 40, actor, item=item, position=position)
        self._results = None
        self._did_animations = False

        self._thrown_item_animator = None

    def get_targeting_color(self, for_mouse=False):
        consume_effect = self.get_item().get_consume_effect()
        if consume_effect is not None:
            return consume_effect.get_color()
        else:
            return colors.RED

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

            # we only want on-hit effects that living on the thrown item to apply
            # and we don't want any on-hit effects to go back to the thrower (I think?)
            attacker = self.get_item()

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

        dmg_dealt = determine_damage_dealt(a_state, t_state, item_used=self.item, is_thrown=True)

        # force damage to be non-zero, otherwise on-hit effects won't trigger because it'd be a miss.
        dmg_dealt = max(1, dmg_dealt)

        self._results = (dmg_dealt, target)

    def animate_in_world(self, progress, world):
        if self._thrown_item_animator is None:
            self._thrown_item_animator = _ThrownItemAnimator(self.get_actor(),
                                                             self.get_position(),
                                                             self.get_item().get_entity_sprite(),
                                                             self.get_item().get_color(),
                                                             hide_actor_held_item=True,
                                                             item_start_rotation=self.get_item().sprite_rotation())

        self._thrown_item_animator.animate_in_world(progress, world)

    def finalize(self, world):
        if self._thrown_item_animator is not None:
            self._thrown_item_animator.finalize(world)

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

    def get_targeting_color(self, for_mouse=False):
        if for_mouse:
            return (1, 1, 1)
        else:
            return (1, 1, 1)

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

    def is_free(self):
        return True

    def is_possible(self, world):
        return True


class PickUpItemAction(Action):

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.PICKUP_ITEM, 1, actor, item=item, position=position)

    def causes_turn(self):
        return True

    def is_free(self):
        return True

    def _get_entity_to_pickup(self, world):
        pos = self.get_position()
        ents_in_cell = world.get_entities_in_cell(pos[0], pos[1],
                                                  cond=lambda e: e.is_item() and e.get_item() == self.get_item())
        if len(ents_in_cell) == 0:
            return None

        return ents_in_cell[0]

    def is_possible(self, world):
        actor = self.get_actor()
        a_state = actor.get_actor_state()

        if a_state.held_item is not None:
            return False

        ent_to_pickup = self._get_entity_to_pickup(world)

        if ent_to_pickup is None:
            return False

        if not ent_to_pickup.can_pickup(world, actor):
            return None

        a_pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        dxy = Utils.sub(a_pos, self.get_position())
        if abs(dxy[0]) > 1 or abs(dxy[1]) > 1:
            return False

        return True

    def finalize(self, world):
        ent_to_pickup = self._get_entity_to_pickup(world)
        if ent_to_pickup is None:
            print("ERROR: item we wanted to pick up isn't there anymore? {}".format(self.get_item()))
        else:
            self.get_actor().get_actor_state().held_item = ent_to_pickup.get_item()
            world.remove(ent_to_pickup)


class DropItemAction(Action):

    def __init__(self, actor, item, drop_dir=None):
        Action.__init__(self, ActionType.DROP_ITEM, 1, actor, item=item)
        self._drop_dir = drop_dir

    def is_free(self):
        return True

    def is_possible(self, world):
        actor = self.get_actor()
        a_state = actor.get_actor_state()

        if a_state.held_item is None:
            if self.get_item() not in a_state.inventory:
                return False
        elif a_state.held_item != self.get_item():
            return False

        return True

    def start(self, world):
        if self._drop_dir is not None:
            if self._drop_dir[0] > 0.1:
                self.get_actor().set_facing_right(True)
            elif self._drop_dir[0] < -0.1:
                self.get_actor().set_facing_right(False)

    def finalize(self, world):
        actor = self.get_actor()
        a_state = actor.get_actor_state()
        if a_state.held_item == self.get_item():
            a_state.held_item = None
        else:
            a_state.inventory().remove(self.get_item())

        world.add_item_as_entity(self.get_item(), actor.center(), direction=self._drop_dir)


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

        if not isinstance(target_dists, tuple):
            # i don't trust myself to not typo this
            raise ValueError("target_dists needs to be a tuple. instead got {}".format(target_dists))

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
    SPEAR_ATTACK = AttackItemActionProvider("Spear Attack", spriteref.Items.spear_icon, (1,))
    WHIP_ATTACK = AttackItemActionProvider("Whip Attack", spriteref.Items.whip_icon, (1,))
    WAND_ATTACK = AttackItemActionProvider("Wand Attack", spriteref.Items.magic_icon, (1, 2))
    SHIELD_ATTACK = AttackItemActionProvider("Shield Bash", spriteref.Items.shield_icon, (1,))
    DAGGER_ATTACK = AttackItemActionProvider("Dagger Attack", spriteref.Items.dagger_icon, (1,))
    BOW_ATTACK = AttackItemActionProvider("Bow Shot", spriteref.Items.bow_icon, (2, 3))
    AXE_ATTACK = AttackItemActionProvider("Axe Attack", spriteref.Items.axe_icon, (1,))
    UNARMED_ATTACK = AttackItemActionProvider("Slap", spriteref.Items.unarmed_icon, (1,))



