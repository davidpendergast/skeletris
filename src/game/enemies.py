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


class EnemyState(ActorState):

    def __init__(self, name, sprites, level, stats):
        """
            stats: map StatType -> value
        """
        self.sprites = sprites
        self.stats = stats
        self.dir = [0, 0]
        self.facing_left = True
        ActorState.__init__(self, name, 0, stats)
        
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
            
            if random.random() < 0.01:
                i = int(10 * random.random())
                if i >= 4:
                    self.dir = [0, 0]
                else:
                    self.dir = [[-1, 0], [1, 0], [0, 1], [0, -1]][i]
        
            x1 = entity.x()
            x2 = entity.x() + entity.w()
            y1 = entity.y()
            y2 = entity.y() + entity.h()
            
            if self.dir[0] < 0:
                if world.is_solid_at(x1 - 1, y1) or world.is_solid_at(x1 - 1, y2):
                    self.dir[0] = 1
            elif self.dir[0] > 0:
                if world.is_solid_at(x2 + 1, y1) or world.is_solid_at(x2 + 1, y2):
                    self.dir[0] = -1
            elif self.dir[1] > 0:
                if world.is_solid_at(x1, y2 + 1) or world.is_solid_at(x2, y2 + 1):
                    self.dir[1] = -1
            elif self.dir[1] < 0:
                if world.is_solid_at(x1, y1 - 1) or world.is_solid_at(x2, y1 - 1):
                    self.dir[1] = 1
            
            move_x = self.dir[0] * 0.65
            move_y = self.dir[1] * 0.65
            entity.move(move_x, move_y, world=world, and_search=True)
            
            if move_x != 0:
                self.facing_left = move_x < 0 
                
            color_scale = min(1.0, self.took_damage_x_ticks_ago / 15)
            img_color = (1, color_scale, color_scale)
            
            sprite = self.sprites[(gs.anim_tick // 2) % len(self.sprites)]

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

