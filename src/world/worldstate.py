import src.renderengine.img as img   
import src.game.spriteref as spriteref


CELLSIZE = 64

class World:

    EMPTY = 0
    WALL = 1
    DOOR = 2
    FLOOR = 3 
    
    SOLIDS = [WALL, DOOR]
    
    def __init__(self, width, height):
        self._size = (width, height)
        self._level_geo = []
        for _ in range(0, width):
            self._level_geo.append([World.EMPTY] * height)
        self._geo_bundle_lookup = {} # x,y -> bundle id
            
        self.entities = []
        
    def cellsize(self):
        return CELLSIZE
        
    def add(self, entity, gridcell=None):
        """
            gridcell: (grid_x, grid_y) or None
        """
        if gridcell is not None:
            x = gridcell[0] * self.cellsize() + (self.cellsize() - entity.w()) // 2
            y = gridcell[1] * self.cellsize() + (self.cellsize() - entity.h()) // 2
            entity.set_x(x)
            entity.set_y(y)
            
        self.entities.append(entity)
        
    def get_player(self):
        for e in self.entities:
            if e.is_player():
                return e
        return None
    
    def entities_in_circle(self, center, radius):
        r2 = radius*radius
        res = []
        for e in self.entities:
            e_c = e.center()
            dx = e_c[0] - center[0]
            dy = e_c[1] - center[1]
            if dx*dx + dy*dy <= r2:
                res.append(e)
        return res       
        
    def set_geo(self, grid_x, grid_y, geo_id, quietly=False):
        if self.is_valid(grid_x, grid_y):
            self._level_geo[grid_x][grid_y] = geo_id
        elif geo_id != World.EMPTY:
            raise ValueError("Cannot set out of bounds grid cell to " + 
                    "non-empty: ({}, {}) <- {}".format(grid_x, grid_y, geo_id))
        
    def get_geo(self, grid_x, grid_y):
        if self.is_valid(grid_x, grid_y):
            return self._level_geo[grid_x][grid_y]
        else:
            return World.EMPTY
            
    def get_geo_at(self, pixel_x, pixel_y):
        return self.get_geo(pixel_x // self.cellsize(), pixel_y // self.cellsize())
        
    def is_solid_at(self, pixel_x, pixel_y):
        geo = self.get_geo_at(pixel_x, pixel_y)
        return geo in World.SOLIDS
            
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
                floor_img_id = 2*n_info[0] + 4*n_info[1] + 1*n_info[7]
                model = spriteref.floors[floor_img_id]
            
            if model is not None:
                return img.ImageBundle(model, grid_x*CELLSIZE, grid_y*CELLSIZE, 
                        scale=int(CELLSIZE/model.w), depth=10)
            else:
                return None
                
    
    def get_all_bundles(self, geo_id):
        res = []
        for x in range(0, self.size()[0]):
            for y in range(0, self.size()[1]):
                if self.get_geo(x, y) == geo_id:
                    bun = self.get_geo_bundle(x, y)
                    if bun is not None:
                        res.append(bun)
                    
        return res
      
              
    def update_all(self, gs, input_state, render_engine):
        for e in self.entities:
            e.update(self, gs, input_state, render_engine)
        
        p = self.get_player()
        if p is not None:
            for w_layer in gs.world_layers:
                p_center = p.raw_center() # use float-valued center for smoothness
                offs_x = -(p_center[0] - gs.screen_size[0] // 2)
                offs_y = -(p_center[1] - gs.screen_size[1] // 2)
                
                render_engine.set_layer_offset(w_layer, offs_x, offs_y)
                
                
                
