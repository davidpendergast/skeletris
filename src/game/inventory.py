from enum import Enum

from src.items.item import StatType
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.entities import AttackCircleArt


class ItemGrid:
    def __init__(self, size):
        self.size = size
        self.items = {} # coords -> item
    
    def can_place(self, item, pos):
        if (item.w() + pos[0] > self.size[0] or 
                item.h() + pos[1] > self.size[1]):
            return False
            
        for cell in self._cells_occupied(item, pos):
            if self.item_at_position(cell) is not None:
                return False
                
        return True
        
    def place(self, item, pos):
        if self.can_place(item, pos):
            self.items[pos] = item
            
    def try_to_replace(self, item, pos):
        if (item.w() + pos[0] > self.size[0] or 
                item.h() + pos[1] > self.size[1]):
            return None
        
        hit_item = None    
        for cell in self._cells_occupied(item, pos):
            item_at_cell = self.item_at_position(cell)
            if item_at_cell is not None:
                if hit_item is not None and hit_item is not item_at_cell:
                    # we're hitting two items, can't replace
                    return None
                else:
                    hit_item = item_at_cell
        
        if hit_item is not None:
            # we hit exactly one thing, so we can replace
            self.remove(hit_item)
            self.place(item, pos)
            return hit_item
        else:
            return None

    def remove(self, item):
        for pos in self.items:
            if self.items[pos] is item:
                del self.items[pos]
                return True
        return False
        
    def item_at_position(self, pos):
        for origin in self.items:
            for cell in self._cells_occupied(self.items[origin], origin):
                if cell == pos:
                    return self.items[origin]
        return None
        
    def _cells_occupied(self, item, pos):
        for cube in item.cubes:
            yield (pos[0] + cube[0], pos[1] + cube[1])
        
    def all_items(self):
        return self.items.values()
        
    def get_pos(self, item):
        for pos in self.items:  # inefficient but whatever
            if self.items[pos] is item:
                return pos
        return None
        

class InventoryState:
    def __init__(self):
        self.rows = 7
        self.cols = 9
        self.equip_grid = ItemGrid((5, 5))
        self.inv_grid = ItemGrid((self.cols, self.rows))
        
    def all_equipped_items(self):
        return self.equip_grid.all_items()


class PlayerStatType(Enum):
    HP = "HP",
    DPS = "DPS",
    MOVESPEED = "MOVE_SPEED",
    TICKS_PER_ATTACK = "TICKS_PER_ATTACK",
    ATTACK_RADIUS = "ATTACK_RADIUS",


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

        self.attack_tick = 0
        self.cur_attack_dur = 1
        
        self.delay_tick = 0
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
        
    def _can_begin_attack(self):
        return self.delay_tick <= 0 and self.attack_tick <= 0
        
    def _activate_attack(self, player_entity, world):
        pos = player_entity.center()
        circle = AttackCircleArt(*pos, 60)
        world.add(circle)
        att_range = self.stat_value(PlayerStatType.ATTACK_RADIUS)
        
        hit_enemies = world.entities_in_circle(pos, att_range)
        for e in hit_enemies:
            if e.is_enemy():
                e.state.deal_damage(15)
        
    def update(self, player_entity, world, gs, input_state):
        if player_entity is None:
            return
            
        if self.delay_tick > 0:
            self.delay_tick -= 1

        blocked = player_entity.inputs_blocked()
             
        if input_state.is_held(inputs.ATTACK) and self._can_begin_attack():
            self.cur_attack_dur = self.stat_value(PlayerStatType.TICKS_PER_ATTACK)
            self.attack_tick = self.cur_attack_dur
                
        elif self.attack_tick > 0:
            self.attack_tick -= 1
            if self.attack_tick <= 0:
                self._activate_attack(player_entity, world)
                
                self.attack_tick = 0
                self.cur_attack_dur = 1
                self.delay_tick = 12
        
        # you can keep moving during the attack windup    
        move_x = int(input_state.is_held(inputs.RIGHT)) - int(input_state.is_held(inputs.LEFT))
        move_y = int(input_state.is_held(inputs.DOWN)) - int(input_state.is_held(inputs.UP))
        
        self.is_moving = move_x != 0 or move_y != 0
        
        if move_x != 0 and move_y != 0:
            move_x /= 1.4142 
            move_y /= 1.4142   
        
        if self.delay_tick > 0:
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
        
    def attack_progress(self):
        if self.attack_tick <= 0:
            return -1
        else:
            return min(1.0, max(0.0, 1 - self.attack_tick / self.cur_attack_dur))
    
    def get_sprite(self, gs):
        if self.attack_tick > 0:
            progress = self.attack_progress()
            idx = int(progress * len(spriteref.player_attacks))
            return spriteref.player_attacks[idx]
        elif self.delay_tick > 0:
            return spriteref.player_squat   
        elif self.is_moving:
            return spriteref.player_move_all[gs.anim_tick % len(spriteref.player_move_all)]
        else:
            return spriteref.player_idle_all[(gs.anim_tick // 2) % len(spriteref.player_idle_all)] 
            
    def get_shadow_sprite(self):
        if self.attack_tick > 0:
            progress = self.attack_progress()
            if progress > 0.25 and progress < 0.75:
                return spriteref.small_shadow
        return spriteref.medium_shadow
        
        
        

