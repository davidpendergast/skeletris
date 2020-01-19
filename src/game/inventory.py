import collections


class ItemGridType:

    INVENTORY = "INVENTORY"
    EQUIPMENT = "EQUIPMENT"
    MISC = "MISC"


class ItemGrid:

    def __init__(self, size, grid_type=ItemGridType.MISC):
        self._size = size
        self.items = collections.OrderedDict()  # item -> pos: (int: x, int: y)
        self._grid_type = grid_type

        self._dirty = False
    
    def can_place(self, item, pos, allow_replace=False):
        if item in self.items:
            print("WARN: Attempting to place into a grid it's already inside? item={}".format(item))
            return False
        if (item.w() + pos[0] > self.w() or
                item.h() + pos[1] > self.h()):
            return False

        hit_item = None
        for cell in self._cells_occupied(item, pos):
            item_in_cell = self.item_at_position(cell)
            if item_in_cell is not None:
                if not allow_replace:
                    return False
                elif hit_item is None:
                    hit_item = item_in_cell
                elif hit_item is not item_in_cell:
                    return False  # overlapping two items
                
        return True

    def is_inventory(self):
        return self._grid_type == ItemGridType.INVENTORY

    def is_equipment(self):
        return self._grid_type == ItemGridType.EQUIPMENT

    def w(self):
        return self._size[0]

    def h(self):
        return self._size[1]

    def size(self):
        return self._size

    def __contains__(self, item):
        return item in self.items

    def is_dirty(self):
        return self._dirty

    def set_clean(self):
        self._dirty = False
        
    def place(self, item, pos):
        if self.can_place(item, pos, allow_replace=False):
            self.items[item] = pos
            self._dirty = True
            return True
        return False
            
    def try_to_replace(self, item, pos):
        if item.w() + pos[0] > self.w() or item.h() + pos[1] > self.h():
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

    def remove_all(self):
        res = []
        all_items = [item for item in self.items]
        for item in all_items:
            if self.remove(item):
                res.append(item)
        return res
        
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

    def search_for_valid_position_to_place(self, item):
        for y in range(0, self.h()):
            for x in range(0, self.w()):
                if self.can_place(item, (x, y), allow_replace=False):
                    return (x, y)
        return None
        

class InventoryState:

    def __init__(self):
        self.rows = 8
        self.cols = 9
        self.equip_grid = ItemGrid((5, 5), grid_type=ItemGridType.EQUIPMENT)
        self.inv_grid = ItemGrid((self.cols, self.rows), grid_type=ItemGridType.INVENTORY)

    def is_dirty(self):
        return self.equip_grid.is_dirty() or self.inv_grid.is_dirty()

    def set_clean(self):
        self.equip_grid.set_clean()
        self.inv_grid.set_clean()

    def get_equip_grid(self):
        return self.equip_grid

    def get_inv_grid(self):
        return self.inv_grid

    def all_equipped_items(self):
        return self.equip_grid.all_items()

    def all_inv_items(self):
        return self.inv_grid.all_items()

    def is_equipped(self, item):
        return item in self.equip_grid

    def is_in_inventory(self, item):
        return item in self.inv_grid

    def __contains__(self, item):
        return self.is_equipped(item) or self.is_in_inventory(item)

    def remove(self, item):
        if self.equip_grid.remove(item) or self.inv_grid.remove(item):
            return True
        return False

    def add_to_inv(self, item, pos=None):
        if pos is None:
            pos = self.inv_grid.search_for_valid_position_to_place(item)
            if pos is None:
                return False

        if self.inv_grid.place(item, pos):
            return True

        return False

    def add_to_equipment(self, item, pos=None):
        if pos is None:
            pos = self.equip_grid.search_for_valid_position_to_place(item)
            if pos is None:
                return False

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



        
        
        

