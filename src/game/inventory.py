from enum import Enum

from src.items.item import StatType


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
    TICKS_PER_ATTACK = "TICKS_PER_ATTACK"

class PlayerState:
    def __init__(self, name, inventory):
        self._name = name
        self._inventory = inventory
        self._level = 0
        self._base_values = {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10,
            PlayerStatType.TICKS_PER_ATTACK: 50
        }
    
    def name(self):
        return self._name
    
    def level(self):
        return self._level
        
    def inventory(self):
        return self._inventory
        
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
        
     
     
     
     
     
