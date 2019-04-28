import random

from enum import Enum

from src.attacks import attacks as attacks
from src.game import spriteref as spriteref
from src.game.stats import ActorStatType, StatType
from src.utils.util import Utils
from src.world.entities import AnimationEntity, Player, ReturnExitEntity, FloatingTextEntity, ItemEntity, ExitEntity, PickupEntity, HoverTextEntity, PotionEntity, Pushable
import src.game.events as events
from src.game.loot import LootFactory
from src.world.entities import AttackCircleArt
import src.game.debug as debug
import src.game.globalstate as gs
import src.game.sound_effects as sound_effects


class ActorState(Pushable):

    R_TEXT_COLOR = (0.75, 0.0, 0.0)
    G_TEXT_COLOR = (0.2, 0.85, 0.2)
    B_TEXT_COLOR = (0.2, 0.2, 0.85)

    def __init__(self, name, level, base_values):
        Pushable.__init__(self)

        self._name = name
        self._level = level
        self._base_values = base_values
        self.current_hp = self.stat_value(ActorStatType.HP)

        self.attack_state = attacks.AttackState()

        self.damage_recoil = 15
        self.took_damage_x_ticks_ago = self.damage_recoil
        self.set_color_x_ticks_ago = self.damage_recoil
        self.dmg_color = (1, 0, 0)

        self.damage_amounts = []
        self.heal_amounts = []
        self.avoided_attack = False

        self._status_effects = []
        self._statuses_to_add = []
        self._statuses_to_remove = set()

    def update(self, entity, world, input_state):
        pass

    def name(self):
        return self._name

    def level(self):
        return self._level

    def get_base_stats(self):
        return dict(self._base_values)

    def get_attack_state(self):
        return self.attack_state

    def add_status(self, status):
        self._statuses_to_add.append(status)

    def remove_status(self, status):
        self._statuses_to_remove.add(status)

    def has_status(self, status_type):
        for s in self._status_effects:
            if s.get_type() == status_type:
                return True
        return False

    def remove_all_statuses(self):
        for s in self._status_effects:
            self.remove_status(s)

    def max_hp(self):
        return self.stat_value(ActorStatType.HP)

    def hp(self):
        return Utils.bound(self.current_hp, 0, self.max_hp())

    def set_hp(self, value):
        self.current_hp = Utils.bound(value, 0, self.max_hp())

    def get_hp_color(self):
        return (1, 0, 0) if not self.has_status(attacks.StatusEffect.POISON) else (0.2, 0.7, 0.2)

    def move_speed(self):
        return self.stat_value(ActorStatType.MOVESPEED)

    def recoil_progress(self):
        return Utils.bound(self.took_damage_x_ticks_ago / self.damage_recoil, 0.0, 1.0)

    def color_fade_progress(self):
        return Utils.bound(self.set_color_x_ticks_ago / self.damage_recoil, 0.0, 1.0)

    def recoil_color(self):
        return Utils.linear_interp(self.dmg_color, self.base_color(), self.color_fade_progress())

    def is_invuln(self):
        return False

    def base_color(self):
        return (1, 1, 1)

    def get_dodge_text_info(self):
        return ("miss", 2, ActorState.B_TEXT_COLOR)

    def get_dmg_text_info(self):
        return ("-{}", 2, ActorState.R_TEXT_COLOR)

    def get_heal_text_info(self):
        return ("+{}", 2, ActorState.G_TEXT_COLOR)

    def handle_floating_text(self, entity, world):
        dmg_info = self.get_dmg_text_info()
        if dmg_info is not None:
            total_dmg = sum(self.damage_amounts)
            if total_dmg > 0:
                show_floating_text(dmg_info[0].format(round(total_dmg)), dmg_info[2], dmg_info[1], entity, world)
        self.damage_amounts.clear()

        heal_info = self.get_heal_text_info()
        if heal_info is not None:
            total_heal = sum(self.heal_amounts)
            if total_heal >= 0.05:
                heal_amt = round(total_heal) if total_heal >= 1 else round(total_heal*10)/10
                show_floating_text(heal_info[0].format(heal_amt), heal_info[2], heal_info[1], entity, world)
        self.heal_amounts.clear()

        avoid_info = self.get_dodge_text_info()
        if avoid_info is not None:
            if self.avoided_attack:
                show_floating_text(avoid_info[0], avoid_info[2], avoid_info[1], entity, world)
        self.avoided_attack = False

    def deal_damage(self, damage, ignore_invuln=False, knockback=(0, 0), color=(1, 0, 0)):
        if damage > 0 and (ignore_invuln or not self.is_invuln()):
            self.set_hp(self.hp() - damage)
            self.took_damage_x_ticks_ago = 0
            self.set_color_x_ticks_ago = 0
            self.dmg_color = color
            self.damage_amounts.append(damage)

            if knockback != (0, 0):
                # faster implies lighter, implies easier to knock back, lol
                knockback = Utils.mult(knockback, 1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100)
                self.push(knockback, self.damage_recoil)

    def do_full_heal(self):
        heal_val = self.max_hp() - self.hp()
        if heal_val > 0:
            self.do_heal(heal_val)

    def do_heal(self, amount):
        if amount > 0:
            prev_hp = self.hp()
            self.set_hp(prev_hp + amount)
            diff = self.hp() - prev_hp
            self.heal_amounts.append(diff)

    def update_status_effects(self, entity, world):
        for status in self._statuses_to_add:
            self._status_effects.append(status)
        self._status_effects = [x for x in self._status_effects if x not in self._statuses_to_remove]
        self._statuses_to_add.clear()
        self._statuses_to_remove.clear()

        for status in self._status_effects:
            status.update(entity, world)

    def was_missed(self):
        self.avoided_attack = True

    def _compute_derived_stat(self, stat_type):
        """
            returns: None if stat is not derived, else stat value
        """
        if stat_type is ActorStatType.HP:
            vit = self.stat_value(StatType.VIT)
            plus_hp = self.stat_value(StatType.MAX_HEALTH)
            return round(vit * 4 * (1 + plus_hp / 100))

        elif stat_type is ActorStatType.MOVESPEED:
            base = self._base_values[stat_type]
            return base * (1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100)

    def stat_value(self, stat_type):
        return 0


