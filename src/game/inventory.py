import collections


class ItemGrid:

    def __init__(self, size):
        self.size = size
        self.items = collections.OrderedDict()  # item -> pos: (int: x, int: y)

        self._dirty = False
    
    def can_place(self, item, pos):
        if item in self.items:
            print("WARN: Attempting to place into a grid it's already inside? item={}".format(item))
            return False
        if (item.w() + pos[0] > self.size[0] or 
                item.h() + pos[1] > self.size[1]):
            return False
            
        for cell in self._cells_occupied(item, pos):
            if self.item_at_position(cell) is not None:
                return False
                
        return True

    def is_dirty(self):
        return self._dirty

    def set_clean(self):
        self._dirty = False
        
    def place(self, item, pos):
        if self.can_place(item, pos):
            self.items[item] = pos
            self._dirty = True
            return True
        return False
            
    def try_to_replace(self, item, pos):
        if item.w() + pos[0] > self.size[0] or item.h() + pos[1] > self.size[1]:
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
        if item in self.items:
            del self.items[item]
            self._dirty = True
            return True
        return False
        
    def item_at_position(self, pos):
        for item in self.items:
            origin = self.items[item]
            for cell in self._cells_occupied(item, origin):
                if cell == pos:
                    return item
        return None
        
    def _cells_occupied(self, item, pos):
        for cube in item.cubes:
            yield (pos[0] + cube[0], pos[1] + cube[1])
        
    def all_items(self):
        for item in self.items:
            yield item
        
    def get_pos(self, item):
        if item in self.items:
            return self.items[item]
        else:
            return None
        

class InventoryState:

    def __init__(self):
        self.rows = 8
        self.cols = 9
        self.equip_grid = ItemGrid((5, 5))
        self.inv_grid = ItemGrid((self.cols, self.rows))

    def is_dirty(self):
        return self.equip_grid.is_dirty() or self.inv_grid.is_dirty()

    def set_clean(self):
        self.equip_grid.set_clean()
        self.inv_grid.set_clean()

    def all_equipped_items(self):
        return self.equip_grid.all_items()

    def all_inv_items(self):
        return self.inv_grid.all_items()

    def is_equipped(self, item):
        return self.equip_grid.get_pos(item) is not None

    def is_in_inventory(self, item):
        return self.inv_grid.get_pos(item) is not None

    def __contains__(self, item):
        return self.is_equipped(item) or self.is_in_inventory(item)

    def remove(self, item):
        if self.equip_grid.remove(item) or self.inv_grid.remove(item):
            return True
        return False

    def add_to_inv(self, item, pos=(0, 0)):
        if self.inv_grid.place(item, pos):
            return True
        return False
    def add_to_equipment(self, item, pos=(0, 0)):

        if self.equip_grid.place(item, pos):
            return True
        return False

    def all_items(self):
        res = []
        for i in self.all_equipped_items():
            res.append(i)
        for i in self.all_inv_items():
            res.append(i)
        return res


class FakeInventoryState(InventoryState):

    def __init__(self):
        InventoryState.__init__(self)  # TODO - make an actual superclass
        self.equipped_items = []
        self.inv_items = []

    def all_equipped_items(self):
        return list(self.equipped_items)

    def all_inv_items(self):
        return list(self.inv_items)

    def add_to_equipment(self, item, pos=(0, 0)):
        self.equipped_items.append(item)

    def add_to_inv(self, item, pos=(0, 0)):
        self.inv_items.append(item)

    def is_equipped(self, item):
        return item in self.equipped_items

    def is_in_inventory(self, item):
        return item in self.inv_items



        
        
        

