

class ItemGrid:
    def __init__(self, size):
        self.size = size
        self.place_order = []
        self.items = {}  # coords -> item
    
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
            self.place_order.append(item)
            return True
        return False

    def to_map(self):
        """
        returns: (int, int) -> Item
        """
        res = {}
        res.update(self.items)
        return res
            
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
                self.place_order.remove(item)
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
        return list(self.place_order)
        
    def get_pos(self, item):
        for pos in self.items:  # inefficient but whatever
            if self.items[pos] is item:
                return pos
        return None
        

class InventoryState:

    def __init__(self):
        self.rows = 8
        self.cols = 9
        self.equip_grid = ItemGrid((5, 5))
        self.inv_grid = ItemGrid((self.cols, self.rows))

    def all_equipped_items(self):
        return self.equip_grid.all_items()

    def all_inv_items(self):
        return self.inv_grid.all_items()

    def is_equipped(self, item):
        for i in self.all_equipped_items():
            if i == item:
                return True
        return False

    def add_to_inv(self, item, pos=(0, 0)):
        return self.inv_grid.place(item, pos)

    def add_to_equipment(self, item, pos=(0, 0)):
        return self.equip_grid.place(item, pos)

    def all_items(self):
        res = []
        for i in self.all_equipped_items():
            res.append(i)
        for i in self.all_inv_items():
            res.append(i)
        return res

    def to_json(self):
        return {}

    @staticmethod
    def from_json(json_blob):
        return InventoryState()


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



        
        
        