class PlayerState(ActorState):
    def __init__(self, name, inventory):
        self._inventory = inventory
        self.kill_count = 0
        self.num_potions = 5

        ActorState.__init__(self, name, 0, {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10,
            ActorStatType.MOVESPEED: 2.5,
        })

        self.current_sprite = spriteref.player_idle_0

        self._default_attack = attacks.GROUND_POUND
        self.attack_state.set_attack(self._default_attack)

        self._potion_cooldown = 1  # set whenever a potion is activated
        self._potion_tick_count = self._potion_cooldown

        self._damage_last_tick = 0
        self._healing_last_tick = 0

        self.is_moving = False
        self.facing_right = True

        self._is_dead = False
        self.death_seq_duration = 120
        self.death_seq_tick = 0

        self._is_actionable = True
        self._is_visible = True

        self.held_item = None
        self._held_item_image_entity_uid = None

        self.current_hover_text = None
        self.current_hover_text_entity_uid = None

    def hp(self):
        if debug.DEBUG:
            # no dying in debug mode
            return max(1, ActorState.hp(self))
        else:
            return ActorState.hp(self)

    def get_cooldown_progress(self, slot_num):
        if slot_num == 0:
            if self.attack_state.is_active():
                return self.attack_state.total_progress()
            else:
                return 1.0
        elif slot_num == 1:
            return Utils.bound(self._potion_tick_count / self._potion_cooldown, 0, 1)
        else:
            return 1.0

    def inventory(self):
        return self._inventory

    def get_hp_color(self):
        if self.has_status(attacks.StatusEffect.POISON):
            return (0.5, 1.0, 0.5)
        else:
            return (1.0, 0.5, 0.5)

    def picked_up(self, pickup_entity, world):
        print("INFO: picked up {}".format(pickup_entity))

        if pickup_entity.is_potion():
            self.num_potions += 1

    def damage_and_healing_last_tick(self):
        return self._damage_last_tick, self._healing_last_tick

    def is_invuln(self):
        # can't be hit while attacking
        return self.attack_state.is_attacking()

    def is_dead(self):
        return self._is_dead

    def _handle_death(self, player_entity, world):
        world.remove(player_entity)
        death_anim = AnimationEntity(player_entity.x(), player_entity.y(),
                                     spriteref.player_death_seq, 20, spriteref.ENTITY_LAYER,
                                     scale=2, w=player_entity.w(), h=player_entity.h())

        death_anim.set_sprite_offset((0, -24))
        death_anim.set_finish_behavior(AnimationEntity.FREEZE_ON_FINISH)
        death_anim.set_xflipped(not self.facing_right)
        death_anim.set_vel(Utils.mult(self.get_total_push(), 2), fric=0.90, collides=True)

        world.add(death_anim)

    def _can_use_potion(self):
        return self._potion_tick_count >= self._potion_cooldown and self.hp() < self.max_hp()

    def _can_interact(self):
        return self._is_actionable and not self.attack_state.is_active()

    def _handle_potions(self, try_to_use):
        if self._potion_tick_count < self._potion_cooldown:
            self._potion_tick_count += 1

        if try_to_use and self.num_potions > 0 and self._can_use_potion():
            pot_heal = 10 + self.stat_value(StatType.POTION_HEALING)
            self.do_heal(pot_heal)
            self.num_potions -= 1

            pot_cd = round(max(1, 180 * (1 - 0.01 * self.stat_value(StatType.POTION_COOLDOWN))))
            self._potion_cooldown = pot_cd
            self._potion_tick_count = 0

    def stat_value(self, stat_type):
        """
            stat_type: StatType or PlayerStatType
        """
        derived = self._compute_derived_stat(stat_type)
        if derived is not None:
            return derived
        else:
            value = 0
            if stat_type in self._base_values:
                value = self._base_values[stat_type]

            for item in self.inventory().all_equipped_items():
                for stat in item.all_stats():
                    if stat.stat_type is stat_type:
                        value += stat.value

        return value

    def get_dodge_text_info(self):
        return ("dodge", 3, ActorState.B_TEXT_COLOR)

    def get_dmg_text_info(self):
        return ("-{}", 5, ActorState.R_TEXT_COLOR)

    def get_heal_text_info(self):
        return ("+{}", 3, ActorState.G_TEXT_COLOR)

    def drop_held_item(self, player_entity, world, direction=None):
        if self.held_item is None:
            return
        else:
            if direction is not None:
                vel = PickupEntity.rand_vel(speed=None, direction=direction)
            else:
                vel = (0, 1)

            pos = player_entity.center()
            world.add(ItemEntity(self.held_item, pos[0], pos[1], vel=vel))
            print("INFO: dropped item " + str(self.held_item))
            self.held_item = None

    def _update_hover_text(self, target_entity, text, world):
        if self.current_hover_text_entity_uid is not None:
            hover_entity = world.get_entity(self.current_hover_text_entity_uid, onscreen=True)
            if hover_entity is None:
                hover_entity = world.get_entity(self.current_hover_text_entity_uid, onscreen=False)
                if hover_entity is None:
                    self.current_hover_text_entity_uid = None
        else:
            hover_entity = None

        if text is None and hover_entity is not None:
            world.remove(hover_entity)
            self.current_hover_text_entity_uid = None

        elif text is not None:
            offs = (0, -64)

            # TODO - holy special case batman
            if isinstance(target_entity, Player):
                offs = (0, -96)
            elif isinstance(target_entity, ExitEntity):
                offs = (0, -150)

            if hover_entity is None:
                hover_entity = HoverTextEntity(text, target_entity, offset=offs)
                self.current_hover_text_entity_uid = hover_entity.get_uid()
                world.add(hover_entity)
            else:
                # TODO - if this thing is offscreen, it won't update properly
                hover_entity.set_text(text)
                hover_entity.set_target_entity(target_entity, offset=offs)

    def set_actionable(self, val):
        self._is_actionable = val

    def set_visible(self, val):
        self._is_visible = val

    def update(self, player_entity, world, input_state):
        if not gs.get_instance().world_updates_paused():

            if self._is_dead:
                if self.death_seq_tick >= self.death_seq_duration:
                    gs.get_instance().event_queue().add(events.PlayerDiedEvent())
                else:
                    self.death_seq_tick += 1

            if player_entity is None:
                return

            self._damage_last_tick = sum(self.damage_amounts)
            self._healing_last_tick = sum(self.damage_amounts)
            self.handle_floating_text(player_entity, world)

            if self._damage_last_tick / self.max_hp() > 0.15:
                shake_strength = 45 * self._damage_last_tick / self.max_hp()
                duration = 25
                gs.get_instance().add_screenshake(shake_strength, duration, freq=3)

            if self.hp() <= 0:
                self._is_dead = True
                self._handle_death(player_entity, world)
                self._damage_last_tick = 0
                return

            if self._is_actionable:
                self._handle_potions(input_state.was_pressed(gs.get_instance().settings().potion_key()))

            if gs.get_instance().tick_counter % 60 == 0:
                regen = self.stat_value(StatType.LIFE_REGEN)
                self.do_heal(regen)

            self.update_status_effects(player_entity, world)

            if self.took_damage_x_ticks_ago < self.damage_recoil:
                self.took_damage_x_ticks_ago += 1

            if self.set_color_x_ticks_ago < self.damage_recoil:
                self.set_color_x_ticks_ago += 1

            if self._is_actionable:
                if input_state.is_held(gs.get_instance().settings().attack_key()) and self.attack_state.can_attack():
                    self.drop_held_item(player_entity, world)
                    self.attack_state.start_attack(self)

            self.attack_state.update(player_entity, world)

            closest_interactable = None
            p_center = player_entity.center()
            inter = [x for x in world.entities_in_circle(p_center, 128) if x.is_interactable()]
            inter.sort(key=lambda x: Utils.dist(x.center(), p_center))
            for i in range(0, len(inter)):
                #  trying to find the closest interactable in range
                dist = Utils.dist(inter[i].center(), p_center)
                if dist <= inter[i].interact_radius():
                    closest_interactable = inter[i]
                    break

            if self._can_interact() and input_state.was_pressed(gs.get_instance().settings().interact_key()):
                if self.held_item is not None:
                    self.drop_held_item(player_entity, world)
                elif closest_interactable is not None:
                    closest_interactable.interact(world)
                    gs.get_instance().event_queue().add(events.EntityInteractEvent(closest_interactable))

            # you can keep moving during the attack windup
            left_held = self._is_actionable and input_state.is_held(gs.get_instance().settings().left_key())
            right_held = self._is_actionable and input_state.is_held(gs.get_instance().settings().right_key())
            down_held = self._is_actionable and input_state.is_held(gs.get_instance().settings().down_key())
            up_held = self._is_actionable and input_state.is_held(gs.get_instance().settings().up_key())

            move_x = int(right_held) - int(left_held)
            move_y = int(down_held) - int(up_held)

            self.is_moving = move_x != 0 or move_y != 0

            if move_x != 0 and move_y != 0:
                move_x /= 1.4142
                move_y /= 1.4142

            if self.attack_state.is_delaying() or self.recoil_progress() < 1:
                # half speed after attacking or being attacked
                move_x /= 2
                move_y /= 2

            move_x *= self.move_speed()
            move_y *= self.move_speed()

            total_push = self.get_total_push()
            move_x += total_push[0] * 2
            move_y += total_push[1] * 2
            self.update_pushes()

            player_entity.move(move_x, move_y, world=world, and_search=True)
            if move_x != 0:
                self.facing_right = move_x > 0

            self._update_held_item(player_entity, world)

            if self.held_item is None and self._can_interact() and closest_interactable is not None:
                # TODO - holy special case batman
                if isinstance(closest_interactable, ReturnExitEntity):
                    self._update_hover_text(player_entity, closest_interactable.interact_text(), world)
                else:
                    self._update_hover_text(closest_interactable, closest_interactable.interact_text(), world)
            else:
                self._update_hover_text(None, None, world)
        else:
            self._update_hover_text(None, None, world)

        color = self.recoil_color()
        player_entity.update_images(self.get_sprite(), self.facing_right, color=color)
        player_entity.set_shadow_sprite(self.get_shadow_sprite())

        player_entity.set_visible(self._is_visible)

    def _get_held_item_offset(self, spr):
        h = spr.height() * 2
        # XXX this is pretty boo
        if self.is_moving:
            idx = gs.get_instance().anim_tick % len(spriteref.player_move_arms_up_all)
            return [(0, -54 - h), (0, -52 - h), (0, -50 - h), (0, -52 - h)][idx]
        else:
            idx = gs.get_instance().anim_tick // 2 % len(spriteref.player_idle_arms_up_all)
            return [(0, -54 - h), (0, -52 - h)][idx]

    def _update_held_item(self, player_entity, world):
        if self._held_item_image_entity_uid is None:
            current_anim = None
        else:
            current_anim = world.get_entity(self._held_item_image_entity_uid, onscreen=False)

        if self.held_item is None and not current_anim is None:
            world.remove(current_anim)
            self._held_item_image_entity_uid = None
        elif self.held_item is not None:
            sprite = spriteref.get_item_entity_sprite(self.held_item.cubes)
            pos = player_entity.center()
            if current_anim is None:
                current_anim = AnimationEntity(pos[0], pos[1], [sprite], 60, layer_id=spriteref.ENTITY_LAYER)
                current_anim.on_finish_mode = AnimationEntity.LOOP_ON_FINISH
                self._held_item_image_entity_uid = current_anim.get_uid()
                world.add(current_anim)

            current_anim.set_sprites([sprite])
            current_anim.set_sprite_offset(self._get_held_item_offset(sprite))
            current_anim.set_center(pos[0], pos[1])
            current_anim.set_y_centered(False)
            current_anim.set_color(self.held_item.color)

    def get_sprite(self):
        if self.attack_state.is_attacking():
            progress = self.attack_state.attack_progress()
            idx = int(progress * len(spriteref.player_attacks))
            return spriteref.player_attacks[idx]
        elif self.attack_state.is_delaying():
            return spriteref.player_squat
        elif self.is_moving:
            if self.held_item is not None:
                return spriteref.player_move_arms_up_all[gs.get_instance().anim_tick % len(spriteref.player_move_arms_up_all)]
            else:
                return spriteref.player_move_all[gs.get_instance().anim_tick % len(spriteref.player_move_all)]
        else:
            if self.held_item is not None:
                return spriteref.player_idle_arms_up_all[(gs.get_instance().anim_tick // 2) % len(spriteref.player_idle_arms_up_all)]
            else:
                return spriteref.player_idle_all[(gs.get_instance().anim_tick // 2) % len(spriteref.player_idle_all)]

    def get_shadow_sprite(self):
        if self.attack_state.is_attacking():
            progress = self.attack_state.attack_progress()
            if 0.25 < progress < 0.75:
                return spriteref.small_shadow
        return spriteref.medium_shadow


class EnemyState(ActorState):

    def __init__(self, template, level, stats, is_rare):
        """
            stats: map StatType -> value
        """
        self.template = template
        self.is_rare = is_rare
        self.sprites = template.get_sprites()
        self.stats = stats
        ActorState.__init__(self, template.get_name(), level, stats)
        self.jump_height = 32

        self.facing_left = True
        self.facing_left_last_frame = None  # used to detect and prevent left-right flickering

        self.is_aggro = False
        self.aggro_radius = 350
        self.forget_radius = 450

        self.attack_state.set_attack(template.get_attack())
        self.special_attack = None

        self.movement_ai_state = {}
        self._anim_offset = int(60 * random.random())

        self._lunge_duration = 45
        self._lunge_count = self._lunge_duration
        self._lunge_direction = (0, 0)

    def lunge_progress(self):
        return Utils.bound(self._lunge_count / self._lunge_duration, 0.0, 1.0)

    def _get_movespeed_mult(self):
        res = 1

        if self.is_lunging():
            if self.lunge_progress() < 0.2:
                res *= 0.2  # bit of slowdown at the beginning to serve as visual indicator
            else:
                res *= 5

        if self.recoil_progress() < 1.0:
            res *= 0.5

        return res

    def duplicate(self):
        res = EnemyState(self.template, self.level(), dict(self.stats), self.is_rare)
        res.set_special_attack(self.special_attack)
        return res

    def base_color(self):
        if self.special_attack is not None:
            sp_color = self.special_attack.dmg_color
            res = (1 - (1 - sp_color[0]) * 0.15,
                   1 - (1 - sp_color[1]) * 0.15,
                   1 - (1 - sp_color[2]) * 0.15)
            return res
        else:
            return ActorState.base_color(self)

    def stat_value(self, stat_type):
        derived = self._compute_derived_stat(stat_type)
        if derived is not None:
            return derived

        elif stat_type in self.stats:
            return self.stats[stat_type]
        else:
            return 0

    def _handle_death(self, entity, world):
        if self.template.drops_loot():
            loot = LootFactory.gen_loot(self.level(), self.is_rare)
        else:
            loot = []

        sound_effects.play_sound(sound_effects.Effects.ENEMY_DEATH)
        position = entity.center()

        for item in loot:
            item_ent = ItemEntity(item, *position)
            world.add(item_ent)

        if self.template.drops_loot():
            for _ in range(0, LootFactory.gen_num_potions_to_drop(self.level(), self.is_rare)):
                world.add(PotionEntity(*entity.center()))

        self.template.special_death_action(self.level(), entity, world)

        world.remove(entity)

        if self.template.show_death_explosion():
            splosion = AnimationEntity(entity.x(), entity.y() - 24,
                                       spriteref.explosions, 40,
                                       spriteref.ENTITY_LAYER, scale=4)
            splosion.set_color((0, 0, 0))
            world.add(splosion)

        gs.get_instance().event_queue().add(events.EnemyDiedEvent(entity.get_uid(), self.template, position))

    def _get_sprite(self, entity, world):
        return self.sprites[((gs.get_instance().anim_tick + self._anim_offset) // 2) % len(self.sprites)]

    def _get_sprite_offset(self):
        if self.attack_state.is_attacking() and self.attack_state.current_attack.is_jumpy:
            prog = self.attack_state.attack_progress()
            return (0, -Utils.parabola_height(self.jump_height, prog))
        else:
            return (0, 0)

    def get_pathfinding(self):
        return self.template.get_pathfinding()

    def update(self, entity, world, input_state):
        self.handle_floating_text(entity, world)

        if not gs.get_instance().world_updates_paused():
            if self.hp() <= 0:
                self._handle_death(entity, world)
            else:

                if (gs.get_instance().tick_counter + self._anim_offset) % 60 == 0:
                    regen = self.stat_value(StatType.LIFE_REGEN)
                    self.do_heal(regen)

                self.update_status_effects(entity, world)

                if self.took_damage_x_ticks_ago < self.damage_recoil:
                    self.took_damage_x_ticks_ago += 1

                if self.set_color_x_ticks_ago < self.damage_recoil:
                    self.set_color_x_ticks_ago += 1

                # updating aggro
                if random.random() < 0.05:
                    p = world.get_player()
                    if p is not None:
                        dist = Utils.dist(p.center(), entity.center())
                        if self.is_aggro:
                            self.is_aggro = dist <= self.forget_radius
                        else:
                            self.is_aggro = dist <= self.aggro_radius

                # doing attacks
                if random.random() < 0.1 and self._should_attack(entity, world):
                    self.attack_state.start_attack(self)

                self.attack_state.update(entity, world)

                if self.is_lunging():
                    move_dir = self._lunge_direction if self.lunge_progress() > 0.3 else (0, 0)
                elif world.get_hidden_at(*entity.center()) or not self.is_aggro:
                    move_dir = IdleAI.get_move_dir(entity, self.movement_ai_state, world)
                else:
                    path_type = self.get_pathfinding()
                    if path_type == PathfindingType.PASSIVE:
                        move_dir = IdleAI.get_move_dir(entity, self.movement_ai_state, world)
                    elif path_type == PathfindingType.STOPPED:
                        move_dir = (0, 0)
                    elif path_type == PathfindingType.BASIC_CUT_OFF:
                        move_dir = BasicCutOffAI.get_move_dir(entity, self.movement_ai_state, world)
                    elif path_type == PathfindingType.BASIC_CHASE:
                        move_dir = BasicChaseAI.get_move_dir(entity, self.movement_ai_state, world)
                    else:
                        move_dir = BasicChaseAI.get_move_dir(entity, self.movement_ai_state, world)

                # doing lunges
                if random.random() < 0.02 and self._should_lunge(entity, world):
                    self._lunge_count = 0
                    self._lunge_direction = move_dir

                move_x, move_y = move_dir
                move_x *= 1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100
                move_y *= 1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100

                ms_mult = self._get_movespeed_mult()
                move_x *= ms_mult
                move_y *= ms_mult

                total_push = self.get_total_push()
                move_x += total_push[0]
                move_y += total_push[1]
                self.update_pushes()

                if self.is_lunging():
                    self._lunge_count += 1

                entity.move(move_x, move_y, world=world, and_search=True)

                if move_x != 0:
                    # don't actually turn until we've been moving that direction for two frames
                    if self.facing_left_last_frame == (move_x < 0):
                        self.facing_left = move_x < 0

                    self.facing_left_last_frame = move_x < 0
                else:
                    self.facing_left_last_frame = None

        color = self.recoil_color()
        sprite = self._get_sprite(entity, world)
        health_ratio = Utils.bound(self.hp() / self.stat_value(ActorStatType.HP), 0.0, 1.0)
        hp_color = self.get_hp_color()

        entity.update_images(sprite, self.facing_left, health_ratio, color=color, hp_color=hp_color,
                             offset=self._get_sprite_offset(), shadow_sprite=self.template.get_shadow_sprite())

    def _should_attack(self, entity, world):
        p = world.get_player()
        if (self.attack_state.can_attack() and
                self.template.can_attack() and
                self.is_aggro and
                p is not None and
                self.took_damage_x_ticks_ago >= self.damage_recoil and
                not world.get_hidden_at(*entity.center())):
            radius = self.attack_state.get_attack_range(entity.state)

            return Utils.dist(p.center(), entity.center()) < radius * 1.5
        else:
            return False

    def is_lunging(self):
        return self.lunge_progress() < 1.0

    def _should_lunge(self, entity, world):
        return (self.template.get_lunges() and
                self.attack_state.can_attack() and
                self.is_aggro and
                self.took_damage_x_ticks_ago >= self.damage_recoil and
                not self.is_lunging())

    def set_special_attack(self, attack):
        self.special_attack = attack
        if attack is None:
            self.attack_state.set_attack(self.template.get_attack())
        else:
            self.attack_state.set_attack(attack)


class PathfindingType(Enum):
    PASSIVE = 0,
    BASIC_CHASE = 1,
    SMART_CHASE = 2,
    BASIC_CUT_OFF = 3,
    STOPPED = 4


class MovementAI():

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        return (0, 0)


class BasicChaseAI(MovementAI):
    @staticmethod
    def basic_move_towards_target(ai_state, start_pos, target_pos):
        if "basic_angle_offset_degrees" not in ai_state:
            ai_state["basic_angle_offset_degrees"] = 0

        if random.random() < 0.03:
            dist = Utils.dist(start_pos, target_pos)
            max_angle_range = 80  # plus or minus
            angle = random.random() * max_angle_range * Utils.bound((400 - dist) / 400, 0.25, 1.0)
            angle *= 1.0 if random.random() < 0.5 else -1.0

            ai_state["basic_angle_offset_degrees"] = angle

        rotate_rads = Utils.to_rads(ai_state["basic_angle_offset_degrees"])

        towards_player = Utils.set_length(Utils.sub(target_pos, start_pos), 1.0)

        return Utils.rotate(towards_player, rotate_rads)

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        p = world.get_player()
        if p is None:
            return (0, 0)
        else:
            e_pos = entity.center()
            p_pos = p.center()

            return BasicChaseAI.basic_move_towards_target(ai_state, e_pos, p_pos)


class BasicCutOffAI(MovementAI):

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        p = world.get_player()
        if p is None:
            return (0, 0)
        else:
            e_pos = entity.center()
            p_pos = p.center()
            p_vel = p.get_vel()
            target_pos = Utils.add(p_pos, Utils.mult(p_vel, 64 + 256 * random.random()))

            return BasicChaseAI.basic_move_towards_target(ai_state, e_pos, target_pos)


class IdleAI(MovementAI):

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        if "idle_dir" not in ai_state:
            ai_state["idle_dir"] = [0, 0]

        res = ai_state["idle_dir"]

        if random.random() < 0.01:
            i = int(8 * random.random())
            if i >= 4:
                res = [0, 0]
            else:
                res = [[-1, 0], [1, 0], [0, 1], [0, -1]][i]

        x1 = entity.x()
        x2 = entity.x() + entity.w()
        y1 = entity.y()
        y2 = entity.y() + entity.h()

        if res[0] < 0:
            if world.is_solid_at(x1 - 1, y1) or world.is_solid_at(x1 - 1, y2):
                res[0] = 1
        elif res[0] > 0:
            if world.is_solid_at(x2 + 1, y1) or world.is_solid_at(x2 + 1, y2):
                res[0] = -1
        elif res[1] > 0:
            if world.is_solid_at(x1, y2 + 1) or world.is_solid_at(x2, y2 + 1):
                res[1] = -1
        elif res[1] < 0:
            if world.is_solid_at(x1, y1 - 1) or world.is_solid_at(x2, y1 - 1):
                res[1] = 1

        ai_state["idle_dir"] = res
        return ai_state["idle_dir"]