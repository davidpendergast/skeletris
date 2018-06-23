import random

import src.renderengine.img as img
import src.game.spriteref as spriteref
from src.utils.util import Utils


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
        self._geo_bundle_lookup = {}  # x,y -> bundle id
        self._dirty_bundles = []
            
        self.entities = []
        self._ents_to_remove = []
        
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
        
    def remove(self, entity):
        self._ents_to_remove.append(entity)
        
    def get_player(self):
        for e in self.entities:
            if e.is_player():
                return e
        return None
    
    def entities_in_circle(self, center, radius):
        """
            returns: list of entities in circle, sorted by distance from center 
        """
        r2 = radius*radius
        res = []
        for e in self.entities:
            e_c = e.center()
            dx = e_c[0] - center[0]
            dy = e_c[1] - center[1]
            if dx*dx + dy*dy <= r2:
                res.append(e)
        
        res.sort(key=lambda e: Utils.dist(center, e.center()))
        
        return res       
        
    def set_geo(self, grid_x, grid_y, geo_id):
        if self.is_valid(grid_x, grid_y):
            self._level_geo[grid_x][grid_y] = geo_id
        elif geo_id != World.EMPTY:
            raise ValueError("Cannot set out of bounds grid cell to " + 
                    "non-empty: ({}, {}) <- {}".format(grid_x, grid_y, geo_id))

    def to_grid_coords(self, pixel_x, pixel_y):
        return (pixel_x // CELLSIZE, pixel_y // CELLSIZE)

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
        return 0 <= grid_x < self.size()[0] and 0 <= grid_y < self.size()[1]
        
    def size(self):
        return self._size
        
    NEIGHBORS = [(-1, -1), (0, -1), (1, -1), (1, 0),
                 (1, 1), (0, 1), (-1, 1), (-1, 0)]
    
    def get_neighbor_info(self, grid_x, grid_y, mapping=lambda x: x):
        return [mapping(self.get_geo(grid_x + offs[0], grid_y + offs[1])) for offs in World.NEIGHBORS]

    def update_geo_bundle(self, grid_x, grid_y, and_neighbors=False):
        if not self.is_valid(grid_x, grid_y):
            return

        bundle = self.get_geo_bundle(grid_x, grid_y)
        sprite = self.calc_sprite_for_geo(grid_x, grid_y)
        if bundle is not None:
            if sprite is not None:
                new_bun = bundle.update(new_model=sprite)
                if new_bun is not bundle:
                    self._dirty_bundles.append(new_bun)

        if and_neighbors:
            for n in World.NEIGHBORS:
                self.update_geo_bundle(grid_x + n[0], grid_y + n[1], and_neighbors=False)

    def calc_sprite_for_geo(self, grid_x, grid_y):
        geo = self.get_geo(grid_x, grid_y)

        if geo == World.WALL:
            n_info = self.get_neighbor_info(grid_x, grid_y,
                                            mapping=lambda x: 1 if x == World.WALL or x == World.DOOR else 0)
            mults = [1, 2, 4, 8, 16, 32, 64, 128]
            wall_img_id = sum(n_info[i] * mults[i] for i in range(0, 8))
            return spriteref.walls[wall_img_id]

        elif geo == World.FLOOR or geo == World.DOOR:
            n_info = self.get_neighbor_info(grid_x, grid_y,
                                            mapping=lambda x: 1 if x == World.WALL or x == World.EMPTY else 0)
            floor_img_id = 2 * n_info[0] + 4 * n_info[1] + 1 * n_info[7]
            return spriteref.floors[floor_img_id]

        return None

    def get_geo_bundle(self, grid_x, grid_y):
        key = (grid_x, grid_y)
        if key in self._geo_bundle_lookup:
            return self._geo_bundle_lookup[key] 
        else:
            sprite = self.calc_sprite_for_geo(grid_x, grid_y)

            if sprite is not None:
                return img.ImageBundle(sprite, grid_x*CELLSIZE, grid_y*CELLSIZE,
                        scale=int(CELLSIZE/sprite.w), depth=10)
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
        for e in self._ents_to_remove:
            self.entities.remove(e) # n^2 but whatever
            e.cleanup(gs, render_engine)
        self._ents_to_remove.clear()
            
        for e in self.entities:
            e.update(self, gs, input_state, render_engine)

        for bun in self._dirty_bundles:
            render_engine.update(bun, layer_id=gs.WALL_LAYER)
        
        p = self.get_player()
        if p is not None:
            # raw center for scrolling smoothness
            gs.set_world_camera_center(*p.center())
                
                
                
