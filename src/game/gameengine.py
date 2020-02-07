from src.utils.util import Utils
import src.game.globalstate as gs
import src.game.settings as settings
import src.game.spriteref as spriteref
from src.game.stats import StatTypes
import src.utils.colors as colors
import src.game.statuseffects as statuseffects
import src.game.balance as balance
from src.game.stats import StatProvider
import src.game.debug as debug
import src.game.events as events
import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
import src.game.constants as constants


import random


class ActorState(StatProvider):

    def __init__(self, name, level, base_stats, inventory, alignment, is_player):
        self.name_ = name
        self.level = level
        self.base_stats = base_stats

        self._is_player = is_player

        self.inventory_ = inventory

        self.status_effects = {}  # StatusEffectType -> turns remaining

        self.current_hp = self.max_hp()
        self.current_energy = 0

        self._ready_to_act = False

        self.alignment = alignment  # what "team" the actor is on.

    def get_all_mappable_action_providers(self):
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

        for status_effect in self.status_effects:
            res += status_effect.stat_value(stat_type, local=local)

        if self.is_player() and debug.insta_kill() and stat_type == StatTypes.ATT:
            res += 99

        return res

    def get_att_value_with_active_weapon(self):
        if self.is_player(): # enemies can't use weapons... (yet?)
            active_action = gs.get_instance().get_targeting_action_provider()
            if active_action is not None and active_action.get_type() == ActionType.ATTACK:

                action_item = self.get_item_in_possession_with_uid(active_action.get_item_uid())
                if action_item is not None:
                    return self.stat_value_with_item(StatTypes.ATT, action_item)

        return self.stat_value(StatTypes.UNARMED_ATT) + self.stat_value(StatTypes.ATT)

    def is_player(self):
        return self._is_player

    def hp(self):
        return min(self.current_hp, self.max_hp())

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
        if self.is_player() and debug.player_cant_die():
            new_hp = max(1, new_hp)

        self.current_hp = new_hp

    def energy(self):
        return self.current_energy

    def intelligence(self):
        return Utils.bound(self.stat_value(StatTypes.INTELLIGENCE), 1, 5)

    def unarmed_range(self):
        return Utils.bound(self.stat_value(StatTypes.UNARMED_RANGE), 1, 8)

    def unarmed_is_projectile(self):
        return self.stat_value(StatTypes.UNARMED_IS_PROJECTILE) > 0

    def is_confused(self):
        return self.stat_value(StatTypes.CONFUSION) > 0

    def is_grasped(self):
        return self.stat_value(StatTypes.GRASPED) > 0

    def is_flinched(self):
        return self.stat_value(StatTypes.FLINCHED) > 0

    def speed(self):
        raw_val = self.stat_value(StatTypes.SPEED)
        return Utils.bound(raw_val, 1, self.max_energy())

    def is_nullified(self):
        return self.stat_value(StatTypes.NULLIFICATION) > 0

    def is_unflinching(self):
        return self.stat_value(StatTypes.UNFLINCHING) > 0

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

    def get_item_in_possession_with_uid(self, item_uid):
        if item_uid is None:
            return None

        held_item = gs.get_instance().held_item() if self.is_player() else None
        if held_item is not None and held_item.get_uid() == item_uid:
            return held_item

        for it in self.inventory().all_items():
            if it.get_uid() == item_uid:
                return it
        return None

    def name(self):
        return self.name_

    def try_to_add_status_effect(self, effect, duration):
        """
        effect: the StatusEffectType to add
        duration: the new effect's duration.
        return: bool indicating whether the addition was successful
        """
        if duration < 0:
            return False

        if effect in self.status_effects:
            self.status_effects[effect] = max(duration, self.status_effects[effect])
            return True
        else:
            for cur_effect in self.status_effects:
                if effect.is_blocked_by(cur_effect):
                    return False

            if self.is_unflinching() and effect.is_blocked_by(statuseffects.StatusEffectTypes.FLINCH_RESIST):
                return False

            if self.is_nullified() and effect.is_blocked_by(statuseffects.StatusEffectTypes.NULLIFICATION):
                return False

            blocked = []

            for cur_effect in self.status_effects:
                if cur_effect.is_blocked_by(effect):
                    blocked.append(cur_effect)

            for eff in blocked:
                del self.status_effects[eff]

            self.status_effects[effect] = duration
            return True

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

        add_flinch_recovery = False

        for e in all_effects:
            expired = self.status_effects[e] <= 1

            if expired:
                del self.status_effects[e]

                if e == statuseffects.StatusEffectTypes.FLINCHED:
                    add_flinch_recovery = True
            else:
                self.status_effects[e] = self.status_effects[e] - 1

        if add_flinch_recovery:
            flinch_recovery_dur = self.stat_value(StatTypes.FLINCH_RESIST)
            if flinch_recovery_dur > 0:
                self.try_to_add_status_effect(statuseffects.StatusEffectTypes.FLINCH_RESIST, flinch_recovery_dur)

    def clear_all_status_effects(self):
        self.status_effects.clear()


class ActorController:

    def get_actual_next_action(self, actor, world):
        """This is where action-mutating status effects are applied."""

        next_action = self.get_next_action(actor, world)

        if next_action.is_free():
            return next_action

        a_state = actor.get_actor_state()
        a_pos = world.to_grid_coords(*actor.center())
        import src.game.stats as stats

        if a_state.is_flinched() and not next_action.is_skip_turn_action():
            return SkipTurnAction(actor, a_pos, perturb_color=stats.StatTypes.FLINCHED.get_color(), intentional=False)

        # intentionally still letting you do things like lunge-attack while grasped, for flavor...
        if a_state.is_grasped() and next_action.is_move_action():
            return SkipTurnAction(actor, a_pos, perturb_color=stats.StatTypes.GRASPED.get_color(), intentional=False)

        if a_state.is_confused() and next_action.is_move_action():
            if random.random() < balance.CONFUSION_CHANCE:
                pos = next_action.get_position()
                neighbors = [n for n in Utils.neighbors(a_pos[0], a_pos[1]) if n != pos]
                random.shuffle(neighbors)
                for n in neighbors:
                    if actor.is_player():
                        open_door_action = OpenDoorAction(actor, n, perturb_color=stats.StatTypes.CONFUSION.get_color())
                        if open_door_action.is_possible(world):
                            return open_door_action
                    move_action = MoveToAction(actor, n, perturb_color=stats.StatTypes.CONFUSION.get_color())
                    if move_action.is_possible(world):
                        return move_action

        return next_action

    def get_next_action(self, actor, world):
        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, pos)


