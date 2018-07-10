import random

from enum import Enum

from src.attacks import attacks as attacks
from src.game import spriteref as spriteref, inputs as inputs
from src.game.stats import PlayerStatType, StatType
from src.utils.util import Utils
from src.world.entities import AnimationEntity, FloatingTextEntity, ItemEntity


def show_floating_text(text, color, scale, entity, world):
    x_offs = int(15 * (0.5 - random.random()))
    text = FloatingTextEntity(text, 25, color, anchor=None, scale=scale,
                              start_offs=(x_offs, -64), end_offs=(x_offs, -96))
    text.set_x(entity.center()[0] - text.w() // 2)
    text.set_y(entity.center()[1] - text.h() // 2)
    world.add(text)


class ActorState:

    R_TEXT_COLOR = (0.75, 0.0, 0.0)
    G_TEXT_COLOR = (0.2, 0.85, 0.2)
    B_TEXT_COLOR = (0.2, 0.2, 0.85)

    def __init__(self, name, level, base_values):
        self._name = name
        self._level = level
        self._base_values = base_values
        self.current_hp = self.stat_value(PlayerStatType.HP)

        self.attack_state = attacks.AttackState()

        self.damage_recoil = 15
        self.took_damage_x_ticks_ago = self.damage_recoil
        self.current_knockback = (0, 0)
        self.dmg_color = (1, 0, 0)

        self.damage_amounts = []
        self.heal_amounts = []
        self.avoided_attack = False

    def update(self, entity, world, gs, input_state):
        pass

    def name(self):
        return self._name

    def level(self):
        return self._level

    def get_base_stats(self):
        return dict(self._base_values)

    def max_hp(self):
        return self.stat_value(PlayerStatType.HP)

    def hp(self):
        return Utils.bound(self.current_hp, 0, self.max_hp())

    def set_hp(self, value):
        self.current_hp = Utils.bound(value, 0, self.max_hp())

    def move_speed(self):
        return self.stat_value(PlayerStatType.MOVESPEED)

    def recoil_progress(self):
        return Utils.bound(self.took_damage_x_ticks_ago / self.damage_recoil, 0.0, 1.0)

    def recoil_color(self):
        return Utils.linear_interp(self.dmg_color, (1, 1, 1), self.recoil_progress())

    def is_invuln(self):
        return False

    def get_dodge_text_info(self):
        return ("miss", 2, ActorState.B_TEXT_COLOR)

    def get_dmg_text_info(self):
        return ("-{}", 2, ActorState.R_TEXT_COLOR)

    def get_heal_text_info(self):
        return ("+{}", 2, ActorState.G_TEXT_COLOR)

    def handle_floating_text(self, entity, world):
        dmg_info = self.get_dmg_text_info()
        if dmg_info is not None:
            for dmg in self.damage_amounts:
                show_floating_text(dmg_info[0].format(round(dmg)), dmg_info[2], dmg_info[1], entity, world)
        self.damage_amounts.clear()

        heal_info = self.get_heal_text_info()
        if heal_info is not None:
            for heal in self.heal_amounts:
                if heal < 0.05:
                    continue
                heal_amt = round(heal) if heal >= 1 else round(heal*10)/10
                show_floating_text(heal_info[0].format(heal_amt), heal_info[2], heal_info[1], entity, world)
        self.heal_amounts.clear()

        avoid_info = self.get_dodge_text_info()
        if avoid_info is not None:
            if self.avoided_attack:
                show_floating_text(avoid_info[0], avoid_info[2], avoid_info[1], entity, world)
        self.avoided_attack = False

    def deal_damage(self, damage, knockback=(0, 0), color=(1, 0, 0)):
        if damage > 0 and not self.is_invuln():
            self.set_hp(self.hp() - damage)
            self.took_damage_x_ticks_ago = 0
            self.dmg_color = color
            self.current_knockback = knockback
            self.damage_amounts.append(damage)

    def do_heal(self, amount):
        if amount > 0:
            prev_hp = self.hp()
            self.set_hp(prev_hp + amount)
            diff = self.hp() - prev_hp
            self.heal_amounts.append(diff)

    def was_missed(self):
        self.avoided_attack = True

    def _compute_derived_stat(self, stat_type):
        """
            returns: None if stat is not derived, else stat value
        """
        if stat_type is PlayerStatType.HP:
            vit = self.stat_value(StatType.VIT)
            plus_hp = self.stat_value(StatType.MAX_HEALTH)
            return round(vit * 4 * (1 + plus_hp / 100))

        elif stat_type is PlayerStatType.MOVESPEED:
            base = self._base_values[stat_type]
            return base * (1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100)

        elif stat_type is PlayerStatType.DPS:
            return self.attack_state.get_dps(self)

    def stat_value(self, stat_type):
        return 0


class PlayerState(ActorState):
    def __init__(self, name, inventory):
        self._inventory = inventory

        ActorState.__init__(self, name, 0, {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10,
            PlayerStatType.MOVESPEED: 2.5,
        })

        self.current_sprite = spriteref.player_idle_0

        self.attack_state.set_attack(attacks.GROUND_POUND)
        # self.attack_state.set_attack(attacks.MINION_LAUNCH_ATTACK)

        self._damage_last_tick = 0
        self._healing_last_tick = 0

        self.is_moving = False
        self.facing_right = True

        self._is_dead = False
        self.death_seq_duration = 120
        self.death_seq_tick = 0

    def inventory(self):
        return self._inventory

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
        death_anim.set_vel(Utils.mult(self.current_knockback, 2), fric=0.90, collides=True)

        world.add(death_anim)

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

    def update(self, player_entity, world, gs, input_state):
        if self._is_dead:
            if self.death_seq_tick >= self.death_seq_duration:
                gs.player_died()
            else:
                self.death_seq_tick += 1

        if player_entity is None:
            return

        self._damage_last_tick = sum(self.damage_amounts)
        self._healing_last_tick = sum(self.damage_amounts)
        self.handle_floating_text(player_entity, world)

        if self.hp() <= 0:
            self._is_dead = True
            self._handle_death(player_entity, world)
            self._damage_last_tick = 0
            return

        if gs.tick_counter % 60 == 0:
            regen = self.stat_value(StatType.LIFE_REGEN)
            self.do_heal(regen)

        if self.took_damage_x_ticks_ago < self.damage_recoil:
            self.took_damage_x_ticks_ago += 1

        if input_state.is_held(inputs.ATTACK) and self.attack_state.can_attack():
            self.attack_state.start_attack(self)

        self.attack_state.update(player_entity, world, gs)

        # you can keep moving during the attack windup
        move_x = int(input_state.is_held(inputs.RIGHT)) - int(input_state.is_held(inputs.LEFT))
        move_y = int(input_state.is_held(inputs.DOWN)) - int(input_state.is_held(inputs.UP))

        self.is_moving = move_x != 0 or move_y != 0

        if move_x != 0 and move_y != 0:
            move_x /= 1.4142
            move_y /= 1.4142

        if self.attack_state.is_delaying() or self.recoil_progress() < 1:
            # half speed after attacking or being attacked
            move_x /= 2
            move_y /= 2

        if self.recoil_progress() < 1:
            move_x += self.current_knockback[0] * (1 - self.recoil_progress())
            move_y += self.current_knockback[1] * (1 - self.recoil_progress())

        move_x *= self.move_speed()
        move_y *= self.move_speed()

        player_entity.move(move_x, move_y, world=world, and_search=True)
        if move_x != 0:
            self.facing_right = move_x > 0

        color = self.recoil_color()

        player_entity.update_images(self.get_sprite(gs), self.facing_right, color=color)
        player_entity.set_shadow_sprite(self.get_shadow_sprite())

    def get_sprite(self, gs):
        if self.attack_state.is_attacking():
            progress = self.attack_state.attack_progress()
            idx = int(progress * len(spriteref.player_attacks))
            return spriteref.player_attacks[idx]
        elif self.attack_state.is_delaying():
            return spriteref.player_squat
        elif self.is_moving:
            return spriteref.player_move_all[gs.anim_tick % len(spriteref.player_move_all)]
        else:
            return spriteref.player_idle_all[(gs.anim_tick // 2) % len(spriteref.player_idle_all)]

    def get_shadow_sprite(self):
        if self.attack_state.is_attacking():
            progress = self.attack_state.attack_progress()
            if 0.25 < progress < 0.75:
                return spriteref.small_shadow
        return spriteref.medium_shadow

    def get_attack_state(self):
        return self.attack_state


class EnemyState(ActorState):

    def __init__(self, template, level, stats):
        """
            stats: map StatType -> value
        """
        self.template = template
        self.sprites = template.get_sprites()
        self.stats = stats
        ActorState.__init__(self, template.get_name(), level, stats)

        self.facing_left = True
        self.facing_left_last_frame = None  # used to detect and prevent left-right flickering

        self.is_aggro = False
        self.aggro_radius = 350
        self.forget_radius = 450

        self.attack_state.set_attack(template.get_attack())
        self.movement_ai_state = {}
        self._anim_offset = int(60 * random.random())

    def duplicate(self):
        return EnemyState(self.template, self.level(), dict(self.stats))

    def stat_value(self, stat_type):
        derived = self._compute_derived_stat(stat_type)
        if derived is not None:
            return derived

        elif stat_type in self.stats:
            return self.stats[stat_type]
        else:
            return 0

    def _handle_death(self, entity, world, gs):
        loot = self.template.get_loot(self.level())

        for item in loot:
            item_ent = ItemEntity(item, *entity.center())
            world.add(item_ent)

        self.template.special_death_action(self.level(), entity, world)

        world.remove(entity)
        splosion = AnimationEntity(entity.x(), entity.y() - 24,
                                   spriteref.explosions, 40, spriteref.ENTITY_LAYER, scale=4)
        splosion.set_color((0, 0, 0))
        world.add(splosion)
        gs.kill_count += 1

    def update(self, entity, world, gs, input_state):
        self.handle_floating_text(entity, world)

        if self.hp() <= 0:
            self._handle_death(entity, world, gs)
        else:

            if (gs.tick_counter + self._anim_offset) % 60 == 0:
                regen = self.stat_value(StatType.LIFE_REGEN)
                self.do_heal(regen)

            if self.took_damage_x_ticks_ago < self.damage_recoil:
                self.took_damage_x_ticks_ago += 1

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
            if random.random() < 0.1:
                if self.is_aggro and self._should_attack(entity, world):
                    self.attack_state.start_attack(self)

            self.attack_state.update(entity, world, gs)

            if world.get_hidden_at(*entity.center()) or not self.is_aggro:
                move_dir = IdleAI.get_move_dir(entity, self.movement_ai_state, world)
            else:
                move_dir = BasicChaseAI.get_move_dir(entity, self.movement_ai_state, world)

            move_x, move_y = move_dir
            move_x *= 1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100
            move_y *= 1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100

            if self.recoil_progress() < 1.0:
                move_x /= 2
                move_y /= 2

            if self.recoil_progress() < 1:
                move_x += self.current_knockback[0] * (1 - self.recoil_progress())
                move_y += self.current_knockback[1] * (1 - self.recoil_progress())

            entity.move(move_x, move_y, world=world, and_search=True)

            if move_x != 0:
                # don't actually turn until we've been moving that direction for two frames
                if self.facing_left_last_frame == (move_x < 0):
                    self.facing_left = move_x < 0

                self.facing_left_last_frame = move_x < 0
            else:
                self.facing_left_last_frame = None

            color = self.recoil_color()

            sprite = self.sprites[((gs.anim_tick + self._anim_offset) // 2) % len(self.sprites)]

            health_ratio = Utils.bound(self.hp() / self.stat_value(PlayerStatType.HP), 0.0, 1.0)

            entity.update_images(sprite, self.facing_left, health_ratio, color=color,
                                 shadow_sprite=self.template.get_shadow_sprite())

    def _should_attack(self, entity, world):
        p = world.get_player()
        return (self.attack_state.can_attack() and
                self.is_aggro and
                p is not None and
                self.took_damage_x_ticks_ago >= self.damage_recoil and
                not world.get_hidden_at(*entity.center()))


class PathfindingType(Enum):
    PASSIVE = 0,
    BASIC_CHASE = 1,
    SMART_CHASE = 2


class MovementAI():

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        return (0, 0)


class BasicChaseAI(MovementAI):

    @staticmethod
    def get_move_dir(entity, ai_state, world):
        p = world.get_player()
        if p is None:
            return (0, 0)
        else:
            e_pos = entity.center()
            p_pos = p.center()

            if "basic_angle_offset_degrees" not in ai_state:
                ai_state["basic_angle_offset_degrees"] = 0

            if random.random() < 0.03:
                dist = Utils.dist(e_pos, p_pos)
                max_angle_range = 80  # plus or minus
                angle = random.random() * max_angle_range * Utils.bound((400 - dist) / 400, 0.25, 1.0)
                angle *= 1.0 if random.random() < 0.5 else -1.0

                ai_state["basic_angle_offset_degrees"] = angle

            rotate_rads = Utils.to_rads(ai_state["basic_angle_offset_degrees"])

            towards_player = Utils.set_length(Utils.sub(p_pos, e_pos), 1.0)
            return Utils.rotate(towards_player, rotate_rads)


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