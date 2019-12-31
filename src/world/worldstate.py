import random

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.utils.colors as colors
import src.game.globalstate as gs
import src.game.constants as constants

CELLSIZE = constants.CELLSIZE  # it's 32


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
        self._needs_full_geo_rebuild = False

        for _ in range(0, width):
            self._level_geo.append([World.EMPTY] * height)
            self._level_lighting.append([0.0] * height)
            self._hidden.append([False] * height)

        self.entities = []
        self._ents_to_remove = set()
        self._ents_to_add = []
        self._onscreen_entities = set()

        # actors within this x, y range from player will act
        self._entity_act_range = (9, 8)

        self._camera_modifiers = []

        self._wall_type = spriteref.WALL_NORMAL_ID
        self._floor_type = spriteref.FLOOR_NORMAL_ID

        self._wall_art_overrides = {}  # x,y -> wall_type_id
        self._floor_art_overrides = {}  # x,y -> floor_type_id
        self._geo_color = colors.WHITE

    def cellsize(self):
        return CELLSIZE

    def cell_center(self, grid_x, grid_y):
        return (int(CELLSIZE * (grid_x + 0.5)),
                int(CELLSIZE * (grid_y + 0.5)))
        
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
        import src.world.entities as entities  # just chill, it's fine
        cx = entity.center()[0]
        cy = entity.center()[1]
        x_render_offs = int(15 * (0.5 - random.random()))
        text = entities.FloatingTextEntity(cx, cy, text, 25, color, anchor=None, scale=scale,
                                           start_offs=(x_render_offs, -16),
                                           end_offs=(x_render_offs, -32))
        self.add(text)

    def show_explosion(self, cx, cy, duration, color=None, offs=(0, 0), scale=2):
        import src.world.entities as entities
        splosion = entities.AnimationEntity(cx, cy, spriteref.Animations.explosions, duration, spriteref.ENTITY_LAYER, scale=scale)
        if color is not None:
            splosion.set_color(color)
        splosion.set_sprite_offset(offs)
        self.add(splosion)

    def show_effect_circle(self, cx, cy, art_type, height=constants.CELLSIZE, color=None, duration=45):
        if art_type is None:
            return
        else:
            if color is None:
                color = colors.WHITE
            from src.world.entities import EffectCircleArt
            circle = EffectCircleArt(cx, cy, height, duration, art_type=art_type, color=color)
            self.add(circle)
        
    def remove(self, entity):
        if entity not in self._ents_to_remove:
            self._ents_to_remove.add(entity)

            for ent_uid in entity.get_dependent_entity_uids():
                if ent_uid is not None:
                    dep_ent = self.get_entity(ent_uid, onscreen=False)
                    if dep_ent is not None:
                        self.remove(dep_ent)

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

    def get_entity_for_mouseover(self, xy, visible_only=True, cond=None):
        hover_rad = constants.CELLSIZE // 2
        hover_over = self.entities_in_circle(xy, hover_rad)
        if visible_only:
            hover_over = list(filter(lambda ent: ent.is_visible_in_world(self), hover_over))
        if cond is not None:
            hover_over = list(filter(cond, hover_over))
        if len(hover_over) > 0:
            return hover_over[0]
        else:
            return None

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

    def add_camera_modifier(self, modifier):
        self._camera_modifiers.append(modifier)

    def get_camera_modifiers(self, grid_xy):
        for cm in self._camera_modifiers:
            if grid_xy in cm:
                yield cm

    def visible_entities(self, camera_rect, onscreen=True):
        for e in self.all_entities(onscreen=onscreen):
            on_camera = Utils.rect_contains(camera_rect, e.center())

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
        elif self.get_geo(grid_xy[0], grid_xy[1]) == World.HOLE:
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

    def get_decoration_type(self, grid_x, grid_y):
        if self.is_valid(grid_x, grid_y):
            ents = self.get_entities_in_cell(grid_x, grid_y, cond=lambda e: e.is_decoration())
            if len(ents) == 0:
                return None
            else:
                return ents[0].get_dec_type()

    def get_visible(self, grid_x, grid_y):
        return not self.get_hidden(grid_x, grid_y) and self.get_lighting(grid_x, grid_y) > 0

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

            processed = set()
            q = [(grid_x, grid_y)]
            processed.add(q[0])
            rect = [grid_x - max_dist,
                    grid_y - max_dist,
                    2 * max_dist + 1,
                    2 * max_dist + 1]

            while len(q) > 0:
                x, y = q.pop()

                xy_dist = Utils.dist((x, y), (grid_x, grid_y))
                if xy_dist <= max_dist:
                    mult = Utils.bound((max_dist / 6) ** (2 / 3), 0, 1)
                    level = mult * (1 - (xy_dist / max_dist) ** 1.5)
                    if level > self.get_lighting(x, y):
                        self._set_lighting(x, y, level)

                    # it's sometimes expected to have light sources embedded inside solid blocks
                    # (like when the player is walking through a door that's opening...)
                    if (x, y) != (grid_x, grid_y) and self.is_solid(x, y):
                        continue

                    for n in Utils.neighbors(x, y):
                        if n not in processed:
                            if rect[0] <= n[0] < rect[0] + rect[2] and rect[1] <= n[1] < rect[1] + rect[3]:
                                processed.add(n)
                                q.append(n)

    def set_bg_color(self, color):
        self._bg_color = color

    def get_bg_color(self):
        return self._bg_color

    def get_geo_color(self):
        return self._geo_color

    def set_geo_color(self, color):
        if self._geo_color != color:
            self._needs_full_geo_rebuild = True
            self._geo_color = color

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

    def is_solid_at(self, pixel_x, pixel_y, including_entities=False):
        grid_xy = self.to_grid_coords(pixel_x, pixel_y)
        return self.is_solid(grid_xy[0], grid_xy[1], including_entities=including_entities)

    def is_solid(self, grid_x, grid_y, including_entities=False):
        geo = self.get_geo(grid_x, grid_y)
        if geo in World.SOLIDS:
            return True

        if including_entities:
            if len(self.get_entities_in_cell(grid_x, grid_y, cond=lambda e: e.is_solid(self))) > 0:
                return True

        return False

    def get_actor_in_cell(self, grid_x, grid_y):
        """returns: an ActorEntity, if there's an actor entity in the specified cell"""
        for e in self.entities:
            if e.is_actor():
                grid_pos = self.to_grid_coords(e.center()[0], e.center()[1])
                if grid_x == grid_pos[0] and grid_y == grid_pos[1]:
                    return e
        return None

    def get_door_in_cell(self, grid_x, grid_y):
        doors = self.get_entities_in_cell(grid_x, grid_y, cond=lambda e: e.is_door())
        if len(doors) == 0:
            return None
        else:
            if len(doors) > 1:
                print("WARN: multiple doors in cell ({}, {}): {}".format(grid_x, grid_y, doors))
            return doors[0]

    def get_interactable_in_cell(self, grid_x, grid_y):
        ents = self.get_entities_in_cell(grid_x, grid_y, cond=lambda e: e.is_interactable(self))
        if len(ents) == 0:
            return None
        else:
            if len(ents) > 1:
                print("WARN: multiple interactables in cell ({}, {}): {}".format(grid_x, grid_y, ents))
            return ents[0]

    def get_entities_in_cell(self, grid_x, grid_y, cond=None):
        res = []
        for e in self.entities:
            if cond is None or cond(e):
                grid_pos = self.to_grid_coords(e.center()[0], e.center()[1])
                if grid_x == grid_pos[0] and grid_y == grid_pos[1]:
                    res.append(e)
        return res

    def get_map_text_for_cells(self, grid_rect, ignore_visiblity=False):
        from src.ui.ui import TextBuilder, TextImage
        res = TextBuilder()

        corners = [(grid_rect[0], grid_rect[1]),
                   (grid_rect[0] + grid_rect[2] - 1, grid_rect[1]),
                   (grid_rect[0], grid_rect[1] + grid_rect[3] - 1),
                   (grid_rect[0] + grid_rect[2] - 1, grid_rect[1] + grid_rect[3] - 1)]

        ent_coords = {}

        for e in self.all_entities(onscreen=(not ignore_visiblity)):
            e_pos = self.to_grid_coords(*e.center())
            if Utils.rect_contains(grid_rect, e_pos) and (ignore_visiblity or e.is_visible_in_world(self)):
                identifier = e.get_map_identifier()
                if identifier is not None:
                    ent_coords[e_pos] = identifier

        for y in range(grid_rect[1], grid_rect[1] + grid_rect[3]):
            for x in range(grid_rect[0], grid_rect[0] + grid_rect[2]):
                did_add = False
                if (x, y) in ent_coords:
                    char, color = ent_coords[(x, y)]
                    res.add(char, color=color)
                    did_add = True

                if not did_add and self.get_geo(x, y) == World.FLOOR:
                    if not self.get_hidden(x, y):
                        if self.get_lighting(x, y) > 0:
                            res.add(".", color=colors.LIGHT_GRAY)
                        else:
                            res.add(".", color=colors.DARK_GRAY)
                        did_add = True

                if not did_add and self.get_geo(x, y) in (World.WALL, World.DOOR):
                    touching_non_hidden = False
                    for n in Utils.neighbors(x, y, and_diags=True):
                        if self.get_geo(*n) == World.FLOOR and not self.get_hidden(*n):
                            touching_non_hidden = True
                            break
                    if touching_non_hidden or ignore_visiblity:
                        if self.get_geo(x, y) == World.WALL:
                            res.add("X", color=colors.DARK_GRAY)
                        else:
                            res.add("0", color=colors.BLUE)
                        did_add = True

                if not did_add:
                    if (x, y) in corners:
                        res.add(".", color=colors.BLACK)
                    else:
                        res.add(TextImage.INVISIBLE_CHAR)

            res.add_line("")

        return res

    def get_path_between(self, p1, p2, max_length=-1, cond=None):
        if p1 == p2:
            if cond is None or cond(p1):
                return [p1]
            else:
                return None

        if -1 < max_length < Utils.dist_manhattan(p1, p2):
            return None

        # it's just djikstra's
        dists = {p1: 0}        # pos -> dist
        backrefs = {p1: None}  # pos -> pos

        q = [p1]
        while len(q) > 0:
            cur = q.pop(0)  # O(n) but i ~don't~ care

            n_dist = dists[cur] + 1
            if n_dist > max_length > -1:
                continue

            neighbors = list(Utils.neighbors(cur[0], cur[1]))
            random.shuffle(neighbors)

            for n in neighbors:
                if n in dists:
                    continue
                dists[n] = n_dist
                if self.is_valid(*n) and (cond is None or cond(n)):
                    backrefs[n] = cur
                    q.append(n)

            if p2 in backrefs:
                break

        if p2 in backrefs:
            res = [p2]  # building the list in reverse
            temp = backrefs[p2]
            while temp is not None:
                res.append(temp)
                temp = backrefs[temp]
            res.reverse()
            return res
        else:
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

    def update_all(self):
        old_lighting = self._cached_light_sources

        self.flush_new_entity_additions()

        for e in self._ents_to_remove:
            e.cleanup()
            self.entities.remove(e)  # n^2 but whatever
            e._alive = False
            if e in self._onscreen_entities:
                self._onscreen_entities.remove(e)

        self._ents_to_remove.clear()

        cam_rect = gs.get_instance().get_world_camera_rect(fudge=int(self.cellsize() * 1.5))

        an_actor_is_acting = False
        actors_to_process = []

        player = self.get_player()

        if player is not None:
            player_xy = self.to_grid_coords(*player.center())
        else:
            player_xy = self.to_grid_coords(*Utils.rect_center(cam_rect))

        for e in self.entities:
            on_camera = Utils.rect_contains(cam_rect, e.center())

            e_xy = self.to_grid_coords(*e.center())
            in_x_range = abs(e_xy[0] - player_xy[0]) <= self._entity_act_range[0]
            in_y_range = abs(e_xy[1] - player_xy[1]) <= self._entity_act_range[1]

            should_act_if_actor = in_x_range and in_y_range

            if on_camera or should_act_if_actor:
                e.update(self)
                self._onscreen_entities.add(e)

                if not gs.get_instance().world_updates_paused():
                    if e.is_actor() and not e.get_actor_state().is_alive():
                        e.handle_death(self)
                        if e.is_player():
                            gs.get_instance().set_player_turn_to_act(False)

                    elif e.is_actor() and should_act_if_actor:
                        actors_to_process.append(e)
                        if e.is_performing_action():
                            an_actor_is_acting = True
                            gs.get_instance().set_player_turn_to_act(e.is_player())

            elif e in self._onscreen_entities:
                self._onscreen_entities.remove(e)

        if not gs.get_instance().world_updates_paused() and not an_actor_is_acting:
            actors_to_process.sort(key=lambda a: -1 if a.is_player() else a.get_uid())
            actors_ready_to_act = [a for a in actors_to_process if a.get_actor_state().ready_to_act()]

            while len(actors_ready_to_act) == 0 and len(actors_to_process) > 0:
                for i in range(0, len(actors_to_process)):
                    actor = actors_to_process[i]
                    a_state = actor.get_actor_state()

                    if a_state.energy() + a_state.speed() >= a_state.max_energy():
                        a_state.set_ready_to_act(True)
                        actors_ready_to_act.append(actor)

                    a_state.set_energy((a_state.energy() + a_state.speed()) % a_state.max_energy())

            for actor in actors_ready_to_act:
                # if a different actor added a new solid entity this frame as part of its action,
                # need to make sure it's flushed before any other actors choose their actions.
                self.flush_new_entity_additions()

                a_state = actor.get_actor_state()
                action = actor.get_controller().get_actual_next_action(actor, self)

                if actor.is_player():
                    gs.get_instance().set_player_turn_to_act(True)

                if actor.is_player() and action.is_skip_turn_action() and action.is_intentional():
                    gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.TURNS_SKIPPED_COUNT)

                if action.is_free():
                    action.pre_start(self)
                    action.start(self)
                    action.finalize(self)
                    break
                else:
                    a_state.set_ready_to_act(False)

                    dur_modifier = a_state.turn_duration_modifier(action.get_type())
                    dur = Utils.bound(int(action.get_duration() * dur_modifier), 1, None)
                    actor.set_and_start_action(action, dur, self)

                    if actor.is_player():
                        gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.TURN_COUNT)

                not_visible = not actor.is_visible_in_world(self)
                action_pos = action.get_position()
                if not_visible and (action_pos is None or not self.get_visible(*action_pos)):
                    # this actor is hidden by darkness, need to instantly update them
                    # and importantly, keep updating other actors on the same tick.
                    # otherwise the game will pause for several ticks when enemies are
                    # in darkness, basically telling the player they're there
                    actor.update_action(self, force_finalize=True)
                else:
                    break

        new_lighting = self.get_light_sources(onscreen=False)

        if old_lighting != new_lighting:
            self._recalc_lighting(old_lighting, new_lighting)
            self._cached_light_sources = new_lighting