class NullController(ActorController):

    def __init__(self, silent=False):
        self.is_silent = silent

    def get_next_action(self, actor, world):
        if self.is_silent:
            return SilentSkipTurnAction(actor)
        else:
            pos = world.to_grid_coords(*actor.center())
            return SkipTurnAction(actor, pos)


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

    def _get_nearby_positions_with_actors(self, actor, world, same_alignment=None, min_dist=None, max_dist=None):
        res = []

        actor_pos = world.to_grid_coords(*actor.center())
        for nearby_actor in world.entities_in_circle(actor.center(), 400, onscreen=False,
                                                     cond=lambda e: e is not actor and e.is_actor()):

            has_same_alignment = (nearby_actor.get_actor_state().alignment == actor.get_actor_state().alignment)
            if same_alignment is None or has_same_alignment == same_alignment:

                nearby_actor_pos = world.to_grid_coords(*nearby_actor.center())
                dist = Utils.dist_manhattan(actor_pos, nearby_actor_pos)
                if (min_dist is None or min_dist <= dist) and (max_dist is None or dist <= max_dist):
                    res.append(nearby_actor_pos)

        res.sort(key=lambda pos: Utils.dist_manhattan(pos, actor_pos))

        return res

    def _get_attack_action(self, actor, world):

        target_positions = self._get_nearby_positions_with_actors(actor, world, same_alignment=False)
        if len(target_positions) == 0:
            return None

        # smart enemies use their items to attack
        # TODO - need to think hard about this. player has no way of knowing what items an enemy has,
        # TODO - so from their POV it would just hit way harder for seemingly no reason. scrap this?
        # TODO - well a diligent player could read the enemy's stats...
        #if a_state.intelligence() >= 5:
        #    import src.items.item as item
        #    weapons = []
        #    for it in a_state.inventory().all_equipped_items():
        #        if item.ItemTags.WEAPON in it.get_tags():
        #            weapons.append(it)
        #    random.shuffle(weapons)

        #    attack_action_providers = []
        #    for wep in weapons:
        #        for action_prov in wep.all_actions():
        #            if action_prov.get_type() == ActionType.ATTACK:
        #                attack_action_providers.append(action_prov)

        #    for action_prov in attack_action_providers:
        #        for target in target_positions:
        #            act = action_prov.get_action(actor, position=target)
        #            if act.is_possible(world):
        #                return act

        # falling back to an unarmed attack
        for target in target_positions:
            if actor.get_actor_state().unarmed_is_projectile():
                res = ProjectileAttackAction(actor, None, target)
            else:
                res = MeleeAttackAction(actor, None, target)

            if res.is_possible(world):
                return res

    def _get_movement_action(self, actor, world):
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
                        print("WARN: world gave {} an impossible path? {}".format(actor, path))

        # if hidden, avoid stepping next to doors
        # (so that the player can't get instagibbed as they open a door)
        if world.get_hidden(*pos):
            neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
            random.shuffle(neighbors)

            from src.world.worldstate import World

            for n in neighbors:
                adjacent_to_door = False
                for n2 in Utils.neighbors(n[0], n[1]):
                    if n2 != pos and world.get_geo(n2[0], n2[1]) == World.DOOR:
                        adjacent_to_door = True
                        break
                if not adjacent_to_door:
                    res = MoveToAction(actor, n)
                    if res.is_possible(world):
                        return res

        # otherwise just fallback to dumb movement
        neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
        random.shuffle(neighbors)
        for n in neighbors:
            res = MoveToAction(actor, n)
            if res.is_possible(world):
                return res

    def _get_item_consume_action(self, actor, world):
        a_state = actor.get_actor_state()

        if a_state.stat_value(StatTypes.POTION_AFFINITY) >= 1 and a_state.hp() <= 2 * a_state.max_hp() // 3:
            for it in a_state.inventory().all_inv_items():
                consume_effect = it.get_consume_effect()
                if consume_effect is not None and consume_effect.stat_value(StatTypes.HP_REGEN) > 0:
                    consume_action = ConsumeItemAction(actor, it)

                    # should probably always be possible, but could depend on other things in the future
                    if consume_action.is_possible(world):
                        return consume_action
        return None

    def _get_item_throw_action(self, actor, world):
        a_state = actor.get_actor_state()

        all_throwables = []
        for it in a_state.inventory().all_inv_items():
            if it.can_throw():
                all_throwables.append(it)

        if len(all_throwables) == 0:
            return None

        # throw weapons at player
        if a_state.stat_value(StatTypes.THROW_AFFINITY) > 0:
            target_throw_positions = self._get_nearby_positions_with_actors(actor, world, same_alignment=False, min_dist=2)
            if len(target_throw_positions) > 0:

                for it in all_throwables:
                    if it.can_equip():
                        for pos in target_throw_positions:
                            throw_action = ThrowItemAction(actor, it, pos)
                            if throw_action.is_possible(world):
                                return throw_action

        # throw bad potions at player
        if a_state.stat_value(StatTypes.POTION_AFFINITY) >= 3:
            target_throw_positions = self._get_nearby_positions_with_actors(actor, world, same_alignment=False)
            if len(target_throw_positions) > 0:
                for it in all_throwables:
                    consume_effect = it.get_consume_effect()
                    if consume_effect is not None and consume_effect.is_debuff():
                        for pos in target_throw_positions:
                            throw_action = ThrowItemAction(actor, it, pos)
                            if throw_action.is_possible(world):
                                return throw_action

        # throw good potions at allies
        if a_state.stat_value(StatTypes.POTION_AFFINITY) >= 2:
            target_throw_positions = self._get_nearby_positions_with_actors(actor, world, same_alignment=True)
            if len(target_throw_positions) > 0:
                for it in all_throwables:
                    consume_effect = it.get_consume_effect()
                    if consume_effect is not None and not consume_effect.is_debuff():
                        for pos in target_throw_positions:

                            # don't heal allies with mostly full HP already.
                            if consume_effect.stat_value(StatTypes.HP_REGEN) > 0:
                                target_actor = world.get_actor_in_cell(*pos)
                                if target_actor is not None:
                                    pcnt_hp = target_actor.get_actor_state().hp() / target_actor.get_actor_state().max_hp()
                                    if pcnt_hp > 2 / 3:
                                        continue

                            throw_action = ThrowItemAction(actor, it, pos)
                            if throw_action.is_possible(world):
                                return throw_action

    def get_next_action(self, actor, world):
        is_hidden = world.get_hidden_at(*actor.center())

        # prevent bosses from blocking or insta-killing the player as they open the door
        if actor.is_boss() and is_hidden:
            pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
            return SkipTurnAction(actor, pos)

        is_visible = actor.is_visible_in_world(world)

        if is_visible:
            consume_action = self._get_item_consume_action(actor, world)
            if consume_action is not None and consume_action.is_possible(world):
                return consume_action

            throw_action = self._get_item_throw_action(actor, world)
            if throw_action is not None and throw_action.is_possible(world):
                return throw_action

        attack_action = self._get_attack_action(actor, world)
        if attack_action is not None and attack_action.is_possible(world):
            return attack_action

        movement_action = self._get_movement_action(actor, world)
        if movement_action is not None and movement_action.is_possible(world):
            return movement_action

        pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        return SkipTurnAction(actor, pos)


class ActionType:
    MOVE_TO = "MOVE_TO"
    SKIP_DIALOG = "SKIP_DIALOG"
    PICKUP_ITEM = "PICKUP_ITEM"
    DROP_ITEM = "DROP_ITEM"
    THROW_ITEM = "THROW_ITEM"
    GIVE_ITEM = "GIVE ITEM"
    ADD_ITEM_TO_GRID = "ADD_ITEM_TO_GRID"
    REMOVE_ITEM_FROM_GRID = "REMOVE_ITEM_FROM_GRID"
    CONSUME_ITEM = "CONSUME_ITEM"
    ATTACK = "ATTACK"
    INTERACT = "INTERACT"
    PLAYER_WAIT = "PLAYER_WAIT"  # special command used by player to indicate they're still deciding
    SKIP_TURN = "SKIP_TURN"
    SPAWN_ACTOR = "SPAWN_ACTOR"
    FROG_LEAP = "FROG_LEAP"


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

    def is_skip_turn_action(self):
        return self.get_type() == ActionType.SKIP_TURN

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
        evt = events.ActionStartedEvent(self)
        gs.get_instance().add_event(evt)

    def finalize(self, world):
        evt = events.ActionFinishedEvent(self)
        gs.get_instance().add_event(evt)

    def __str__(self):
        return "{}:[actor={}, item={}, position={}]".format(self.cmd_type, self.actor_entity, self.item, self.position)


