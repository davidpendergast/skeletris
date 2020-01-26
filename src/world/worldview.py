import math

import src.game.spriteref as spriteref
import src.renderengine.img as img
import src.game.globalstate as gs
from src.world.worldstate import World
from src.utils.util import Utils
from src.renderengine.engine import RenderEngine
import src.utils.colors as colors
import src.game.constants as constants


class WorldView:

    def __init__(self, world):
        self.world = world

        self._geo_bundle_lookup = {}  # x,y -> ImageBundle
        self._onscreen_geo_bundles = set()
        self._dirty_geo_bundles = []

        self._onscreen_entities = set()

        self._fade_overlay_bundle = None  # used to achieve a 'fade to black effect'

        # so that the in-game map gives the same-ish advantage as a big monitor
        self._max_render_range = (constants.MAP_DIMS[0] // 2, constants.MAP_DIMS[1] // 2)

    def update_geo_bundle(self, grid_x, grid_y):
        if not self.world.is_valid(grid_x, grid_y):
            return

        bundle = self.get_geo_bundle(grid_x, grid_y)
        sprite = self.calc_sprite_for_geo(grid_x, grid_y)  # this may be None

        if self.world.get_geo(grid_x, grid_y) not in (World.FLOOR, World.DOOR):
            color = self.world.get_geo_color()
        else:
            lighting = self.world.get_lighting(grid_x, grid_y)
            color = Utils.linear_interp(self.world.get_geo_color(), colors.WHITE, lighting)

        if bundle is not None:
            new_bun = bundle.update(new_model=sprite,
                                    new_x=grid_x * self.world.cellsize(),
                                    new_y=grid_y * self.world.cellsize(),
                                    new_scale=2,
                                    new_depth=10,
                                    new_color=color)
            self._geo_bundle_lookup[(grid_x, grid_y)] = new_bun
            self._dirty_geo_bundles.append((grid_x, grid_y))

    def calc_sprite_for_geo(self, grid_x, grid_y):
        geo = self.world.get_geo(grid_x, grid_y)

        if geo == World.WALL:
            def mapping(x): return 1 if x == World.WALL or x == World.DOOR else 0
            n_info = self.world.get_neighbor_info(grid_x, grid_y, mapping=mapping)
            mults = [1, 2, 4, 8, 16, 32, 64, 128]
            wall_img_id = sum(n_info[i] * mults[i] for i in range(0, 8))
            return spriteref.get_wall(wall_img_id, wall_type_id=self.world.wall_type_at((grid_x, grid_y)))

        elif geo == World.DOOR:
            return spriteref.floor_totally_dark

        elif geo == World.FLOOR or geo == World.HOLE:
            if self.world.get_hidden(grid_x, grid_y):
                return spriteref.floor_hidden
            else:
                def mapping(x): return 1 if x in (World.WALL, World.EMPTY, World.DOOR) else 0
                n_info = self.world.get_neighbor_info(grid_x, grid_y, mapping=mapping)

                encoding = 2 * n_info[0] + 4 * n_info[1] + 1 * n_info[7]
                lighting = self.world.get_lighting(grid_x, grid_y)
                floor_id = self.world.floor_type_at((grid_x, grid_y))
                return spriteref.get_floor(encoding, floor_type_id=floor_id, darkness_level=1-lighting)

        return None

    def get_geo_bundle(self, grid_x, grid_y, create_if_missing=True):
        key = (grid_x, grid_y)
        if key in self._geo_bundle_lookup:
            return self._geo_bundle_lookup[key]
        elif create_if_missing:
            geo = self.world.get_geo(grid_x, grid_y)
            if geo is World.WALL:
                layer = spriteref.WALL_LAYER
            else:
                layer = spriteref.FLOOR_LAYER

            self._geo_bundle_lookup[key] = img.ImageBundle(None, 0, 0, layer=layer)
            self.update_geo_bundle(grid_x, grid_y)
            return self._geo_bundle_lookup[key]
        else:
            return None

    def _get_cam_grid_center(self):
        cam_x, cam_y = gs.get_instance().get_actual_camera_xy()
        cam_w, cam_h = gs.get_instance().get_world_camera_size()
        p = self.world.get_player()
        if p is not None:
            return self.world.to_grid_coords(*p.center())
        else:
            cam_center = Utils.rect_center([cam_x, cam_y, cam_w, cam_h])
            return self.world.to_grid_coords(*cam_center)

    def _get_grid_rect_to_render(self):
        cam_x, cam_y = gs.get_instance().get_actual_camera_xy()
        cam_w, cam_h = gs.get_instance().get_world_camera_size()
        screen_grid_rect = [cam_x // self.world.cellsize(), cam_y // self.world.cellsize(),
                            cam_w // self.world.cellsize() + 2, cam_h // self.world.cellsize() + 2]

        max_grid_rect = self._get_max_grid_rect_to_render()

        return Utils.get_rect_intersect(screen_grid_rect, max_grid_rect)

    def _get_max_grid_rect_to_render(self):
        center_xy = self._get_cam_grid_center()
        return [center_xy[0] - self._max_render_range[0],
                center_xy[1] - self._max_render_range[1],
                1 + 2 * self._max_render_range[0],
                1 + 2 * self._max_render_range[1]]

    def _update_onscreen_tile_bundles(self):
        render_eng = RenderEngine.get_instance()

        grid_rect = self._get_grid_rect_to_render()

        old_onscreen_geo = self._onscreen_geo_bundles
        new_onscreen_geo = set()
        for x in range(grid_rect[0], grid_rect[0] + grid_rect[2]):
            for y in range(grid_rect[1], grid_rect[1] + grid_rect[3]):
                bun_key = (x, y)

                if bun_key in old_onscreen_geo:
                    old_onscreen_geo.remove(bun_key)

                bun = self.get_geo_bundle(*bun_key, create_if_missing=False)

                if bun is None and self.world.get_geo(x, y) != World.EMPTY:
                    bun = self.get_geo_bundle(*bun_key, create_if_missing=True)

                if bun is not None:
                    new_onscreen_geo.add(bun_key)
                    if bun_key not in self._onscreen_geo_bundles or bun_key in self._dirty_geo_bundles:
                        render_eng.update(bun)

        # clear out the bundles that aren't onscreen anymore
        for bun_key in old_onscreen_geo:
            expired_bun = self.get_geo_bundle(*bun_key, create_if_missing=False)
            if expired_bun is not None:
                render_eng.remove(expired_bun)
                if bun_key in self._geo_bundle_lookup:
                    del self._geo_bundle_lookup[bun_key]

        self._onscreen_geo_bundles = new_onscreen_geo

    def _calc_new_camera_center(self):
        p = self.world.get_player()
        if p is None:
            return None

        unmodified_xy = p.center()
        new_xys = []

        p_pos = self.world.to_grid_coords(*p.center())
        for mod in self.world.get_camera_modifiers(p_pos):
            new_xy = mod.modify_camera_center(self.world, unmodified_xy)
            if new_xy is not None:
                new_xys.append(new_xy)

        if len(new_xys) == 0:
            return unmodified_xy
        else:
            avg_xy = Utils.average(new_xys)
            return Utils.round(avg_xy)

    def cleanup_active_bundles(self):
        render_eng = RenderEngine.get_instance()
        for e in self._onscreen_entities:
            for bun in e.all_bundles():
                render_eng.remove(bun)
        self._onscreen_entities.clear()

        for bun_key in self._onscreen_geo_bundles:
            render_eng.remove(self._geo_bundle_lookup[bun_key])
        self._geo_bundle_lookup.clear()
        self._onscreen_geo_bundles.clear()

        if self._fade_overlay_bundle is not None:
            render_eng.remove(self._fade_overlay_bundle)
            self._fade_overlay_bundle = None

    def _update_fade_overlay(self):
        fade_state = gs.get_instance().get_fade_overlay_state()
        if fade_state is None or fade_state[1] == 0:
            if self._fade_overlay_bundle is not None:
                RenderEngine.get_instance().remove(self._fade_overlay_bundle)
                self._fade_overlay_bundle = None
        else:
            if self._fade_overlay_bundle is None:
                self._fade_overlay_bundle = img.ImageBundle.new_bundle(spriteref.UI_0_LAYER,
                                                                       scale=1, depth=-float('inf'))
            color, alpha = fade_state
            sprite = spriteref.get_floor_lighting(1-alpha)
            scr_size = RenderEngine.get_instance().get_game_size()
            ratio = (int(0.5 + scr_size[0] / sprite.width()), int(0.5 + scr_size[1] / sprite.height()))

            self._fade_overlay_bundle = self._fade_overlay_bundle.update(new_model=sprite, new_x=0, new_y=0,
                                                                         new_ratio=ratio, new_color=color)
            RenderEngine.get_instance().update(self._fade_overlay_bundle)

    def update_all(self):
        cam_center = gs.get_instance().get_camera_center_in_world()
        cam_rect = gs.get_instance().get_world_camera_rect(fudge=int(self.world.cellsize() * 1.5))

        max_render_rect = self._get_max_grid_rect_to_render()

        new_onscreens = set()
        for e in self.world.visible_entities(cam_rect, onscreen=True):
            e_grid_xy = self.world.to_grid_coords(*e.center())
            if Utils.rect_contains(max_render_rect, e_grid_xy):
                new_onscreens.add(e)
                if e in self._onscreen_entities:
                    self._onscreen_entities.remove(e)

        render_eng = RenderEngine.get_instance()

        for leftover_e in self._onscreen_entities:
            leftover_e.cleanup()
        self._onscreen_entities = new_onscreens

        if self.world._needs_full_geo_rebuild:
            self._geo_bundle_lookup.clear()
        else:
            for dirty_xy in self.world._dirty_geo:
                self.update_geo_bundle(dirty_xy[0], dirty_xy[1])
        self.world._needs_full_geo_rebuild = False
        self.world._dirty_geo.clear()

        for e in self._onscreen_entities:
            for bun in e.all_bundles():
                render_eng.update(bun)

        new_cam_center = self._calc_new_camera_center()

        if new_cam_center is not None:
            dist = Utils.dist(cam_center, new_cam_center)
            min_speed = 10
            max_speed = 20
            if dist > 400 or dist <= min_speed:
                gs.get_instance().set_camera_center_in_world(*new_cam_center)
            else:
                speed = min_speed + (max_speed - min_speed) * math.sqrt(dist / 200)
                move_xy = Utils.set_length(Utils.sub(new_cam_center, cam_center), speed)
                new_pos = Utils.add(cam_center, move_xy)
                gs.get_instance().set_camera_center_in_world(*Utils.round(new_pos))

        self._update_onscreen_tile_bundles()
        self._update_fade_overlay()
