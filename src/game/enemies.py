import random
import src.game.spriteref as spriteref
from src.items.item import StatType, ItemFactory
from src.world.entities import Enemy, ItemEntity, PotionEntity, AnimationEntity
from src.game.inventory import ActorState, PlayerStatType
from src.utils.util import Utils


class LootFactory:

    @staticmethod
    def gen_loot(pos, player_lvl, dungeon_level):
        loot = []
        for _ in range(0, 3):
            if random.random() < 0.50:  
                loot.append(ItemEntity(ItemFactory.gen_item(), *pos))
        for _ in range(0, 3):
            if random.random() < 0.75:
                loot.append(PotionEntity(*pos))
        return loot


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


class EnemyState(ActorState):

    def __init__(self, name, sprites, level, stats):
        """
            stats: map StatType -> value
        """
        self.sprites = sprites
        self.stats = stats

        self.facing_left = True
        self.facing_left_last_frame = None # used to detect and prevent left-right flickering

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
            loot = LootFactory.gen_loot(entity.center(), 0, self.level())
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
        self.took_damage_x_ticks_ago = 0
        self.set_hp(self.hp() - damage)
     
     
class EnemyFactory:

    @staticmethod
    def gen_enemy(level):
        i = int(random.random() * len(spriteref.enemies_all))
        stats = {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10
        }
        state = EnemyState("enem1", spriteref.enemies_all[i], level, stats)
        
        return Enemy(0, 0, state)

    @staticmethod
    def gen_enemies(level, n=None):
        if n is None:
            n = int(1 + random.random()*4)

        first = EnemyFactory.gen_enemy(level)
        res = [first]
        for _ in range(1, n):
            res.append(Enemy(0, 0, first.state.duplicate()))

        return res