class MoveToAction(Action):

    def __init__(self, actor, position, perturb_color=None):
        Action.__init__(self, ActionType.MOVE_TO, 22, actor, position=position)
        self.start_pos = None  # this is a pixel position, used for animating

        self._did_perturb_color = False
        self._perturb_color = perturb_color

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])

        if Utils.dist_manhattan(self.position, pos) != 1:
            return False
        elif world.is_solid(self.position[0], self.position[1], including_entities=True):
            return False

        return True

    def start(self, world):
        super().start(world)
        self.start_pos = self.actor_entity.center()

    def animate_in_world(self, progress, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))

        new_pos = Utils.linear_interp(self.start_pos, end_pos, progress)
        self.actor_entity.move_to(round(new_pos[0]), round(new_pos[1]))

        if not self._did_perturb_color and self._perturb_color is not None:
            self._did_perturb_color = True
            self.get_actor().perturb_color(self._perturb_color, 30)

    def finalize(self, world):
        super().finalize(world)
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
        it = self.get_item()
        if it is None or not it.can_consume():
            return False

        if not _find_accessible_item(it, self.get_actor(), world, and_remove_it=False):
            return False

        return True

    def start(self, world):
        super().start(world)
        removed = _find_accessible_item(self.get_item(), self.get_actor(), world, and_remove_it=True)
        if not removed:
            print("WARN: failed to remove consumable?: {}".format(self.item))

    def animate_in_world(self, progress, world):
        if progress >= 0.6 and not self._did_anim:
            self._did_anim = True
            consume_effect = self.item.get_consume_effect()
            if consume_effect is not None:
                self.actor_entity.perturb_color(consume_effect.get_color(), 30)
                self.actor_entity.set_visually_held_item_override(False)

                cx, cy = self.actor_entity.get_render_center(ignore_perturbs=True)
                world.show_effect_circle(cx, cy, consume_effect.get_effect_circle_art_type(),
                                         color=consume_effect.get_color(), duration=45)

            sound_effects.play_sound(soundref.potion_drink)

    def finalize(self, world):
        super().finalize(world)
        print("INFO: {} consumed item {}".format(self.actor_entity, self.item))
        consume_effect = self.item.get_consume_effect()
        if consume_effect is not None:
            self.actor_entity.get_actor_state().try_to_add_status_effect(consume_effect, self.item.get_consume_duration())
        self.actor_entity.set_visually_held_item_override(None)


class OpenDoorAction(MoveToAction):

    def __init__(self, actor, position, perturb_color=None):
        MoveToAction.__init__(self, actor, position, perturb_color=perturb_color)
        self.door_entity = None
        self._did_sound = False

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
        if not self._did_sound:
            sound_effects.play_sound(soundref.door_open)
            self._did_sound = True

    def finalize(self, world):
        super().finalize(world)
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))
        self.door_entity.remove_self_from_world(world)
        self.door_entity.do_special_open_hooks(world)
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


class HitResult:

    def __init__(self):
        self.missed = False
        self.should_swap = False


def apply_damage_and_hit_effects(damage, attacker, defender, world=None,
                                 attacker_entity=None, defender_entity=None, item_used=False,
                                 responsible_entity=None):
    """
    :param damage: Amount of damage to deal. If less than 1, the attack is a miss.
    :param attacker: The offensive stats_provider, which may contribute secondary offensive effects.
    :param defender: The defensive stats_provider, which may contribute secondary defensive effects.
    :param world: The world in which the attack is occurring.
    :param attacker_entity: The entity delivering the attack.
    :param defender_entity: The entity receiving the attack.
    :param item_used: The item used in the attack, which may contribute secondary offensive effects.
    :param responsible_entity: The entity that will be credited with the attack or kill.
    :returns: HitResult
    """
    res = HitResult()

    if damage <= 0:
        if defender_entity is not None and world is not None:
            world.show_floating_text("miss", colors.B_TEXT_COLOR, 1.5, defender_entity)
            sound_effects.play_sound(soundref.whiff_noise)
        res.missed = True
    else:
        was_alive = defender.is_alive()  # bleh
        defender.set_hp(defender.hp() - damage)

        res.missed = False

        # TODO consider making 'swap on hit' and 'swap when hit' cancel each other out, would be funny
        do_swap = attacker.stat_value_with_item(StatTypes.SWAP_ON_HIT, item_used) > 0
        do_swap = do_swap or defender.stat_value(StatTypes.SWAPS_WHEN_HIT) > 0

        if attacker.stat_value_with_item(StatTypes.UNSWAPPABLE, item_used) > 0:
            do_swap = False
        if defender.stat_value(StatTypes.UNSWAPPABLE) > 0:
            do_swap = False
        res.should_swap = do_swap

        if defender_entity is not None and world is not None:
            world.show_floating_text("-{}".format(damage), colors.R_TEXT_COLOR, 1.5, defender_entity)

            if defender.hp() > 0:
                defender_entity.animate_damage_taken(world)

        new_status_effects_for_attacker = []  # (StatusEffectType, duration)

        plus_def_duration = attacker.stat_value_with_item(StatTypes.PLUS_DEFENSE_ON_HIT, item_used)
        if plus_def_duration > 0:
            new_status_effects_for_attacker.append((statuseffects.StatusEffectTypes.PLUS_DEFENSES, plus_def_duration + 1))

        if was_alive and not defender.is_alive():

            if not defender_entity.is_enemy() or not defender_entity.is_inanimate():
                killer_uid = responsible_entity.get_uid() if responsible_entity is not None else None
                kill_event = events.ActorKilledEvent(defender_entity.get_uid(), killer_uid)
                gs.get_instance().add_event(kill_event)

            hp_on_kill = attacker.stat_value_with_item(StatTypes.HP_ON_KILL, item_used)
            if hp_on_kill > 0:
                new_status_effects_for_attacker.append((statuseffects.new_instant_heal_effect(hp_on_kill, name="HP on Kill"), 0))

        if attacker_entity is not None:
            for s in new_status_effects_for_attacker:
                effect, duration = s
                success = attacker_entity.get_actor_state().try_to_add_status_effect(effect, duration)

                if success:
                    if effect.get_color() is not None:
                        attacker_entity.perturb_color(effect.get_color(), 30)

                    # TODO - these all get drawn on top of each other...
                    if effect.get_effect_circle_art_type() is not None:
                        cx, cy = attacker_entity.get_render_center(ignore_perturbs=True)
                        world.show_effect_circle(cx, cy, effect.get_effect_circle_art_type(),
                                                 color=effect.get_color(), duration=45)

        new_status_effects_for_defender = []  # (StatusEffectType, duration)

        pois_duration = attacker.stat_value_with_item(StatTypes.POISON_ON_HIT, item_used)
        if pois_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.POISON, pois_duration))

        confuse_duration = attacker.stat_value_with_item(StatTypes.CONFUSION_ON_HIT, item_used)
        if confuse_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.CONFUSION, confuse_duration))

        blindness_duration = attacker.stat_value_with_item(StatTypes.BLINDNESS_ON_HIT, item_used)
        if blindness_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.BLINDNESS, blindness_duration))

        flinches = attacker.stat_value_with_item(StatTypes.FLINCH_ON_HIT, item_used) > 0
        if flinches:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.FLINCHED, 1))

        slow_duration = attacker.stat_value_with_item(StatTypes.SLOW_ON_HIT, item_used)
        if slow_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.SLOWNESS, slow_duration))

        chill_duration = attacker.stat_value_with_item(StatTypes.CHILL_ON_HIT, item_used)
        if chill_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.CHILLED, chill_duration))

        # TODO - the 'on melee hit' thing is not enforced right now
        grasped_duration = attacker.stat_value_with_item(StatTypes.GRASP_ON_MELEE_HIT, item_used)
        if grasped_duration > 0:
            new_status_effects_for_defender.append((statuseffects.StatusEffectTypes.GRASPED, grasped_duration))

        if defender_entity is not None:
            for s in new_status_effects_for_defender:
                effect, duration = s
                success = defender_entity.get_actor_state().try_to_add_status_effect(effect, duration)
                if success:
                    if effect.get_color() is not None:
                        defender_entity.perturb_color(effect.get_color(), 30)

                    if effect.get_effect_circle_art_type() is not None:
                        cx, cy = defender_entity.get_render_center(ignore_perturbs=True)
                        world.show_effect_circle(cx, cy, effect.get_effect_circle_art_type(),
                                                 color=effect.get_color(), duration=45)

    return res


