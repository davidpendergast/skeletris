import renderengine.img as img   
import spriteref


class World:

    EMPTY = 0
    WALL = 1
    DOOR = 2
    FLOOR = 3 
    
    def __init__(self, width, height):
        self._size = (width, height)
        self._level_geo = []
        for _ in range(0, width):
            self._level_geo.append([World.EMPTY] * height)
        self._geo_bundle_lookup = {} # x,y -> bundle id
            
        self.entities = []
        
    def set_geo(self, grid_x, grid_y, geo_id):
        if self.is_valid(grid_x, grid_y):
            self._level_geo[grid_x][grid_y] = geo_id
        elif geo_id != World.EMPTY:
            raise ValueError("Cannot set out of bounds grid cell to " + 
                    "non-empty: ({}, {}) <- {}".format(grid_x, grid_y, geo_id))
        
    def get_geo(self, grid_x, grid_y):
        if self.is_valid(grid_x, grid_y):
            return self._level_geo[grid_x][grid_y]
        else:
            return 
            
    def is_valid(self, grid_x, grid_y):
        return (grid_x >= 0 and grid_x < self.size()[0] 
                and grid_y >= 0 and grid_y < self.size()[1])
        
    def size(self):
        return self._size
        
    NEIGHBORS = [(-1,-1), (0, -1), (1, -1), (1, 0), 
                 (1, 1), (0, 1), (-1, 1), (-1, 0)]
    
    def get_neighbor_info(self, grid_x, grid_y, mapping=lambda x: x):
        return [mapping(self.get_geo(grid_x + offs[0], grid_y + offs[1])) for offs in World.NEIGHBORS]
    
    def get_geo_bundle(self, grid_x, grid_y):
        key = (grid_x, grid_y)
        if key in self._geo_bundle_lookup:
            return self._geo_bundle_lookup[key] 
        else:
            geo = self.get_geo(grid_x, grid_y)
            model = None
            
            if geo == World.WALL:
                n_info = self.get_neighbor_info(grid_x, grid_y, 
                        mapping=lambda x: 1 if x == World.WALL or x == World.DOOR else 0)
                mults = [1, 2, 4, 8, 16, 32, 64, 128]
                wall_img_id = sum(n_info[i] * mults[i] for i in range(0, 8))
                model = spriteref.walls[wall_img_id]
                
            elif geo == World.FLOOR:
                n_info = self.get_neighbor_info(grid_x, grid_y, 
                        mapping=lambda x: 1 if x == World.WALL or x == World.EMPTY else 0)
                floor_img_id = n_info[0] + 2*n_info[1] + 4*n_info[7]
                model = spriteref.floors[floor_img_id]
            
            if model is not None:
                return img.ImageBundle(model, grid_x*32, grid_y*32, absolute=False, scale=2)
            else:
                return None
                
    
    def get_all_bundles(self):
        res = []
        for x in range(0, self.size()[0]):
            for y in range(0, self.size()[1]):
                bun = self.get_geo_bundle(x, y)
                if bun is not None:
                    res.append(bun)
                    
        return res
                
                
                
