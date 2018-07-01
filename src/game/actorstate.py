import random

from src.attacks import attacks as attacks
from src.game import spriteref as spriteref, inputs as inputs
from src.game.stats import PlayerStatType, StatType
from src.utils.util import Utils
from src.world.entities import AnimationEntity


class ActorState:
    def __init__(self, name, level, base_values):
        self._name = name
        self._level = level
        self._base_values = base_values
        self.current_hp = self.stat_value(PlayerStatType.HP)

    def update(self, entity, world, gs, input_state):
        pass

    def name(self):
        return self._name

    def level(self):
        return self._level

    def hp(self):
        return self.current_hp

    def set_hp(self, value):
        self.current_hp = value

    def move_speed(self):
        return self.stat_value(PlayerStatType.MOVESPEED)

    def deal_damage(self, damage):
        self.set_hp(self.hp() - damage)

    def _compute_derived_stat(self, stat_type):
        """
            returns: None if stat is not derived, else stat value
        """
        if stat_type is PlayerStatType.HP:
            vit = self.stat_value(StatType.VIT)
            plus_hp = self.stat_value(StatType.MAX_HEALTH)
            return round(vit * 4 * (1 + plus_hp / 100))

        elif stat_type is PlayerStatType.DPS:
            att = self.stat_value(StatType.ATT)
            att_dmg_inc = self.stat_value(StatType.ATTACK_DAMAGE)
            ticks_per_att = self._compute_derived_stat(PlayerStatType.TICKS_PER_ATTACK)
            attacks_per_sec = 60 / ticks_per_att
            return round((att + (1 + att_dmg_inc / 100)) * attacks_per_sec)

        elif stat_type is PlayerStatType.TICKS_PER_ATTACK:
            base = self._base_values[stat_type]
            speed = 1 / base
            att_speed_inc = self.stat_value(StatType.ATTACK_SPEED)
            speed = speed * (1 + att_speed_inc / 100)
            return round(1 / speed)

        elif stat_type is PlayerStatType.MOVESPEED:
            base = self._base_values[stat_type]
            return base * (1 + self.stat_value(StatType.MOVEMENT_SPEED) / 100)

        elif stat_type is PlayerStatType.ATTACK_RADIUS:
            base = self._base_values[stat_type]
            return round(base * (1 + self.stat_value(StatType.ATTACK_RADIUS) / 100))

    def stat_value(self, stat_type):
        return 0


class PlayerState(ActorState):
    def __init__(self, name, inventory):
        self._inventory = inventory

        ActorState.__init__(self, name, 0, {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10,
            PlayerStatType.TICKS_PER_ATTACK: 30,
            PlayerStatType.MOVESPEED: 2.5,
            PlayerStatType.ATTACK_RADIUS: 64
        })

        self.current_sprite = spriteref.player_idle_0

        self.attack_state = attacks.AttackState()
        self.attack_state.set_attack(attacks.GROUND_POUND)

        self.is_moving = False
        self.facing_right = True

    def inventory(self):
        return self._inventory

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

    def update(self, player_entity, world, gs, input_state):
        if player_entity is None:
            return

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

        if self.attack_state.is_delaying():
            # half speed after attacking
            move_x /= 2
            move_y /= 2

        move_x *= self.move_speed()
        move_y *= self.move_speed()

        player_entity.move(move_x, move_y, world=world, and_search=True)
        if move_x != 0:
            self.facing_right = move_x > 0

        player_entity.update_images(self.get_sprite(gs), self.facing_right)
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


class EnemyState(ActorState):

    def __init__(self, name, sprites, level, stats):
        """
            stats: map StatType -> value
        """
        self.sprites = sprites
        self.stats = stats

        self.facing_left = True
        self.facing_left_last_frame = None  # used to detect and prevent left-right flickering

        self.movement_ai_state = {}
        ActorState.__init__(self, name, 0, stats)
        self._anim_offset = int(20 * random.random())

        self.took_damage_x_ticks_ago = 15

    def duplicate(self):
        return EnemyState(self.name, self.sprites, self.level, dict(self.stats))

    def stat_value(self, stat_type):
        derived = self._compute_derived_stat(stat_type)
        if derived is not None:
            return derived

        elif stat_type in self.stats:
            return self.stats[stat_type]
        else:
            return 0

    def update(self, entity, world, gs, input_state):
        if self.hp() <= 0:
            import src.game.enemies as enemies
            loot = enemies.LootFactory.gen_loot(entity.center(), 0, self.level())

            for l in loot:
                world.add(l)

            world.remove(entity)
            splosion = AnimationEntity(entity.x(), entity.y() - 24,
                                       spriteref.explosions, 40, spriteref.ENTITY_LAYER, scale=4)
            world.add(splosion)
        else:
            if self.took_damage_x_ticks_ago < 15:
                self.took_damage_x_ticks_ago += 1

            if world.get_hidden_at(*entity.center()):
                move_dir = IdleAI.get_move_dir(entity, self.movement_ai_state, world)
            else:
                move_dir = BasicChaseAI.get_move_dir(entity, self.movement_ai_state, world)

            move_x, move_y = move_dir
            move_x *= 0.65
            move_y *= 0.65
            entity.move(move_x, move_y, world=world, and_search=True)

            if move_x != 0:
                # don't actually turn until we've been moving that direction for two frames
                if self.facing_left_last_frame == (move_x < 0):
                    self.facing_left = move_x < 0

                self.facing_left_last_frame = move_x < 0
            else:
                self.facing_left_last_frame = None

            color_scale = min(1.0, self.took_damage_x_ticks_ago / 15)
            img_color = (1, color_scale, color_scale)

            sprite = self.sprites[((gs.anim_tick + self._anim_offset) // 2) % len(self.sprites)]

            health_ratio = Utils.bound(self.hp() / self.stat_value(PlayerStatType.HP), 0.0, 1.0)

            entity.update_images(sprite, self.facing_left, health_ratio, color=img_color)

    def deal_damage(self, damage):
        print("enemy took {} damage".format(damage))
        ActorState.deal_damage(self, damage)
        if damage > 0:
            self.took_damage_x_ticks_ago = 0


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