class AttackAction(Action):

    def __init__(self, actor, item, position, duration):
        Action.__init__(self, ActionType.ATTACK, duration, actor, item=item, position=position)
        self._did_animations = False
        self._results = None  # (int: dmg, ActorEntity: target)
        self._hit_result = None

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
        if target is None or not target.get_actor_state().is_alive():
            return False

        if target.get_actor_state().alignment == actor.get_actor_state().alignment:
            return False

        return True

    def _apply_attack_and_add_animations_if_necessary(self, world):
        if not self._did_animations:
            self._did_animations = True
            damage = self._results[0]
            target = self._results[1]
            attacker = self.get_actor().get_actor_state()
            defender = target.get_actor_state()

            self._hit_result = apply_damage_and_hit_effects(damage, attacker, defender,
                                                            attacker_entity=self.get_actor(), defender_entity=target,
                                                            responsible_entity=self.get_actor(),
                                                            world=world, item_used=self.item)

    def start(self, world):
        super().start(world)
        target = world.get_actor_in_cell(self.position[0], self.position[1])
        t_state = target.get_actor_state()
        a_state = self.get_actor().get_actor_state()
        dmg_dealt = determine_damage_dealt(a_state, t_state, item_used=self.item, is_thrown=False)

        self._results = (dmg_dealt, target)

    def animate_in_world(self, progress, world):
        pass

    def swap_actor_with_target(self, world, show_effects=True):
        target = self._results[1]
        if target is not None:
            target_pos = world.to_grid_coords(*target.center())
            actor_pos = world.to_grid_coords(*self.actor_entity.center())

            # if somehow an actor is stuck in a wall, don't let it swap
            if world.is_solid(target_pos[0], target_pos[1], False):
                return False
            if world.is_solid(actor_pos[0], actor_pos[1], False):
                return False

            target_new_center = (int(world.cellsize() * (actor_pos[0] + 0.5)),
                                 int(world.cellsize() * (actor_pos[1] + 0.5)))
            target.set_center(*target_new_center)

            actor_new_center = (int(world.cellsize() * (target_pos[0] + 0.5)),
                                int(world.cellsize() * (target_pos[1] + 0.5)))
            self.actor_entity.set_center(*actor_new_center)

            if show_effects:
                if target.is_visible_in_world(world):
                    cx, cy = target.get_render_center(ignore_perturbs=True)
                    world.show_effect_circle(cx, cy, spriteref.EffectCircleTypes.STAR_5_ENCLOSED,
                                             color=colors.WHITE, duration=45, height=constants.CELLSIZE * 1.5)

                if self.actor_entity.is_visible_in_world(world):
                    cx, cy = self.actor_entity.get_render_center(ignore_perturbs=True)
                    world.show_effect_circle(cx, cy, spriteref.EffectCircleTypes.STAR_5_ENCLOSED,
                                             color=colors.WHITE, duration=45, height=constants.CELLSIZE * 1.5)

    def finalize(self, world):
        super().finalize(world)
        self._apply_attack_and_add_animations_if_necessary(world)
        self.actor_entity.set_draw_offset(0, 0)
        self.actor_entity.set_vel((0, 0))

        if self._hit_result.should_swap:
            self.swap_actor_with_target(world)

        attack_vec = Utils.sub(self._results[1].center(), self.actor_entity.center())

        if attack_vec[0] < -world.cellsize() // 2:
            self.actor_entity.set_facing_right(False)
            if self._results[0] > 0:
                self._results[1].set_facing_right(True)

        elif attack_vec[0] > world.cellsize() // 2:
            self.actor_entity.set_facing_right(True)
            if self._results[0] > 0:
                self._results[1].set_facing_right(False)


class ProjectileAttackAction(AttackAction):

    def __init__(self, actor, item, position):
        AttackAction.__init__(self, actor, item, position, 40)

        self._projectile_sprite = self._calc_projectile_sprite()
        self._projectile_animator = None

    def _calc_projectile_sprite(self):
        my_item = self.get_item()
        if my_item is not None:
            proj_sprite = my_item.get_projectile_sprite()
            if proj_sprite is not None:
                return proj_sprite

        return spriteref.Items.projectile_small

    def animate_in_world(self, progress, world):
        if self._projectile_animator is None:
            self._projectile_animator = _ThrownItemAnimator(self.get_actor(),
                                                            self.get_position(),
                                                            self._projectile_sprite,
                                                            colors.WHITE,  # TODO - better color choosing
                                                            hide_actor_held_item=False)
        self._projectile_animator.animate_in_world(progress, world)

    def finalize(self, world):
        super().finalize(world)
        if self._projectile_animator is not None:
            self._projectile_animator.finalize(world)


