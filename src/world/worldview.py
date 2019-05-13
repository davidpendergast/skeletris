import math

import src.game.spriteref as spriteref
import src.renderengine.img as img
import src.game.globalstate as gs
from src.world.worldstate import World
from src.utils.util import Utils
from src.renderengine.engine import RenderEngine


class WorldView:

    def __init__(self, world):
        self.world = world

        self._geo_bundle_lookup = {}  # x,y -> ImageBundle
        self._onscreen_geo_bundles = set()
        self._dirty_geo_bundles = []

        self._onscreen_entities = set()

    def update_geo_bundle(self, grid_x, grid_y):
        if not self.world.is_valid(grid_x, grid_y):
            return

        bundle = self.get_geo_bundle(grid_x, grid_y)
        sprite = self.calc_sprite_for_geo(grid_x, grid_y)  # this may be None
        if bundle is not None:
            new_bun = bundle.update(new_model=sprite,
                                    new_x=grid_x*self.world.cellsize(),
                                    new_y=grid_y*self.world.cellsize(),
                                    new_scale=4, new_depth=10)
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

    def _update_onscreen_tile_bundles(self):
        px, py = gs.get_instance().get_world_camera()
        pw, ph = gs.get_instance().get_world_camera_size()
        grid_rect = [px // self.world.cellsize(), py // self.world.cellsize(),
                     pw // self.world.cellsize() + 3, ph // self.world.cellsize() + 3]

        render_eng = RenderEngine.get_instance()

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

    def update_all(self, input_state):
        cam_center = gs.get_instance().get_world_camera(center=True)

        new_onscreens = set()
        for e in self.world.visible_entities(cam_center):
            new_onscreens.add(e)
            if e in self._onscreen_entities:
                self._onscreen_entities.remove(e)

        render_eng = RenderEngine.get_instance()

        for leftover_e in self._onscreen_entities:
            leftover_e.cleanup()
        self._onscreen_entities = new_onscreens

        for dirty_xy in self.world._dirty_geo:
            self.update_geo_bundle(dirty_xy[0], dirty_xy[1])
        self.world._dirty_geo.clear()

        for e in self._onscreen_entities:
            for bun in e.all_bundles():
                render_eng.update(bun)

        p = self.world.get_player()
        if p is not None:
            dist = Utils.dist(cam_center, p.center())
            min_speed = 10
            max_speed = 20
            if dist > 200 or dist <= min_speed:
                gs.get_instance().set_world_camera_center(*p.center())
            else:
                speed = min_speed + (max_speed - min_speed) * math.sqrt(dist / 200)
                move_xy = Utils.set_length(Utils.sub(p.center(), cam_center), speed)
                new_pos = Utils.add(cam_center, move_xy)
                gs.get_instance().set_world_camera_center(*Utils.round(new_pos))

        self._update_onscreen_tile_bundles()