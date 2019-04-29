import math

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.globalstate as gs

CELLSIZE = 64


class World:
    EMPTY = 0
    WALL = 1
    DOOR = 2
    FLOOR = 3
    HOLE = 4
    
    SOLIDS = [WALL, DOOR, HOLE, EMPTY]
    
    def __init__(self, width, height):
        self._size = (width, height)
        self._level_geo = []
        self._level_lighting = []  # 0.0 = totally dark, 1.0 = fully lit
        self._hidden = []

        self._cached_light_sources = set()  # used to track changes in lighting between updates

        self._bg_color = (92, 92, 92)

        # tells the WorldView to update the bundles at these coords
        self._dirty_geo = set()
        # self._dirty_lighting = set()

        for _ in range(0, width):
            self._level_geo.append([World.EMPTY] * height)
            self._level_lighting.append([0.0] * height)
            self._hidden.append([False] * height)

        self.entities = []
        self._ents_to_remove = []
        self._ents_to_add = []
        self._onscreen_entities = set()

        self._wall_type = spriteref.WALL_NORMAL_ID
        self._floor_type = spriteref.FLOOR_NORMAL_ID

        self._wall_art_overrides = {}  # x,y -> wall_type_id
        self._floor_art_overrides = {}  # x,y -> floor_type_id

    def cellsize(self):
        return CELLSIZE
        
    def add(self, entity, gridcell=None):
        """
            gridcell: (grid_x, grid_y) or None
        """
        if entity is None:
            raise ValueError("tried to add None to world.")

        if gridcell is not None:
            x = gridcell[0] * self.cellsize() + (self.cellsize() - entity.w()) // 2
            y = gridcell[1] * self.cellsize() + (self.cellsize() - entity.h()) // 2
            entity.set_x(x)
            entity.set_y(y)

        self._ents_to_add.append(entity)

    def add_item_as_entity(self, item, pos, direction=None):
        if item is None:
            return
        else:
            import src.world.entities as entities
            if direction is not None:
                vel = entities.PickupEntity.rand_vel(speed=None, direction=direction)
            else:
                vel = (0, 1)

            self.add(entities.ItemEntity(item, pos[0], pos[1], vel=vel))

    def show_floating_text(self, text, color, scale, entity):
        import src.world.entities as entities
        import random  # just chill, it's fine
        x_offs = int(15 * (0.5 - random.random()))
        text = entities.FloatingTextEntity(text, 25, color, anchor=None, scale=scale,
                                  start_offs=(x_offs, -64), end_offs=(x_offs, -96))
        text.set_x(entity.center()[0] - text.w() // 2)
        text.set_y(entity.center()[1] - text.h() // 2)
        self.add(text)
        
    def remove(self, entity):
        self._ents_to_remove.append(entity)

    def __contains__(self, entity):
        return entity in self.entities
        
    def get_player(self):
        for e in self.entities:
            if e.is_player():
                return e
        return None

    def get_npc(self, npc_id):
        for e in self.entities:
            if e.is_npc() and e.get_id() == npc_id:
                return e
        return None
    
    def entities_in_circle(self, center, radius, onscreen=True, cond=None):
        """
            returns: list of entities in circle, sorted by distance from center 
        """
        r2 = radius*radius
        res = []
        search_space = self._onscreen_entities if onscreen else self.entities
        for e in search_space:
            if cond is None or cond(e):
                e_c = e.center()
                dx = e_c[0] - center[0]
                dy = e_c[1] - center[1]
                if dx*dx + dy*dy <= r2:
                    res.append(e)
        
        res.sort(key=lambda e: Utils.dist(center, e.center()))
        
        return res

    def get_entity(self, uid, onscreen=True):
        if onscreen:
            for e in self._onscreen_entities:
                if e.get_uid() == uid:
                    return e
        else:
            for e in self.entities:
                if e.get_uid() == uid:
                    return e
        return None

    def all_entities(self, onscreen=False):
        if onscreen:
            for e in self._onscreen_entities:
                yield e
        else:
            for e in self.entities:
                yield e

    def get_light_sources(self, onscreen=True):
        """returns: set of (grid_x, grid_y, int: light_range)"""
        search_domain = self._onscreen_entities if onscreen else self.entities
        res = set()
        for e in search_domain:
            if e.get_light_level() > 0:
                xy = self.to_grid_coords(e.center()[0], e.center()[1])
                res.add((xy[0], xy[1], e.get_light_level()))

        return res

    def visible_entities(self, cam_center):
        for e in self.all_entities(onscreen=True):
            on_camera = Utils.dist(e.center(), cam_center) <= 800

            if on_camera and e.is_visible_in_world(self):
                yield e

    def set_wall_type(self, wall_id, xy=None):
        old_type = self.wall_type_at(xy)
        if xy is None:
            self._wall_type = wall_id
        elif wall_id is None:
            if xy in self._wall_art_overrides:
                del self._wall_art_overrides[xy]
        else:
            self._wall_art_overrides[xy] = wall_id
        if old_type != wall_id:

            self._dirty_geo.add(xy)

    def wall_type_at(self, grid_xy):
        if grid_xy in self._wall_art_overrides:
            return self._wall_art_overrides[grid_xy]
        else:
            return self._wall_type

    def set_floor_type(self, floor_id, xy=None):
        old_type = self.floor_type_at(xy)
        if xy is None:
            self._floor_type = floor_id
        elif floor_id is None:
            if xy in self._floor_art_overrides:
                del self._floor_art_overrides[xy]
        else:
            self._floor_art_overrides[xy] = floor_id

        if old_type != floor_id:
            self._dirty_geo.add(xy)

    def floor_type_at(self, grid_xy):
        if grid_xy in self._floor_art_overrides:
            return self._floor_art_overrides[grid_xy]
        elif self.get_geo(*grid_xy) == World.HOLE:
            return spriteref.FLOOR_HOLE_ID
        else:
            return self._floor_type

    def set_geo(self, grid_x, grid_y, geo_id):
        if self.is_valid(grid_x, grid_y):
            old_geo_id = self._level_geo[grid_x][grid_y]
            self._level_geo[grid_x][grid_y] = geo_id

            if old_geo_id != geo_id:
                self._dirty_geo.add((grid_x, grid_y))
                for n in World.ALL_NEIGHBORS:
                    self._dirty_geo.add((grid_x + n[0], grid_y + n[1]))

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

    def door_opened(self, grid_x, grid_y):
        for n in World.NEIGHBORS:
            self.set_hidden(grid_x + n[0], grid_y + n[1], False, and_fill_adj_floors=True)

    def get_hidden_at(self, pixel_x, pixel_y):
        return self.get_hidden(*self.to_grid_coords(pixel_x, pixel_y))

    def get_hidden(self, grid_x, grid_y):
        if self.is_valid(grid_x, grid_y):
            return self._hidden[grid_x][grid_y]
        else:
            return False

    def get_lighting(self, grid_x, grid_y):
        if not self.is_valid(grid_x, grid_y):
            return 0.0
        else:
            return self._level_lighting[grid_x][grid_y]

    def _set_lighting(self, grid_x, grid_y, val):
        if val < 0 or val > 1:
            raise ValueError("light value out of range: {}".format(val))

        if not self.is_valid(grid_x, grid_y):
            return
        elif self._level_lighting[grid_x][grid_y] == val:
            return
        elif self.get_geo(grid_x, grid_y) in (World.FLOOR, World.DOOR):
            self._dirty_geo.add((grid_x, grid_y))
            self._level_lighting[grid_x][grid_y] = val

    def _recalc_lighting(self, old_lighting, new_lighting):
        """
        :param old_lighting: set of (grid_x, grid_y, int: light range)
        :param new_lighting: set of (grid_x, grid_y, int: light range)
        """

        deleted = []
        for src in old_lighting:
            if src not in new_lighting:
                deleted.append(src)

        for d_src in deleted:
            grid_x = d_src[0]
            grid_y = d_src[1]
            dist = d_src[2]

            for x in range(grid_x - dist, grid_x + dist + 1):
                for y in range(grid_y - dist, grid_y + dist + 1):
                    self._set_lighting(x, y, 0.0)

        if len(deleted) == 0:
            to_add = []
            for src in new_lighting:
                if src not in old_lighting:
                    to_add.append(src)
        else:
            to_add = new_lighting

        for src in to_add:
            grid_x = src[0]
            grid_y = src[1]
            max_dist = src[2]
            for x in range(grid_x - max_dist, grid_x + max_dist + 1):
                for y in range(grid_y - max_dist, grid_y + max_dist + 1):
                    xy_dist = Utils.dist((x, y), (grid_x, grid_y))
                    if xy_dist <= max_dist:
                        mult = Utils.bound((max_dist / 6) ** (2 / 3), 0, 1)
                        level = mult * (1 - (xy_dist / max_dist)**1.5)
                        if level > self.get_lighting(x, y):
                            self._set_lighting(x, y, level)

    def set_bg_color(self, color):
        self._bg_color = color

    def get_bg_color(self):
        return self._bg_color

    def set_hidden(self, grid_x, grid_y, val, and_fill_adj_floors=True):
        if self.get_geo(grid_x, grid_y) == World.FLOOR and self._hidden[grid_x][grid_y] != val:
            self._hidden[grid_x][grid_y] = val
            self._dirty_geo.add((grid_x, grid_y))

            if and_fill_adj_floors:
                for n in World.NEIGHBORS:
                    self.set_hidden(grid_x + n[0], grid_y + n[1], val, and_fill_adj_floors=True)

    def hide_all_floors(self):
        for x in range(0, self.size()[0]):
            for y in range(0, self.size()[1]):
                if self.get_geo(x, y) == World.FLOOR:
                    self.set_hidden(x, y, True, and_fill_adj_floors=False)

    def is_solid_at(self, pixel_x, pixel_y):
        geo = self.get_geo_at(pixel_x, pixel_y)
        return geo in World.SOLIDS

    def is_solid(self, grid_x, grid_y):
        geo = self.get_geo(grid_x, grid_y)
        return geo in World.SOLIDS

    def get_actor_in_cell(self, grid_x, grid_y):
        """returns: an ActorState, if there's an actor entity in the specified cell"""
        for e in self.entities:
            if e.is_actor():
                grid_pos = self.to_grid_coords(e.center()[0], e.center()[1])
                if grid_x == grid_pos[0] and grid_y == grid_pos[1]:
                    return e
        return None

    def get_actors(self):
        res = []
        for e in self.entities:
            if e.is_actor():
                res.append(e)
        res.sort(key=lambda a: a.get_uid())
        return res
            
    def is_valid(self, grid_x, grid_y):
        return 0 <= grid_x < self.size()[0] and 0 <= grid_y < self.size()[1]

    def size(self):
        return self._size

    NEIGHBORS = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    ALL_NEIGHBORS = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
    
    def get_neighbor_info(self, grid_x, grid_y, mapping=lambda x: x):
        return [mapping(self.get_geo(grid_x + offs[0], grid_y + offs[1])) for offs in World.ALL_NEIGHBORS]

    def flush_new_entity_additions(self):
        for e in self._ents_to_add:
            self.entities.append(e)
            e._alive = True
        self._ents_to_add.clear()

    def update_all(self, input_state, render_engine):
        old_lighting = self._cached_light_sources

        self.flush_new_entity_additions()

        for e in self._ents_to_remove:
            print("cleaning up {}".format([x for x in e.all_bundles()]))
            e.cleanup(render_engine)
            self.entities.remove(e)  # n^2 but whatever
            e._alive = False
            if e in self._onscreen_entities:
                self._onscreen_entities.remove(e)

        self._ents_to_remove.clear()

        cam_center = gs.get_instance().get_world_camera(center=True)

        an_actor_is_acting = False
        actors_to_process = []

        player = self.get_player()

        for e in self.entities:
            on_camera = Utils.dist(e.center(), cam_center) <= 600
            near_player = player is not None and Utils.dist(e.center(), player.center()) <= 600

            if on_camera or near_player:
                e.update(self, input_state, render_engine)
                self._onscreen_entities.add(e)

                if e.is_actor() and not e.get_actor_state().is_alive():
                    e.get_actor_state().handle_death(self, e)

                elif e.is_actor() and near_player:
                    actors_to_process.append(e)
                    if e.is_performing_action():
                        an_actor_is_acting = True

            elif e in self._onscreen_entities:
                self._onscreen_entities.remove(e)

        if not an_actor_is_acting:
            # process the actors that have waited longest first
            actors_to_process.sort(key=lambda a: a.get_actor_state().last_turn_tick())

            for actor in actors_to_process:
                a_state = actor.get_actor_state()
                if a_state.energy() < a_state.max_energy():
                    a_state.set_energy(a_state.energy() + 1)
                    a_state.update_last_turn_tick()
                else:
                    not_visible = not actor.is_visible_in_world(self)
                    actor.choose_next_action(self, input_state, and_finalize=not_visible)
                    break

        new_lighting = self.get_light_sources(onscreen=False)

        if old_lighting != new_lighting:
            self._recalc_lighting(old_lighting, new_lighting)
            self._cached_light_sources = new_lighting