class MeleeAttackAction(AttackAction):

    def __init__(self, actor, item, position):
        AttackAction.__init__(self, actor, item, position, 24)
        self.start_pos = None
        self.end_pos = None

    def _get_end_pos(self, world):
        cur_pos = world.to_grid_coords(*self.get_actor().center())
        target_pos = self.get_position()

        if target_pos is None or Utils.dist_manhattan(cur_pos, target_pos) <= 1:
            return cur_pos

        closest_n = (target_pos[0] - 1, target_pos[1])
        for n in Utils.neighbors(target_pos[0], target_pos[1]):
            if Utils.dist(cur_pos, n) < Utils.dist(cur_pos, closest_n):
                closest_n = n

        return closest_n

    def is_possible(self, world):
        if not AttackAction.is_possible(self, world):
            return False

        cur_pos = world.to_grid_coords(*self.get_actor().center())
        end_pos = self._get_end_pos(world)
        if cur_pos != end_pos:
            if world.is_solid(end_pos[0], end_pos[1], including_entities=True):
                return False

        return True

    def start(self, world):
        super().start(world)
        self.start_pos = world.to_grid_coords(*self.get_actor().center())
        self.end_pos = self._get_end_pos(world)

    def finalize(self, world):
        end_center = (int(world.cellsize() * (self.end_pos[0] + 0.5)),
                      int(world.cellsize() * (self.end_pos[1] + 0.5)))
        self.actor_entity.set_center(*end_center)
        super().finalize(world)

    def animate_in_world(self, progress, world):
        run_at_pct = 0.3
        recover_pcnt = 1 - run_at_pct
        target_at = self._results[1].center()

        start_at = world.cell_center(*self.start_pos)
        stop_at = None  # actor's position at the moment of attack
        finish_at = world.cell_center(*self.end_pos)

        vec = Utils.sub(target_at, start_at)
        dist = Utils.mag(vec)
        if dist > world.cellsize() // 4:
            vec = Utils.set_length(vec, dist - world.cellsize() // 4)
            stop_at = Utils.add(start_at, vec)
        else:
            stop_at = target_at

        if progress <= run_at_pct:
            new_draw_pos = Utils.linear_interp(start_at, stop_at, progress / run_at_pct)
        else:
            self._apply_attack_and_add_animations_if_necessary(world)
            new_draw_pos = Utils.linear_interp(stop_at, finish_at, (progress - run_at_pct) / recover_pcnt)

        old_render_pos = self.actor_entity.get_render_center(ignore_perturbs=True)

        # during a lunge, the actor is actually moving while the attack animation is playing
        if start_at != finish_at:
            new_true_pos = Utils.linear_interp(start_at, finish_at, progress)
            self.actor_entity.set_center(*new_true_pos)

        new_move_offset = Utils.sub(new_draw_pos, self.actor_entity.center())
        self.actor_entity.set_draw_offset(*new_move_offset)

        new_render_pos = self.actor_entity.get_render_center(ignore_perturbs=True)
        vel = Utils.sub(new_render_pos, old_render_pos)
        self.actor_entity.set_vel(vel)


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
                self._actor.perturb_z(jump_height=constants.CELLSIZE // 3, jump_duration=15)

            start_pos = self._actor.center()
            end_pos = Utils.mult(Utils.add(self._position, (0.5, 0.5)), world.cellsize())

            if self._thrown_item_entity is None:
                from src.world.entities import AnimationEntity
                self._thrown_item_entity = AnimationEntity(start_pos[0], start_pos[1], [self._item_sprite], 1,
                                                           spriteref.ENTITY_LAYER, scale=1)
                self._thrown_item_entity.set_finish_behavior(AnimationEntity.FREEZE_ON_FINISH)
                self._thrown_item_entity.set_color(self._item_color)
                self._thrown_item_entity.set_shadow_sprite(spriteref.small_shadow)
                world.add(self._thrown_item_entity)

            airtime_prog = (progress - release_time) / (1 - release_time)

            pos = Utils.linear_interp(start_pos, end_pos, airtime_prog)
            self._thrown_item_entity.move_to(pos[0], pos[1])

            x = airtime_prog

            # heights at x = 0.0, 0.5, and 1.0 respectively
            y1 = (self._actor.get_sprite_height() * 2) // 3
            y2 = self._actor.get_sprite_height()
            y3 = world.cellsize() // 4

            # trust me on this
            a = 2 * y1 - 4 * y2 + 2 * y3
            b = -3 * y1 + 4 * y2 - y3
            c = y1

            h = a * x * x + b * x + c

            self._thrown_item_entity.set_sprite_offset((0, -h))  # XXX this method isn't meant for this

            # make it spin through the air
            rot = (self._item_start_rotation + int(airtime_prog * 6)) % 4
            self._thrown_item_entity.set_rotation(rot)

    def finalize(self, world):
        if self._thrown_item_entity is not None:
            pos = self._thrown_item_entity.center()
            world.show_explosion(pos[0], pos[1], 20, color=self._item_color, offs=(0, -constants.CELLSIZE // 4), scale=1)

            world.remove(self._thrown_item_entity)


class TradeItemAction(Action):

    def __init__(self, actor, item, position):
        Action.__init__(self, ActionType.GIVE_ITEM, 10, actor, item=item, position=position)
        self._recipient_npc = None
        self._received_items = None

    def get_targeting_color(self, for_mouse=False):
        return colors.PURPLE

    def get_recipient(self, world):
        pos = self.get_position()
        recipients = world.get_entities_in_cell(pos[0], pos[1], lambda e: e.can_trade())

        # if there's somehow more than one NPC at the position, just fail. that's a bad state
        if len(recipients) != 1:
            return None
        else:
            return recipients[0]

    def is_possible(self, world):
        if self.get_position() is None:
            return False

        actor = self.get_actor()
        actor_pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
        pos = self.get_position()
        if Utils.dist_manhattan(actor_pos, pos) > 1:
            return False

        if self.get_recipient(world) is None:
            return False

        if self.get_item() is None:
            return True  # this triggers the trade explanation dialog
        else:
            in_inv = self.item in actor.get_actor_state().inventory()
            on_cursor = actor.is_player() and gs.get_instance().held_item() == self.item
            if not (in_inv or on_cursor):
                return False

        return True

    def start(self, world):
        super().start(world)
        self._recipient_npc = self.get_recipient(world)

        item_to_trade = self.get_item()
        self._received_items = self._recipient_npc.try_to_do_trade(self.get_item(), self.get_actor(), world,
                                                                   and_drop_item=False)  # we drop in finalize

        if self._received_items is not None and item_to_trade is not None:

            # XXX the success dialog will freeze world updates, so it'll keep drawing the
            # held item even though it's been set to None...
            self.get_actor().set_visually_held_item_override(False)

            a_state = self.get_actor().get_actor_state()
            removed = a_state.inventory().remove(self.item)
            if not removed:
                if gs.get_instance().held_item() == self.item:
                    gs.get_instance().set_held_item(None)
                    removed = True

            if not removed:
                print("WARN: failed to remove traded item: {}".format(self.item))

    def finalize(self, world):
        super().finalize(world)
        self.get_actor().set_visually_held_item_override(None)

        if self._received_items is not None and len(self._received_items) > 0:
            actor_pos = self.get_actor().get_render_center()
            actor_pos = [actor_pos[0], actor_pos[1] + constants.CELLSIZE // 6]  # want it to land slightly in front of actor

            trader_pos = self._recipient_npc.get_render_center()
            trader_pos = [trader_pos[0], trader_pos[1] + constants.CELLSIZE // 6]

            actor_grid_pos = world.to_grid_coords(*self.get_actor().center())
            trader_grid_pos = world.to_grid_coords(*self._recipient_npc.center())
            if actor_grid_pos[0] == trader_grid_pos[0]:
                # offset the x pos during vertical trades, or else the character sprites will
                # block the item sprites.
                if random.random() < 0.5:
                    actor_pos[0] += int(constants.CELLSIZE * (0.25 + random.random() / 2))
                else:
                    actor_pos[0] -= int(constants.CELLSIZE * (0.25 + random.random() / 2))

            throw_dir = Utils.sub(actor_pos, trader_pos)
            throw_dir = Utils.set_length(throw_dir, 1.0)

            for it in self._received_items:
                world.add_item_as_entity(it, trader_pos, direction=throw_dir)


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
        if not (self.item in a_state.inventory() or gs.get_instance().held_item() == self.item):
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
        if target is None:
            return False

        return True

    def _apply_attack_and_add_animations_if_necessary(self, world):
        if not self._did_animations:
            self._did_animations = True
            damage = self._results[0]
            target = self._results[1]

            # we only want on-hit effects living on the thrown item to apply and
            # we don't want any on-hit effects to go back to the thrower (I think?)
            attacker = self.get_item()

            defender = target.get_actor_state()

            apply_damage_and_hit_effects(damage, attacker, defender,
                                         attacker_entity=None, defender_entity=target,
                                         responsible_entity=self.get_actor(),
                                         world=world, item_used=self.item)

            consume_effect = self.item.get_consume_effect()
            if damage >= 0 and consume_effect is not None:
                success = target.get_actor_state().try_to_add_status_effect(consume_effect, self.item.get_consume_duration())
                if success:
                    target.perturb_color(consume_effect.get_color(), 30)
                    cx, cy = target.get_render_center(ignore_perturbs=True)
                    world.show_effect_circle(cx, cy, consume_effect.get_effect_circle_art_type(),
                                             color=consume_effect.get_color(), duration=45)

    def start(self, world):
        super().start(world)
        a_state = self.actor_entity.get_actor_state()

        removed = a_state.inventory().remove(self.item)
        if not removed:
            if gs.get_instance().held_item() == self.item:
                gs.get_instance().set_held_item(None)
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
        super().finalize(world)
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

    def __init__(self, actor, position, perturb_color=None, intentional=True):
        Action.__init__(self, ActionType.SKIP_TURN, 25, actor, position=position)
        self._did_enemy_jump = False
        self._did_sound = False
        self._did_color_perturb = False

        self._intentional = intentional
        self._perturb_color = perturb_color

    def is_intentional(self):
        return self._intentional

    def animate_in_world(self, progress, world):
        actor = self.get_actor()

        if actor.is_player():
            jump_sprites = spriteref.player_attacks
            idx = int(Utils.bound(progress, 0.0, 0.99) * len(jump_sprites))
            actor.set_sprite_override(jump_sprites[idx])
            actor.set_visually_held_item_override(False)

        elif not self._did_enemy_jump:
            if not self._did_enemy_jump:
                self._did_enemy_jump = True
                actor.perturb_z(jump_height=constants.CELLSIZE // 4, jump_duration=10)

        if not self._did_color_perturb and self._perturb_color is not None:
            self._did_color_perturb = True
            actor.perturb_color(self._perturb_color, 25)

        if not self._did_sound:
            sound = soundref.player_skip_turn if actor.is_player() else soundref.enemy_skip_turn
            sound_effects.play_sound(sound)
            self._did_sound = True

    def is_possible(self, world):
        pix_pos = self.actor_entity.center()
        pos = world.to_grid_coords(pix_pos[0], pix_pos[1])
        return pos == self.position

    def finalize(self, world):
        super().finalize(world)

        if self.get_actor().is_player():
            self.get_actor().set_sprite_override(None)
            self.get_actor().set_visually_held_item_override(None)


class SilentSkipTurnAction(Action):

    def __init__(self, actor):
        Action.__init__(self, ActionType.SKIP_TURN, 0, actor)

    def is_intentional(self):
        return True

    def is_possible(self, world):
        return True


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

        interactable = world.get_interactable_in_cell(self.position[0], self.position[1])
        if interactable is None:
            return False

        if self.get_actor().is_player() and not interactable.is_visible_in_world(world):
            return False

        return True

    def start(self, world):
        super().start(world)
        self.target = world.get_interactable_in_cell(self.position[0], self.position[1])
        self.target.interact(world)

    def animate_in_world(self, world, progress):
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

    def start(self, world):
        # note that we're purposely *NOT* calling super's start
        # because we don't want to spam action_started events.
        pass

    def finalize(self, world):
        # note that we're purposely *NOT* calling super's finalize
        # because we don't want to spam action_finished events.
        pass


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

        if actor.is_player() and gs.get_instance().held_item() is not None:
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

    def start(self, world):
        super().start(world)

    def finalize(self, world):
        super().finalize(world)
        ent_to_pickup = self._get_entity_to_pickup(world)
        if ent_to_pickup is None:
            # this shouldn't be possible if is_possible, start, and finalize are called on the same frame,
            # but that may not always be the case i suppose
            print("ERROR: item we wanted to pick up isn't there anymore? {}".format(self.get_item()))
        else:
            gs.get_instance().set_held_item(ent_to_pickup.get_item())
            world.remove(ent_to_pickup)

            sound_effects.play_sound(soundref.item_pickup)


class DropItemAction(Action):

    def __init__(self, actor, item, drop_dir=None):
        Action.__init__(self, ActionType.DROP_ITEM, 1, actor, item=item)
        self._drop_dir = drop_dir

    def is_free(self):
        return True

    def is_possible(self, world):
        actor = self.get_actor()
        a_state = actor.get_actor_state()

        held_item = gs.get_instance().held_item() if actor.is_player() else None
        if held_item is None:
            if self.get_item() not in a_state.inventory():
                return False
        elif held_item != self.get_item():
            return False

        return True

    def start(self, world):
        super().start(world)
        if self._drop_dir is not None:
            if self._drop_dir[0] > 0.1:
                self.get_actor().set_facing_right(True)
            elif self._drop_dir[0] < -0.1:
                self.get_actor().set_facing_right(False)

    def finalize(self, world):
        super().finalize(world)
        actor = self.get_actor()

        if gs.get_instance().held_item() == self.get_item():
            gs.get_instance().set_held_item(None)
        else:
            a_state = actor.get_actor_state()
            a_state.inventory().remove(self.get_item())

        world.add_item_as_entity(self.get_item(), actor.center(), direction=self._drop_dir)
        sound_effects.play_sound(soundref.item_drop)


def _find_accessible_item(item, actor, world, and_remove_it=False):
    a_state = actor.get_actor_state()
    it = item
    held_item = gs.get_instance().held_item() if actor.is_player() else None
    if held_item is not None and held_item == it:
        if and_remove_it:
            gs.get_instance().set_held_item(None)
        return True

    inv_state = a_state.inventory()
    if inv_state.is_in_inventory(it):
        if and_remove_it:
            rm_result = inv_state.get_inv_grid().remove(it)
            if not rm_result:
                raise ValueError("failed to remove {} from inventory grid even though it's there...".format(it))
        return True

    if inv_state.is_equipped(it):
        if and_remove_it:
            rm_result = inv_state.get_equip_grid().remove(it)
            if not rm_result:
                raise ValueError("failed to remove {} from equipment grid even though it's equipped...".format(it))
        return True

    pos = actor.center()
    items_in_range = world.entities_in_circle(pos, world.cellsize() * 3, cond=lambda e: e.is_item())
    for item_ent in items_in_range:
        if item_ent.get_item() == it:
            actor_grid_pos = world.to_grid_coords(*actor.center())
            item_ent_grid_pos = world.to_grid_coords(*item_ent.center())
            sub = Utils.sub(actor_grid_pos, item_ent_grid_pos)
            if max(abs(sub[0]), abs(sub[1])) <= 1:
                if and_remove_it:
                    world.remove(item_ent)
                return True
    return False


class AddItemToGridAction(Action):

    def __init__(self, actor, item, grid, grid_position=None, position=None):
        Action.__init__(self, ActionType.ADD_ITEM_TO_GRID, 1, actor, item=item, position=position)
        self._grid = grid
        self._grid_position = grid_position

    def get_grid(self):
        return self._grid

    def get_grid_position(self):
        return self._grid_position

    def get_targeting_color(self, for_mouse=False):
        return (1, 1, 1)

    def is_free(self):
        return True

    def is_possible(self, world):
        if not self.get_actor().is_player():
            return False  # for now...

        grid = self.get_grid()
        if grid is None:
            return False

        # don't think you'd ever want to auto-place an item into the same grid
        if self.get_item() in grid:
            return False

        if self.get_position() is not None:
            actor_pos = world.to_grid_coords(*self.get_actor().center())
            if actor_pos != self.get_position():
                return False

        if self.get_grid_position() is not None:
            # direct positioning must be done via a held_item
            if gs.get_instance().held_item() != self.get_item():
                return False
            if not grid.can_place(self.get_item(), self.get_grid_position(), allow_replace=True):
                return False
        else:
            if grid.search_for_valid_position_to_place(self.get_item()) is None:
                return False
            if not _find_accessible_item(self.get_item(), self.get_actor(), world, and_remove_it=False):
                return False

        return True

    def start(self, world):
        super().start(world)
        grid = self.get_grid()
        it = self.get_item()

        pos = self.get_grid_position()
        res = False
        if pos is None:
            auto_pos = grid.search_for_valid_position_to_place(it)
            _find_accessible_item(it, self.get_actor(), world, and_remove_it=True)
            res = grid.place(it, auto_pos)
            sound_effects.play_sound(soundref.item_place)
        else:
            if grid.can_place(it, pos, allow_replace=False):
                gs.get_instance().set_held_item(None)
                res = grid.place(it, pos)
                sound_effects.play_sound(soundref.item_place)
            else:
                swapped_with = self.get_grid().try_to_replace(it, self.get_grid_position())
                if swapped_with is not None:
                    gs.get_instance().set_held_item(swapped_with)
                    sound_effects.play_sound(soundref.item_replace)
                    res = True

        if not res:
            raise ValueError("failed to place item {} in grid {}".format(it, grid))

    def finalize(self, world):
        super().finalize(world)
        self._handle_auto_activate(world)

    def _handle_auto_activate(self, world):
        if not self.get_actor().is_player():
            return

        # if you added the item to the equipment grid
        equip_grid = self.get_actor().get_actor_state().inventory().get_equip_grid()
        if equip_grid != self.get_grid():
            return

        # and the item has some mappable actions
        item_actions = [x for x in self.get_item().all_action_providers() if x.is_mappable()]
        if len(item_actions) == 0:
            return

        # and you don't already have an active action
        if gs.get_instance().get_targeting_action_provider() is None:
            gs.get_instance().set_targeting_action_provider(item_actions[0])  # then activate it


class RemoveItemFromGridAction(Action):

    def __init__(self, actor, item, grid):
        Action.__init__(self, ActionType.REMOVE_ITEM_FROM_GRID, 1, actor, item=item)
        self._grid = grid

    def is_free(self):
        return True

    def get_grid(self):
        return self._grid

    def is_possible(self, world):
        if not self.get_actor().is_player():
            return False  # for now...

        if gs.get_instance().held_item() is not None:
            # can't pick up an item while holding an item
            # (that's an AddItemToGridAction)
            return False

        grid = self.get_grid()
        if grid is None:
            return False

        if self.get_item() is None:
            return False

        if self.get_item() not in self.get_grid():
            return False

        return True

    def start(self, world):
        super().start(world)
        grid = self.get_grid()
        my_item = self.get_item()

        # should always succeed but just in case...
        rem_success = grid.remove(my_item)
        if rem_success:
            sound_effects.play_sound(soundref.item_pickup)
            gs.get_instance().set_held_item(my_item)
        else:
            print("ERROR: failed to remove item from grid: {}".format(my_item))


class FrogLeapAction(MoveToAction):

    def __init__(self, actor, position):
        Action.__init__(self, ActionType.FROG_LEAP, 60, actor, position=position)
        self._pre_jump_pcnt = 0.15
        self._post_jump_pcnt = 0.25
        self._jump_height = constants.CELLSIZE * 1.5
        self._orig_shadow = actor.get_shadow_sprite()

        self._did_screen_shake = False

    def is_possible(self, world):
        pos = self.get_position()
        if pos is None:
            return False

        if world.is_solid(pos[0], pos[1], including_entities=True):
            return False

        # letting the frog jump into dark positions makes it too easy to skip the fight
        if world.get_lighting(pos[0], pos[1]) <= 0:
            return False

        return True

    def _get_z_height(self, jump_pct):
        x = jump_pct
        h = self._jump_height
        res = -4 * h * x * x + 4 * h * x
        return Utils.bound(res, 0, h)

    def animate_in_world(self, progress, world):
        end_pos = (int(world.cellsize() * (self.position[0] + 0.5)),
                   int(world.cellsize() * (self.position[1] + 0.5)))

        z_offs = 0
        new_shadow = None

        if progress < self._pre_jump_pcnt:
            self.actor_entity.set_sprite_override(spriteref.Bosses.frog_idle_down)
            new_pos = self.start_pos
        elif progress >= 1 - self._post_jump_pcnt:
            self.actor_entity.set_sprite_override(spriteref.Bosses.frog_idle_down)
            new_pos = end_pos

            if not self._did_screen_shake:
                self._did_screen_shake = True
                gs.get_instance().add_screenshake(constants.CELLSIZE * 0.375, 18, falloff=3, freq=3)
        else:
            jump_prog = (progress - self._pre_jump_pcnt) / (1 - self._post_jump_pcnt - self._pre_jump_pcnt)
            jump_prog = Utils.bound(jump_prog, 0.0, 1.0)
            if jump_prog < 0.5:
                self.actor_entity.set_sprite_override(spriteref.Bosses.frog_airborn_rising)
            else:
                self.actor_entity.set_sprite_override(spriteref.Bosses.frog_airborn_falling)
            new_pos = Utils.linear_interp(self.start_pos, end_pos, jump_prog)
            z_offs = self._get_z_height(jump_prog)

            if self._orig_shadow is not None and 0.1 <= jump_prog <= 0.9:
                # we know it's a large shadow because this action is only used by the frog boss
                new_shadow = spriteref.large_shadow

        self.actor_entity.set_z_draw_offset(-z_offs)
        self.actor_entity.set_shadow_sprite_override(new_shadow)
        self.actor_entity.move_to(round(new_pos[0]), round(new_pos[1]))

    def finalize(self, world):
        super().finalize(world)
        self.actor_entity.set_z_draw_offset(0)
        self.actor_entity.set_shadow_sprite_override(None)
        self.actor_entity.set_sprite_override(None)


class SpawnActorAction(Action):

    def __init__(self, actor, position, new_actor, art_color=colors.RED, apply_sickness=True):
        Action.__init__(self, ActionType.SPAWN_ACTOR, 40, actor, position=position)
        self.new_actor = new_actor
        self.art_color = art_color

        self._did_animation_1 = False
        self._did_animation_2 = False
        self._did_add = False

        self._apply_summoning_sickness = apply_sickness

    def is_possible(self, world):
        pos = self.get_position()
        if pos is None:
            return False

        if world.is_solid(pos[0], pos[1], including_entities=True):
            return False

        if not self.new_actor.get_actor_state().is_alive():
            print("WARN: trying to spawn a dead actor? {}".format(self.new_actor))
            return False

        if world.get_entity(self.new_actor.get_uid(), onscreen=False) is not None:
            print("WARN: actor is already in world: {}".format(self.new_actor))
            return False

        if self.get_actor().get_actor_state().stat_value(StatTypes.SUMMONING_SICKNESS) > 0:
            return False

        return True

    def start(self, world):
        super().start(world)
        pass

    def animate_in_world(self, progress, world):
        if not self._did_animation_1:
            self._did_animation_1 = True

            if self.art_color is not None:
                cx = (self.get_position()[0] + 0.5) * world.cellsize()
                cy = (self.get_position()[1] + 0.5) * world.cellsize()

                from src.world.entities import EffectCircleArt
                circle_anim = EffectCircleArt(cx, cy, 96, 60, art_type=spriteref.EffectCircleTypes.STAR_5_ENCLOSED,
                                              color=colors.WHITE, color_end=self.art_color)
                world.add(circle_anim)

        if not self._did_animation_2 and progress > 0.5:
            self._did_animation_2 = True

            if self.art_color is not None:
                cx = (self.get_position()[0] + 0.5) * world.cellsize()
                cy = (self.get_position()[1] + 0.75) * world.cellsize()
                world.show_explosion(cx, cy, 30, color=self.art_color, offs=(0, 0), scale=2)

            sound_effects.play_sound(soundref.summon_enemy)

            if self.art_color is not None:
                self.new_actor.perturb_color(self.art_color, 20)

            world.add(self.new_actor, self.get_position())
            self._did_add = True

    def finalize(self, world):
        super().finalize(world)
        if not self._did_add:
            world.add(self.new_actor, self.get_position())
            self._did_add = True

        if self._apply_summoning_sickness:
            duration = self.get_actor().get_actor_state().stat_value(StatTypes.SUMMONING_SICKNESS_ON_SUMMON)
            if duration > 0:
                self.get_actor().get_actor_state().try_to_add_status_effect(statuseffects.StatusEffectTypes.SUMMON_SICKNESS, duration)


class ActionProvider:

    def __init__(self, name, action_type, target_dists=(0,), icon_sprite=None, color=(1, 1, 1),
                 hotbar_color=None, needs_to_be_equipped=False):
        self.name = name
        self.color = color
        self.hotbar_color = hotbar_color
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

    def get_item_uid(self):
        return None

    def get_type(self):
        return self.action_type

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_hotbar_color(self):
        return self.hotbar_color if self.hotbar_color is not None else self.get_color()

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
        return SkipTurnAction(actor, position)


class ItemActionProvider(ActionProvider):

    def __init__(self, item, action_provider):
        ActionProvider.__init__(self, None, None)
        self.item_uid = None if item is None else item.get_uid()
        self.action_provider = action_provider

    def __eq__(self, other):
        if isinstance(other, ItemActionProvider):
            return self.item_uid == other.item_uid and self.action_provider == other.action_provider
        else:
            return False

    def is_mappable(self):
        """Whether the action can be mapped to the action hotbar."""
        return self.action_provider.is_mappable()

    def get_type(self):
        return self.action_provider.get_type()

    def get_item_uid(self):
        return self.item_uid

    def needs_equipped(self):
        return self.action_provider.needs_equipped()

    def get_icon(self):
        return self.action_provider.get_icon()

    def get_name(self):
        return self.action_provider.get_name()

    def get_color(self):
        return self.action_provider.get_color()

    def get_hotbar_color(self):
        return self.action_provider.get_hotbar_color()

    def get_target_dists(self):
        return self.action_provider.get_target_dists()

    def get_targets(self, pos=(0, 0)):
        return self.action_provider.get_targets(pos=pos)

    def get_action(self, actor, position=None, item=None):
        if item is not None:
            raise ValueError("Cannot pass an item to an ItemActionProvider: {}".format(item))

        if self.item_uid is not None:
            item = actor.get_actor_state().get_item_in_possession_with_uid(self.item_uid)
            if item is None:
                print("WARN: Could not find an item with uid={} in actor's possession: {}".format(self.item_uid, actor))

        return self.action_provider.get_action(actor, position=position, item=item)


class ConsumeItemActionProvider(ActionProvider):

    def __init__(self):
        ActionProvider.__init__(self, "Drink", ActionType.CONSUME_ITEM, color=(0.5, 1, 0.5))

    def get_action(self, actor, position=None, item=None):
        return ConsumeItemAction(actor, item)


class AttackItemActionProvider(ActionProvider):

    def __init__(self, name, icon, target_dists, color=colors.RED, hotbar_color=colors.DARKER_RED, projectile=False):
        # i don't trust myself to not typo this
        if not isinstance(target_dists, tuple):
            raise ValueError("target_dists needs to be a tuple. instead got {}".format(target_dists))

        self.projectile = projectile

        ActionProvider.__init__(self, name, ActionType.ATTACK, icon_sprite=icon,
                                target_dists=target_dists, color=color, hotbar_color=hotbar_color,
                                needs_to_be_equipped=True)

    def is_mappable(self):
        return True

    def needs_equipped(self):
        return True

    def get_action(self, actor, position=None, item=None):
        if self.projectile:
            return ProjectileAttackAction(actor, item, position)
        else:
            return MeleeAttackAction(actor, item, position)


class ItemActions:
    CONSUME_ITEM = ConsumeItemActionProvider()
    SWORD_ATTACK = AttackItemActionProvider("Sword Attack", spriteref.Items.sword_icon, (1,))
    SPEAR_ATTACK = AttackItemActionProvider("Spear Attack", spriteref.Items.spear_icon, (1, 2))
    WHIP_ATTACK = AttackItemActionProvider("Whip Attack", spriteref.Items.whip_icon, (1,))
    WAND_ATTACK = AttackItemActionProvider("Wand Attack", spriteref.Items.magic_icon, (1, 2), projectile=True)
    SHIELD_ATTACK = AttackItemActionProvider("Shield Bash", spriteref.Items.shield_icon, (1,))
    DAGGER_ATTACK = AttackItemActionProvider("Dagger Attack", spriteref.Items.dagger_icon, (1,))
    BOW_ATTACK = AttackItemActionProvider("Bow Shot", spriteref.Items.bow_icon, (2, 3), projectile=True)
    AXE_ATTACK = AttackItemActionProvider("Axe Attack", spriteref.Items.axe_icon, (1,))
    UNARMED_ATTACK = AttackItemActionProvider("Slap", spriteref.Items.unarmed_icon, (1,))
    FISHING_ROD_ATTACK = AttackItemActionProvider("Hook n' Reel", spriteref.Items.fishing_rod_icon, (1,))
    SLINGSHOT_ATTACK = AttackItemActionProvider("Sling Shot", spriteref.Items.slingshot_icon, (2,), projectile=True)


def get_basic_movement_actions(player, current_pos, move_pos, for_click=False):
    res = []

    res.append(InteractAction(player, move_pos))
    res.append(TradeItemAction(player, gs.get_instance().held_item(), move_pos))

    if not for_click:
        res.append(OpenDoorAction(player, move_pos))
        res.append(MoveToAction(player, move_pos))

    return res


def get_confusion_move_actions(player, pos, target_pos):
    neighbors = [n for n in Utils.neighbors(pos[0], pos[1])]
    random.shuffle(neighbors)

    res = []

    color = statuseffects.StatTypes.CONFUSION.get_color()

    for n in neighbors:
        if n != target_pos:
            res.append(OpenDoorAction(player, n, perturb_color=color))
            res.append(MoveToAction(player, n, perturb_color=color))

    return res


def get_keyboard_action_requests(world, player, target_pos):
    pos = world.to_grid_coords(*player.center())
    res = []

    if gs.get_instance().held_item() is None:
        action_prov = gs.get_instance().get_targeting_action_provider()
        if action_prov is not None:
            for i in range(1, 5):
                dx = target_pos[0] - pos[0]
                dy = target_pos[1] - pos[1]
                extended_target_pos = (pos[0] + dx * i, pos[1] + dy * i)
                res.append(action_prov.get_action(player, position=extended_target_pos))
        else:
            if player.get_actor_state().unarmed_is_projectile():
                res.append(ProjectileAttackAction(player, None, target_pos))
            else:
                res.append(MeleeAttackAction(player, None, target_pos))

    for basic_action in get_basic_movement_actions(player, pos, target_pos, for_click=False):
        res.append(basic_action)

    return res


def get_right_click_action_for_item(clicked_item):
    w, p = gs.get_instance().get_world_and_player()
    if w is None or p is None:
        return None

    from src.items.item import ItemTags

    inv_state = p.get_actor_state().inventory()

    if inv_state.is_in_inventory(clicked_item) and clicked_item.can_consume():
        consume_action = ConsumeItemAction(p, clicked_item)
        if consume_action.is_possible(w):
            return consume_action

    # right clicking an equippable item will move it between equipment grid and inventory grid
    if clicked_item.get_type().has_tag(ItemTags.EQUIPMENT):
        if inv_state.is_equipped(clicked_item):
            return AddItemToGridAction(p, clicked_item, inv_state.inv_grid, grid_position=None)
        elif inv_state.is_in_inventory(clicked_item):
            return AddItemToGridAction(p, clicked_item, inv_state.equip_grid, grid_position=None)
        else:

            # if it's a weapon with a type we already have equipped, add it to inventory
            if clicked_item.get_type().has_tag(ItemTags.WEAPON):
                already_equipped_same_type = False
                for eq_item in inv_state.equip_grid.all_items():
                    if eq_item.get_type() == clicked_item.get_type():
                        already_equipped_same_type = True
                        break
                if already_equipped_same_type:
                    add_to_inv = AddItemToGridAction(p, clicked_item, inv_state.inv_grid, grid_position=None)
                    if add_to_inv.is_possible(w):
                        return add_to_inv

            # otherwise try to equip it, then try to inventory it
            to_equip_action = AddItemToGridAction(p, clicked_item, inv_state.equip_grid, grid_position=None)
            if to_equip_action.is_possible(w):
                return to_equip_action
            else:
                return AddItemToGridAction(p, clicked_item, inv_state.inv_grid, grid_position=None)

    # just add anything else to the inventory
    elif not inv_state.is_in_inventory(clicked_item):
        return AddItemToGridAction(p, clicked_item, inv_state.inv_grid, grid_position=None)

    return None


def get_actions_from_click(world, world_pos, button=1):
    world_grid_pos = world.to_grid_coords(*world_pos)

    player = world.get_player()
    ps = gs.get_instance().player_state()

    if gs.get_instance().world_updates_paused():
        return []

    res = []

    if player is not None:
        if button == 1:
            held_item = gs.get_instance().held_item()
            if held_item is not None:
                throw_action = ThrowItemAction(player, held_item, world_grid_pos)
                res.append(throw_action)

                trade_action = TradeItemAction(player, held_item, world_grid_pos)
                res.append(trade_action)

                # clicking the player either consumes the item or places it into the inventory
                if world_grid_pos == world.to_grid_coords(*player.center()):
                    if held_item.can_consume():
                        consume_action = ConsumeItemAction(player, held_item)
                        res.append(consume_action)

                    right_click_action = get_right_click_action_for_item(held_item)
                    if right_click_action is not None:
                        res.append(right_click_action)

                drop_dir = Utils.sub(world_pos, player.center())
                drop_action = DropItemAction(player, held_item, drop_dir=drop_dir)
                res.append(drop_action)
            else:
                # picking up items
                clicked_item = world.get_entity_for_mouseover(world_pos, cond=lambda i: i.is_item())
                if clicked_item is not None:
                    item_pos = world.to_grid_coords(*clicked_item.center())
                    pickup_request = PickUpItemAction(player, clicked_item.get_item(), item_pos)
                    res.append(pickup_request)

                # now do attacking and interacting stuff
                action_prov = gs.get_instance().get_targeting_action_provider()
                if action_prov is not None:
                    res.append(action_prov.get_action(player, world_grid_pos))
                else:
                    res.append(MeleeAttackAction(player, None, world_grid_pos))

                pos = world.to_grid_coords(*player.center())
                for action in get_basic_movement_actions(player, pos, world_grid_pos, for_click=True):
                    res.append(action)

        elif button == 3:
            item_to_apply = gs.get_instance().held_item()
            if item_to_apply is None:
                clicked_item_entity = world.get_entity_for_mouseover(world_pos, cond=lambda i: i.is_item())
                if clicked_item_entity is not None:
                    item_to_apply = clicked_item_entity.get_item()

            if item_to_apply is not None:
                right_click_action = get_right_click_action_for_item(item_to_apply)
                if right_click_action is not None and right_click_action.is_possible(world):
                    res.append(right_click_action)
                else:
                    sound_effects.play_sound(soundref.item_cant_place)

    return res

