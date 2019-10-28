import random
import pygame
import traceback

from src.world.worldstate import World
from src.worldgen.worldgen import WorldFactory, WorldBlueprint, RoomFactory, BuilderUtils
from src.utils.util import Utils
import src.world.entities as entities
import src.game.enemies as enemies
import src.game.spriteref as spriteref
import src.game.events as events
import src.game.dialog as dialog
import src.game.music as music
import src.game.cinematics as cinematics
import src.game.globalstate as gs
from src.worldgen import worldgen2
import src.game.npc as npc
import src.game.decoration as decoration
import src.utils.colors as colors
import src.game.debug as debug

_FIRST_ZONE_ID = None
_ZONE_TRANSITIONS = {}
_ALL_ZONES = {}

_STORYLINE_ZONES = []

_LOOT_ZONES = []

# used by zones that "end" the game when they're completed.
_END_OF_GAME_ZONE_ID = "END_GAME"


def first_zone_id():
    return _FIRST_ZONE_ID


def first_zone():
    return get_zone(_FIRST_ZONE_ID)


def all_zone_ids():
    return [z for z in _ALL_ZONES]


def get_zone(zone_id):
    return _ALL_ZONES[zone_id]


def all_storyline_zone_ids():
    return [z for z in _STORYLINE_ZONES]


def all_loot_zone_ids():
    return [z for z in _LOOT_ZONES]


def all_handbuilt_zone_ids():
    loot_zones = set()
    for l in all_loot_zone_ids():
        loot_zones.add(l)

    return [z for z in _ALL_ZONES if (z not in loot_zones and get_zone(z).get_file() is not None)]


def next_storyline_zone(current_id):
    if current_id not in _STORYLINE_ZONES:
        print("WARN: {} isn't a storyline zone, so there's no 'next' storyline zone")
        return None
    else:
        idx = _STORYLINE_ZONES.index(current_id)
        if idx + 1 < len(_STORYLINE_ZONES):
            return _STORYLINE_ZONES[idx + 1]
        else:
            # we hit the end
            return _END_OF_GAME_ZONE_ID


def init_zones():
    _ALL_ZONES.clear()
    for zone_cls in Zone.__subclasses__():
        zone_instance = zone_cls()
        zone_instance.zone_id = zone_cls.ZONE_ID
        make(zone_instance)

    story_zones = []
    story_zones.append(ZoneBuilder.make_generated_zone(0, "Caves I", "caves_1", dims=(3, 1)))
    story_zones.append(ZoneBuilder.make_generated_zone(1, "Caves II", "caves_2", dims=(4, 1)))
    story_zones.append(ZoneBuilder.make_generated_zone(2, "Caves III", "caves_3", dims=(3, 2)))
    story_zones.append(get_zone(TombTownZone.ZONE_ID))

    story_zones.append(ZoneBuilder.make_generated_zone(4, "Swamps I", "swamps_1", geo_color=colors.LIGHT_GREEN))
    story_zones.append(ZoneBuilder.make_generated_zone(5, "Swamps II", "swamps_2", geo_color=colors.LIGHT_GREEN))
    story_zones.append(ZoneBuilder.make_generated_zone(6, "Swamps III", "swamps_3", geo_color=colors.LIGHT_GREEN))
    story_zones.append(get_zone(FrogLairZone.ZONE_ID))

    story_zones.append(ZoneBuilder.make_generated_zone(8, "City I", "city_1", geo_color=colors.LIGHT_BLUE))
    story_zones.append(ZoneBuilder.make_generated_zone(9, "City II", "city_2", geo_color=colors.LIGHT_BLUE))
    story_zones.append(ZoneBuilder.make_generated_zone(10, "City III", "city_3", geo_color=colors.LIGHT_BLUE))
    story_zones.append(get_zone(RoboLairZone.ZONE_ID))

    red_color = get_zone(CaveHorrorZone.ZONE_ID).get_color()
    story_zones.append(ZoneBuilder.make_generated_zone(12, "Rotten Core I", "rotten_core_1", geo_color=red_color))
    story_zones.append(ZoneBuilder.make_generated_zone(13, "Rotten Core II", "rotten_core_2", geo_color=red_color))
    story_zones.append(ZoneBuilder.make_generated_zone(14, "Rotten Core III", "rotten_core_3", geo_color=red_color))
    story_zones.append(get_zone(CaveHorrorZone.ZONE_ID))
    story_zones.append(get_zone(NamelessLairZone.ZONE_ID))

    _STORYLINE_ZONES.clear()

    for z in story_zones:
        if z.get_id() not in _ALL_ZONES:
            _ALL_ZONES[z.get_id()] = z
        _STORYLINE_ZONES.append(z.get_id())

    global _FIRST_ZONE_ID
    _FIRST_ZONE_ID = _STORYLINE_ZONES[0]

    loot_zones = []
    for i in range(0, 16):
        loot_zones.append(LootZoneBuilder.make_generated_zone(i))

    _LOOT_ZONES.clear()
    for z in loot_zones:
        if z.get_id() not in _ALL_ZONES:
            _ALL_ZONES[z.get_id()] = z
        _LOOT_ZONES.append(z.get_id())


class ZoneLoader:
    EMPTY = (92, 92, 92)
    WALL = (0, 0, 0)
    WALL_CRACKED = (30, 30, 30)

    FLOOR = (255, 255, 255)
    FLOOR_CRACKED = (225, 225, 225)
    FLOOR_FANCY = (205, 205, 205)
    FLOOR_SWAMP = (185, 185, 185)
    FLOOR_ID_LOOKUP = {FLOOR: spriteref.FLOOR_NORMAL_ID,
                       FLOOR_CRACKED: spriteref.FLOOR_CRACKED_ID,
                       FLOOR_FANCY: spriteref.FLOOR_FANCY_ID,
                       FLOOR_SWAMP: spriteref.FLOOR_SWAMP_ID}
    HOLE = (100, 100, 100)

    DOOR = (0, 0, 255)
    SENSOR_DOOR = (100, 100, 255)
    PLAYER_SPAWN = (0, 255, 0)
    MONSTER_SPAWN = (255, 255, 0)
    RARE_MONSTER_SPAWN = (200, 200, 0)
    CHEST_SPAWN = (255, 0, 255)
    SAVE_STATION = (0, 255, 255)

    EXIT = (255, 0, 0)
    RETURN_EXIT = (255, 50, 50)

    @staticmethod
    def load_blueprint_from_file(zone_id, filename, level):
        """
        returns: (BluePrint bp, dict: color -> list of (int x, int y))
        """
        try:
            filepath = "assets/zones/" + filename
            raw_img = pygame.image.load(Utils.resource_path(filepath))
            img_size = (raw_img.get_width(), raw_img.get_height())
            bp = WorldBlueprint(img_size, level)

            exit_id = next_storyline_zone(zone_id)  # will be None if this isn't a storyline zone

            unknowns = {}

            for x in range(0, img_size[0]):
                for y in range(0, img_size[1]):
                    color = raw_img.get_at((x, y))
                    color = (color[0], color[1], color[2])

                    if color == ZoneLoader.EMPTY:
                        continue
                    elif color == ZoneLoader.WALL:
                        bp.set(x, y, World.WALL)
                    elif color == ZoneLoader.WALL_CRACKED:
                        bp.set(x, y, World.WALL)
                        bp.set_alt_art(x, y, spriteref.WALL_CRACKED_ID)
                    elif color == ZoneLoader.FLOOR:
                        bp.set(x, y, World.FLOOR)
                    elif color in ZoneLoader.FLOOR_ID_LOOKUP:
                        bp.set(x, y, World.FLOOR)
                        bp.set_alt_art(x, y, ZoneLoader.FLOOR_ID_LOOKUP[color])
                    elif color == ZoneLoader.HOLE:
                        bp.set(x, y, World.HOLE)
                    elif color == ZoneLoader.DOOR:
                        bp.set(x, y, World.DOOR)
                    elif color == ZoneLoader.SENSOR_DOOR:
                        bp.set_sensor_door(x, y)
                    elif color == ZoneLoader.RETURN_EXIT:
                        bp.set(x, y, World.FLOOR)
                        bp.return_exit_spawns.append((x, y))
                    elif color == ZoneLoader.EXIT:
                        bp.set(x, y, World.FLOOR)
                        if exit_id == _END_OF_GAME_ZONE_ID:
                            bp.end_of_game_spawns.append((x, y))
                        elif exit_id in _ALL_ZONES:
                            if _ALL_ZONES[exit_id].is_boss_zone():
                                bp.boss_exit_spawns[exit_id] = (x, y)
                            else:
                                bp.exit_spawns[exit_id] = (x, y)
                        else:
                            print("WARN: no exit zone for {} at ({}, {})".format(zone_id, x, y))
                    elif color == ZoneLoader.CHEST_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.chest_spawns.append((x, y))
                    elif color == ZoneLoader.MONSTER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.enemy_spawns.append((x, y))
                    elif color == ZoneLoader.RARE_MONSTER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.rare_enemy_spawns.append((x, y))
                    elif color == ZoneLoader.PLAYER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.player_spawn = (x, y)
                    elif color == ZoneLoader.SAVE_STATION:
                        bp.set(x, y, World.FLOOR)
                        bp.save_station = (x, y)
                    else:
                        mock_color = (color[0], color[0], color[0])
                        if mock_color in ZoneLoader.FLOOR_ID_LOOKUP:
                            bp.set(x, y, World.FLOOR)
                            bp.set_alt_art(x, y, ZoneLoader.FLOOR_ID_LOOKUP[mock_color])
                        elif color[0] == ZoneLoader.WALL[0]:
                            bp.set(x, y, World.WALL)

                        pos = (x, y)
                        if color in unknowns:
                            unknowns[color].append(pos)
                        else:
                            unknowns[color] = [pos]

            return bp, unknowns

        except ValueError as e:
            print("failed to load " + str(filename))
            raise e


def build_world(zone_id, spawn_at_door_with_zone_id=None):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))

    zone = _ALL_ZONES[zone_id]
    gs.get_instance().prepare_for_new_zone(zone)
    music.play_song(zone.get_music_id())

    from src.game.tutorial import TutorialFactory
    tutorials = TutorialFactory.get_tutorials_for_level(zone.get_level(), non_complete_only=True)
    gs.get_instance().set_inactive_tutorials(tutorials)
    gs.get_instance().set_active_tutorial(None)

    w = zone.build_world()
    w.set_geo_color(zone.get_color())
    w.flush_new_entity_additions()
    w.set_bg_color(zone.get_bg_color())

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        spawn_at_entity = None

        if spawn_at_door_with_zone_id is not None:
            for e in w.all_entities(onscreen=False):
                if e.is_exit() and e.get_zone() == spawn_at_door_with_zone_id:
                    e.set_open(True)
                    spawn_at_entity = e

        if spawn_at_entity is not None:
            grid_xy = w.to_grid_coords(*spawn_at_entity.center())
            size = w.cellsize()
            p.set_center((grid_xy[0] + 0.5) * size, (grid_xy[1] + 0.5) * size)

        grid_xy = w.to_grid_coords(*p.center())
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)
        gs.get_instance().set_camera_center_in_world(*p.center())

    return w


def get_zone_name(zone_id):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))
    return _ALL_ZONES[zone_id].get_name()


def make(zone):
    _ALL_ZONES[zone.get_id()] = zone


class Zone:

    def __init__(self, name, level, filename=None, bg_color=None):
        self.name = name
        self.zone_id = None  # gets set by init_zones()
        self.bg_color = bg_color if bg_color is not None else colors.BLACK
        self.level = level
        self.blueprint_file = filename
        self.music_id = music.Songs.SILENCE
        self.geo_color = colors.WHITE

    def get_name(self):
        return self.name

    def get_file(self):
        return self.blueprint_file

    def get_color(self):
        return self.geo_color

    def get_id(self):
        return self.zone_id

    def get_level(self):
        return self.level

    def get_bg_color(self):
        return self.bg_color

    def get_music_id(self):
        return self.music_id

    def build_world(self):
        pass

    def is_boss_zone(self):
        return False

    def get_enemies(self):
        """List of templates of enemies that can (randomly) spawn here."""
        return []


class TestZone(Zone):

    ZONE_ID = "test_zone"

    def __init__(self):
        Zone.__init__(self, "Test Zone", 5)

    def build_world(self):
        w = WorldFactory.gen_world_from_rooms(self.get_level(), num_rooms=5).build_world()

        decs = [
            (spriteref.wall_decoration_mushrooms[0], ["it's a large cluster of mushrooms.",
                                                      "normally this species would be edible, but these ones have overgrown."]),
            (spriteref.wall_decoration_mushrooms[1], ["it's a large cluster of mushrooms.",
                                                      "normally this species would be edible, but these ones have overgrown."]),
            (spriteref.wall_decoration_mushrooms[2], ["it's a large cluster of mushrooms.",
                                                      "normally this species would be edible, but these ones have overgrown."]),
            (spriteref.wall_decoration_bucket, "it's a bucket. there are small pieces of mushrooms inside."),
            (spriteref.wall_decoration_plant_1, "it's a small fern inside a pot."),
            (spriteref.wall_decoration_rake, "it's a rake."),
            (spriteref.wall_decoration_sign, "the sign says:\n\"Mary Skelly's Mushroom's -- DON'T TOUCH\"")
        ]

        for grid_x in range(0, w.size()[0]):
            for grid_y in range(0, w.size()[1]):
                geo = w.get_geo(grid_x, grid_y)
                geo_above = w.get_geo(grid_x, grid_y - 1)
                if geo_above == World.WALL and geo == World.FLOOR and random.random() < 0.6:
                    sprite_to_use, text_to_use = random.choice(decs)

                    decor = entities.DecorationEntity.wall_decoration(sprite_to_use, grid_x, grid_y,
                                                                      interact_dialog=dialog.PlayerDialog(text_to_use))
                    w.add(decor)

        # just for debugging

        p = w.get_player()

        return w


class ZoneBuilder:

    @staticmethod
    def _add_entities_for_tile(zone_id, level, x, y, tile_type, world):
        if tile_type == worldgen2.TileType.PLAYER:
            world.add(entities.Player(0, 0), gridcell=(x, y))
        elif tile_type == worldgen2.TileType.CHEST:
            # TODO - we probably want to generate the loot here
            world.add(entities.ChestEntity(x, y))
        elif tile_type == worldgen2.TileType.MONSTER:
            e = enemies.EnemyFactory.gen_enemy(None, level)
            world.add(e, gridcell=(x, y))
        elif tile_type == worldgen2.TileType.DOOR:
            world.add(entities.DoorEntity(x, y))
        elif tile_type == worldgen2.TileType.ENTRANCE:
            world.add(entities.ReturnExitEntity(x, y, None))
        elif tile_type == worldgen2.TileType.EXIT:
            next_zone_id = next_storyline_zone(zone_id)
            if next_zone_id == _END_OF_GAME_ZONE_ID:
                world.add(entities.EndGameExitEnitity(x, y))
            else:
                actual_zone = get_zone(next_zone_id)
                if actual_zone is not None:
                    if actual_zone.is_boss_zone():
                        world.add(entities.BossExitEntity(x, y, next_zone_id))
                    else:
                        world.add(entities.ExitEntity(x, y, next_zone_id))
                else:
                    print("ERROR: invalid next zone \"{}\"".format(next_zone_id))
        elif tile_type == worldgen2.TileType.NPC:
            print("WARN: attempted to add an NPC using add_entities_for_tile")
            pass
        elif tile_type == worldgen2.TileType.STRAY_ITEM:
            pass
        elif tile_type == worldgen2.TileType.DECORATION:
            dec_ent = decoration.DecorationFactory.get_decoration(level)
            world.add(dec_ent, gridcell=(x, y-1))
        elif tile_type == worldgen2.TileType.SIGN:
            sign_ent = decoration.DecorationFactory.get_sign(level)
            world.add(sign_ent, gridcell=(x, y-1))

    @staticmethod
    def _tile_grid_to_world(zone_id, level, t_grid):
        w = t_grid.w()
        h = t_grid.h()
        world = World(t_grid.w(), t_grid.h())

        convo_npc_coords = []
        trade_npc_coords = []

        for x in range(0, w):
            for y in range(0, h):
                tile_type = t_grid.get(x, y)
                if tile_type == worldgen2.TileType.EMPTY:
                    world.set_geo(x, y, World.EMPTY)
                elif tile_type == worldgen2.TileType.WALL:
                    world.set_geo(x, y, World.WALL)
                elif tile_type == worldgen2.TileType.DOOR:
                    world.set_geo(x, y, World.DOOR)
                else:
                    world.set_geo(x, y, World.FLOOR)
                    if random.random() < 0.25:
                        world.set_floor_type(spriteref.FLOOR_CRACKED_ID, xy=(x, y))

                if tile_type == worldgen2.TileType.NPC:
                    convo_npc_coords.append((x, y))
                elif tile_type == worldgen2.TileType.TRADE_NPC:
                    trade_npc_coords.append((x, y))
                else:
                    ZoneBuilder._add_entities_for_tile(zone_id, level, x, y, tile_type, world)

        if len(convo_npc_coords) > 0 or len(trade_npc_coords) > 0:
            convo_npc_ents, trade_npc_ents = npc.NpcFactory.get_npcs(level, len(convo_npc_coords), len(trade_npc_coords))
            random.shuffle(convo_npc_coords)
            for i in range(0, len(convo_npc_ents)):
                world.add(convo_npc_ents[i], gridcell=convo_npc_coords[i])

            random.shuffle(trade_npc_coords)
            for i in range(0, len(trade_npc_ents)):
                world.add(trade_npc_ents[i], gridcell=trade_npc_coords[i])

        return world

    @staticmethod
    def generate_tile_grid(level, dims=(3, 3), num_tries=100):
        for i in range(0, num_tries):
            try:
                res = ZoneBuilder.generate_tile_grid_dangerously(level, dims=dims)

                # looks like we did it
                if res is not None:
                    return res
                else:
                    raise ValueError("got a null level...? level={}, dims={}".format(level, dims))

            except ValueError as e:
                print("WARN: failed to generate tile grid {} time(s): level={}, dims={}".format(i+1, level, dims))
                if debug.is_debug():
                    # y'all better fix this
                    raise e
                else:
                    traceback.print_exc()

        raise ValueError("failed to generate level={} with dims={} " +
                         "after {} tries, crashing...".format(level, dims, num_tries))

    @staticmethod
    def generate_tile_grid_dangerously(level, dims=(3, 3)):
        """dangerously = nonzero chance of failing to generate a valid level, and throwing an exception."""
        if dims[0] < 1 or dims[1] < 1 or dims[0] + dims[1] < 3:
            raise ValueError("dims are too small: ({}, {})".format(dims[0], dims[1]))

        start = (0, 0)
        end = (dims[0] - 1, dims[1] - 1)
        t_size = 12
        path, p_grid = worldgen2.GridBuilder.random_partition_grid(dims[0], dims[1],
                                                                   start=start, end=end, fully_connected=True)

        t_grid = worldgen2.TileGrid(dims[0], dims[1], tile_size=(t_size, t_size))

        room_map = {}  # (grid_x, grid_y) -> list of room_rects
        empty_rooms = []

        for x in range(0, dims[0]):
            for y in range(0, dims[1]):
                part = p_grid.get(x, y)
                if part is not None:
                    tile = worldgen2.Tile(t_size + 1, door_len=1, door_offs=3)
                    rooms_in_tile = worldgen2.TileFiller.basic_room_fill(tile, part, disjoint_rooms=True,
                                                                         connected_rooms=True)
                    rooms = [[x * t_size + r[0], y * t_size + r[1], r[2], r[3]] for r in rooms_in_tile]

                    if len(rooms) > 0:
                        room_map[(x, y)] = rooms
                        empty_rooms.extend(rooms)

                    t_grid.set_tile(x, y, tile)

        worldgen2.TileGridBuilder.clean_up_dangly_bits(t_grid)
        worldgen2.TileGridBuilder.clean_up_doors(t_grid)
        worldgen2.TileGridBuilder.add_walls(t_grid)
        worldgen2.TileGridBuilder.fill_empty_islands_with_walls(t_grid)

        if len(empty_rooms) <= 2:
            raise ValueError("no rooms..? n={}".format(len(empty_rooms)))

        start_placed = False
        for p in path:
            rooms_in_p = list(room_map.get(p))
            random.shuffle(rooms_in_p)
            for r in rooms_in_p:
                if r not in empty_rooms:
                    continue
                if worldgen2.FeatureUtils.try_to_place_feature_into_rect(worldgen2.Features.START, t_grid, r):
                    start_placed = True
                    empty_rooms.remove(r)
                    break
            if start_placed:
                break

        if not start_placed:
            for p in path:
                rooms_in_p = list(room_map.get(p))
                random.shuffle(rooms_in_p)
                for r in rooms_in_p:
                    if r not in empty_rooms:
                        continue
                    if worldgen2.FeatureUtils.try_to_place_feature_into_rect(worldgen2.Features.BACKUP_START, t_grid, r):
                        start_placed = True
                        empty_rooms.remove(r)
                        break
                if start_placed:
                    break

            if not start_placed:
                raise ValueError("failed to place start (or backup start) anywhere on path...")

        end_placed = False
        for p in reversed(path):
            rooms_in_p = list(room_map.get(p))
            random.shuffle(rooms_in_p)
            for r in rooms_in_p:
                if r not in empty_rooms:
                    continue
                if worldgen2.FeatureUtils.try_to_place_feature_into_rect(worldgen2.Features.EXIT, t_grid, r):
                    end_placed = True
                    empty_rooms.remove(r)
                    break
            if end_placed:
                break

        if not start_placed:
            raise ValueError("failed to place end anywhere on path...")

        while len(empty_rooms) > 0:
            r = empty_rooms.pop()
            if random.random() < 0.95:
                feat = worldgen2.Features.get_random_feature(at_level=level)
                if feat is not None:
                    worldgen2.FeatureUtils.try_to_place_feature_into_rect(feat, t_grid, r)

        return t_grid

    @staticmethod
    def generate_new_world(zone, dims=None, min_dims=(3, 3), max_dims=(3, 3)):
        if dims is not None:
            grid_dims = dims
        else:
            grid_dims = (random.choice([x for x in range(min(max_dims[0], min_dims[0]), max_dims[0] + 1)]),
                         random.choice([y for y in range(min(min_dims[1], max_dims[1]), max_dims[1] + 1)]))

        t_grid = ZoneBuilder.generate_tile_grid(zone.get_level(), dims=grid_dims)

        print("INFO: generated world: level={}".format(zone.get_level()))
        print(t_grid)

        w = ZoneBuilder._tile_grid_to_world(zone.get_id(), zone.get_level(), t_grid)
        w.set_geo_color(zone.get_color())

        return w

    @staticmethod
    def make_generated_zone(level, name, zone_id, dims=None, min_dims=(3, 3), max_dims=(3, 3),
                            music_id=None, geo_color=None):
        zone = Zone(name, level)
        zone.ZONE_ID = zone_id
        zone.zone_id = zone_id

        if music_id is not None:
            zone.music_id = music_id
        if geo_color is not None:
            zone.geo_color = geo_color

        zone.build_world = lambda: ZoneBuilder.generate_new_world(zone, dims=dims, min_dims=min_dims, max_dims=max_dims)
        return zone


class LootZoneBuilder:

    TRADE_NPC = (255, 140, 230)

    @staticmethod
    def generate_new_world(zone):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(zone.get_id(), zone.get_file(), zone.get_level())

        w = bp.build_world()

        all_temps = [t for t in npc.all_templates()]
        if LootZoneBuilder.TRADE_NPC in unknowns:
            for i in range(0, len(unknowns[LootZoneBuilder.TRADE_NPC])):
                pos = unknowns[LootZoneBuilder.TRADE_NPC][i]
                if i < len(all_temps):
                    template = all_temps[i]
                    if template.get_trade_protocol(zone.get_level()) is not None:
                        ent = npc.NpcFactory.gen_trade_npc(template.npc_id, zone.get_level())
                        w.add(ent, gridcell=pos)

        return w

    @staticmethod
    def make_generated_zone(level):
        name = "Loot Zone {}".format((level + 1))
        zone = Zone(name, level, filename="loot_zone.png")

        zone_id = "loot_zone_{}".format(level)
        zone.ZONE_ID = zone_id
        zone.zone_id = zone_id

        # kinda nice to have the loot zones look like the story zones the represent
        story_zones_at_this_level = [x for x in all_storyline_zone_ids() if get_zone(x).get_level() == level]
        if len(story_zones_at_this_level) > 0:
            zone.geo_color = get_zone(story_zones_at_this_level[0]).get_color()

        zone.build_world = lambda: LootZoneBuilder.generate_new_world(zone)
        return zone


class DesolateCaveZone(Zone):
    """This is the tutorial / intro zone"""

    ZONE_ID = "desolate_cave"

    MUSHROOM_COLOR = (255, 175, 175)
    MUSHROOM_COLOR_SP = (255, 175, 177)  # these can have a switch behind them
    RAKE_COLOR = (255, 220, 175)
    DIALOG_TRIGGER_1_COLOR = (255, 95, 95)

    SPECIAL_SPOT = (60, 140, 230)

    WALL_SIGNS = {
            (255, 133, 0): ("read", "it's a schedule. it says:\n\nplanted:    5.164  5.162  8.164\n""harvests:       3      9      2"),
            (255, 186, 150): ("[i] to read", "use [i] to pick up items, interact with things, and dismiss text."),
            (255, 184, 150): ("[i] to read", "doors and chests will open on their own if you stand next to them for a little while."),
            (255, 182, 150): ("[i] to read", ["use [r] to open inventory.", "items in the top 5x5 grid are currently equipped. the bottom grid is for storage."]),
            (255, 180, 150): ("[i] to read", ["use the mouse to equip some items. right-click rotates the active item.", "you can't fit everything, so use your equipment grid squares wisely."]),
            (255, 178, 150): ("[i] to read", "use [j] to attack. you can't be hit while in the air."),
            (255, 176, 150): ("[i] to read", "use [k] to heal. healing potions can be collected from chests and slain enemies."),
            (255, 174, 150): ("[i] to read", "the controls are also on the hotbar at the bottom of the screen."),
            (255, 172, 150): ("[i] to read", "good luck!")
    }

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave", 1, filename="desolate_cave.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        spawn = bp.player_spawn

        for n in Utils.neighbors(*spawn, and_diags=True):
            bp.chest_spawns.append((n[0], n[1]))

        w = bp.build_world()

        if DesolateCaveZone.SPECIAL_SPOT in unknowns:
            special_spot = unknowns[DesolateCaveZone.SPECIAL_SPOT][0]
            ent = npc.NpcFactory.gen_trade_npc(npc.NpcID.MACHINE, 5)
            w.add(ent, gridcell=special_spot)
            w.set_geo(special_spot[0], special_spot[1], World.FLOOR)

        for pos in unknowns[DesolateCaveZone.MUSHROOM_COLOR]:
            m_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            text = "it's a large cluster of mushrooms. they're overgrown and rotten."
            mushroom_entity = entities.DecorationEntity.wall_decoration(m_sprite, pos[0], pos[1],
                                                                        interact_dialog=dialog.PlayerDialog(text))
            w.add(mushroom_entity)

        sp_mushrooms = unknowns[DesolateCaveZone.MUSHROOM_COLOR_SP]
        hidden_switch_idx = random.randint(0, len(sp_mushrooms) - 1)
        for i in range(0, len(sp_mushrooms)):
            m_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            pos = sp_mushrooms[i]
            if i == hidden_switch_idx:
                text = "you flip the switch."
                unlock_dialog = dialog.PlayerDialog(text)
                switch_pos = ((pos[0] + 0.5) * 64, (pos[1] + 0.5) * 64)
                doors = w.entities_in_circle(switch_pos, 800, onscreen=False,
                                             cond=lambda ent: ent.is_door())
                nearest_door = doors[0]
                action = lambda _e, _w: nearest_door.do_open()
                listener = events.EventListener(action, events.EventType.DIALOG_EXIT,
                                                lambda event: event.get_uid() == unlock_dialog.get_uid(),
                                                single_use=True)
                gs.get_instance().add_trigger(listener)
                mushroom_entity = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_switches,
                                                                            pos[0], pos[1],
                                                                            interact_dialog=unlock_dialog)
            else:
                if i == (hidden_switch_idx + 1) % len(sp_mushrooms):
                    text = "there's nothing interesting here. it's just a large cluster of mushrooms."
                else:
                    text = "this won't help us open the door. it's just a large cluster of mushrooms."
                mushroom_entity = entities.DecorationEntity.wall_decoration(m_sprite, pos[0], pos[1],
                                                                            interact_dialog=dialog.PlayerDialog(text))
            w.add(mushroom_entity)

        for pos in unknowns[DesolateCaveZone.RAKE_COLOR]:
            text = "it's a rake."
            rake_entity = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_rake,
                                                            pos[0], pos[1], interact_dialog=dialog.PlayerDialog(text))
            w.add(rake_entity)

        for key in unknowns:
            if key in DesolateCaveZone.WALL_SIGNS:
                pos = unknowns[key][0]
                hover_text = DesolateCaveZone.WALL_SIGNS[key][0]
                dialog_text = Utils.listify(DesolateCaveZone.WALL_SIGNS[key][1])
                d = dialog.Dialog.link_em_up([dialog.PlayerDialog(x) for x in dialog_text])

                sign = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_sign, pos[0], pos[1],
                                                                 interact_dialog=d)
                w.add(sign)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_enemies(self):
        return [enemies.TEMPLATE_CAVE_CRAWLER]


class DesolateCaveZone2(Zone):

    ZONE_ID = "desolate_cave_2"

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave II", 2, filename="desolate_cave_2.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_enemies(self):
        return [enemies.TEMPLATE_CAVE_CRAWLER]


class DesolateCaveZone3(Zone):
    ZONE_ID = "desolate_cave_3"

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave III", 4, filename="desolate_cave_3.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_enemies(self):
        return [enemies.TEMPLATE_CAVE_CRAWLER, enemies.TEMPLATE_MUNCHER_SMALL]


class TitleSceneZone(Zone):
    # note that this zone only exists to make it easier to create the title scene (via screenshots).
    # it isn't ever built or rendered live during normal play.

    ZONE_ID = "title_scene"

    def __init__(self):
        Zone.__init__(self, "Title Scene", 0, filename="title_scene.png", bg_color=colors.BLACK)
        self.mushroom_id = (255, 150, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        w = bp.build_world()

        if self.mushroom_id in unknowns:
            for pos in unknowns[self.mushroom_id]:
                ent = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationType.MUSHROOM)
                w.add(ent, gridcell=(pos[0], pos[1] - 1))

        return w


class HauntedForestZone1(Zone):

    ZONE_ID = "haunted_forest_1"

    def __init__(self):
        Zone.__init__(self, "Haunted Forest 1", 3, filename="haunted_forest_1.png", bg_color=colors.DARK_GRAY)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        for x in range(0, bp.width()):
            for y in range(0, bp.height()):
                if bp.get(x, y) == World.FLOOR and bp.get_alt_art(x, y) is None:
                    if random.random() < 0.125:
                        bp.set_alt_art(x, y, spriteref.FLOOR_SWAMP_ID)
                    elif random.random() < 0.5:
                        bp.set_alt_art(x, y, spriteref.FLOOR_CRACKED_ID)
        w = bp.build_world()

        return w

    def get_enemies(self):
        return [enemies.TEMPLATE_CAVE_CRAWLER, enemies.TEMPLATE_MUNCHER_SMALL_ALT, enemies.TEMPLATE_FUNGOI]


class FrogLairZone(Zone):

    ZONE_ID = "frog_lair"

    FROG_BOSS_SPAWN = (255, 170, 170)
    FROG_SPAWN = (255, 194, 194)

    def __init__(self):
        Zone.__init__(self, "The Dark Pool", 7, filename="frog_lair.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        boss_spawn = unknowns[FrogLairZone.FROG_BOSS_SPAWN][0]

        boss_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_FROG, self.get_level())
        w.add(boss_entity, gridcell=boss_spawn)

        if FrogLairZone.FROG_SPAWN in unknowns:
            for frog_spawn in unknowns[FrogLairZone.FROG_SPAWN]:
                frog_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_SMALL_FROG, self.get_level())
                w.add(frog_entity, gridcell=frog_spawn)

        return w

    def get_music_id(self):
        return music.Songs.AMPHIBIAN

    def is_boss_zone(self):
        return True

    def get_color(self):
        return colors.LIGHT_GREEN


class RoboLairZone(Zone):

    ZONE_ID = "robo_lair"

    def __init__(self):
        Zone.__init__(self, "Server Room", 11, filename="robo_lair.png")
        self._robo_color = (255, 170, 170)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        robo_pos = unknowns[self._robo_color][0]
        robo_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_ROBO, self.get_level())
        w.add(robo_entity, gridcell=robo_pos)

        return w

    def get_music_id(self):
        return music.Songs.DEAD_CITY

    def get_color(self):
        return colors.LIGHT_BLUE

    def is_boss_zone(self):
        return True


class NamelessLairZone(Zone):

    ZONE_ID = "???_lair"

    def __init__(self):
        Zone.__init__(self, "Unearth", 15, filename="???_lair.png")
        self._nameless_color = (255, 170, 170)

    def gen_mushroom_enemy(self):
        import src.game.enemies as enemies_clz

        templates = enemies_clz.get_all_rand_spawn_templates(
            cond=lambda t: enemies_clz.EnemyTypes.FUNGUS in t.get_types())
        if len(templates) > 0:
            return enemies_clz.EnemyFactory.gen_enemy(random.choice(templates), self.level)
        else:
            return None

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        # pick one of n spawn positions randomly
        nameless_spawns = unknowns[self._nameless_color]
        nameless_pos = random.choice(nameless_spawns)

        # remove enemies in same room as nameless
        enemy_spawns_to_rem = []
        for e_pos in bp.enemy_spawns:
            if Utils.dist(e_pos, nameless_pos) <= 5:
                enemy_spawns_to_rem.append(e_pos)
        for e_pos in enemy_spawns_to_rem:
            bp.enemy_spawns.remove(e_pos)

        min_dist = 10
        min_dist_chance = 0.25
        max_dist = 75
        max_dist_chance = 0.75

        mushroom_positions = []

        for x in range(0, bp.width()):
            for y in range(0, bp.height()):
                geo = bp.get(x, y)
                if geo == World.EMPTY:
                    continue

                # the closer we are, the more mushroomy and cracked it is
                dist = Utils.dist((x, y), nameless_pos)
                dist = Utils.bound(dist, min_dist, max_dist)
                dist_pct = (dist - min_dist) / (max_dist - min_dist)

                chance_to_fungify = min_dist_chance + dist_pct * (max_dist_chance - min_dist_chance)

                if geo == World.FLOOR:
                    if random.random() < chance_to_fungify or (x, y) == bp.player_spawn:
                        bp.set_alt_art(x, y, spriteref.FLOOR_CRACKED_ID)
                    if y != 0 and bp.get(x, y - 1) == World.WALL:
                        if random.random() < chance_to_fungify:
                            mushroom_positions.append((x, y))
                elif geo == World.WALL:
                    if random.random() < chance_to_fungify:
                        bp.set_alt_art(x, y, spriteref.WALL_CRACKED_ID)

        bp.set_enemy_supplier(lambda _x, _y: self.gen_mushroom_enemy())

        w = bp.build_world()

        nameless_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_NAMELESS, self.get_level())
        w.add(nameless_entity, gridcell=nameless_pos)

        for xy in mushroom_positions:
            mushroom_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            mushroom_entity = entities.DecorationEntity.wall_decoration(mushroom_sprite, xy[0], xy[1])
            w.add(mushroom_entity)

        return w

    def is_boss_zone(self):
        return True

    def get_color(self):
        return colors.LIGHT_PURPLE

    def get_music_id(self):
        return music.Songs.UNEARTHED


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_horror_lair"

    def __init__(self):
        Zone.__init__(self, "Cave Horror's Lair", 15, filename="cave_horror.png")
        self._tree_color = (255, 170, 170)
        self._husk_color = (255, 194, 194)
        self._bounds_color = (255, 190, 0)
        self._rake_color = (255, 220, 175)
        self._bucket_color = (225, 200, 0)
        self._mushroom_colors = [(255, 175, 100), (225, 175, 100)]  # mushrooms for varying floor types

        self._special_door = (0, 175, 255)  # the door that triggers the song and such

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        special_door_pos = unknowns[self._special_door][0]
        bp.set(special_door_pos[0], special_door_pos[1], World.DOOR)

        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        if self._rake_color in unknowns:
            for xy in unknowns[self._rake_color]:
                dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationType.RAKE)
                w.add(dec, gridcell=(xy[0], xy[1] - 1))

        if self._bucket_color in unknowns:
            for xy in unknowns[self._bucket_color]:
                dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationType.BUCKET)
                w.add(dec, gridcell=(xy[0], xy[1] - 1))

        for mushroom_color in self._mushroom_colors:
            if mushroom_color in unknowns:
                for xy in unknowns[mushroom_color]:
                    dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationType.MUSHROOM)
                    w.add(dec, gridcell=(xy[0], xy[1] - 1))

        bounds_rect = Utils.get_rect_containing_points(unknowns[self._bounds_color], inclusive=True)

        inital_husk_spawns = unknowns[self._husk_color]

        tree_pos = unknowns[self._tree_color][0]
        tree_entity = self.gen_tree_entity(bounds_rect, inital_husk_spawns, min_n_husks=2)
        w.add(tree_entity, gridcell=tree_pos)

        import src.world.cameramodifiers as cameramodifiers
        camera_shift_rect = Utils.rect_expand(bounds_rect, left_expand=1)  # gotta encompass the door's square too
        camera_shifter = cameramodifiers.SnapToEntityModifier(camera_shift_rect, tree_entity)
        w.add_camera_modifier(camera_shifter)

        tree_uid = tree_entity.get_uid()

        special_door = w.get_door_in_cell(*special_door_pos)
        if special_door is None:
            raise ValueError("there's no door in the cell: {}".format(special_door_pos))

        def entry_door_action(world):
            # play the song when the player opens the door, for maximum drama
            music.play_song(music.Songs.TREE_THEME)

            tree_ent_in_world = w.get_entity(tree_uid, onscreen=False)
            if tree_ent_in_world is not None:
                # want it to wait a few turns before it starts summoning
                import src.game.statuseffects as statuseffects
                no_summon_effect = statuseffects.new_summoning_sickness_effect(4)
                tree_ent_in_world.get_actor_state().add_status_effect(no_summon_effect)

        special_door.add_special_open_hook("cave_horror_main_door", entry_door_action)

        return w

    def is_boss_zone(self):
        return True

    def get_music_id(self):
        # the real song is triggered by the door
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_RED

    def gen_tree_entity(self, arena_rect, spawn_positions, min_n_husks=2):

        import src.game.gameengine as gameengine

        class _CaveHorrorController(gameengine.EnemyController):

            def __init__(self, level, rect, positions, husk_limit=2):
                gameengine.EnemyController.__init__(self)
                self._arena_rect = rect
                self._initial_spawns = [x for x in positions]
                self._level = level
                self._husk_limit = husk_limit

            def gen_spawned_minion(self):
                return enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_INFECTED_HUSK, self._level)

            def get_next_action(self, actor, world):
                if actor.is_visible_in_world(world):

                    summon_color = colors.RED

                    if len(self._initial_spawns) > 0:
                        inital_spawns_copy = [x for x in self._initial_spawns]
                        random.shuffle(inital_spawns_copy)
                        new_husk = self.gen_spawned_minion()
                        for pos in inital_spawns_copy:
                            # these summons are meant to be quick, so they don't give it summoning sickness
                            spawn_action = gameengine.SpawnActorAction(actor, pos, new_husk, apply_sickness=False,
                                                                       art_color=summon_color)
                            if spawn_action.is_possible(world):
                                self._initial_spawns.remove(pos)  # can only use each spawn point once.
                                return spawn_action

                    arena_length = world.cellsize() * max(self._arena_rect[2], self._arena_rect[3])
                    enemies_nearby = world.entities_in_circle(actor.center(),
                                                              round(arena_length * 1.4142),
                                                              onscreen=False,
                                                              cond=lambda ent: ent.is_enemy() and actor is not ent)

                    if len(enemies_nearby) < self._husk_limit:
                        rand_pos_x = random.randint(self._arena_rect[0], self._arena_rect[0] + self._arena_rect[2])
                        rand_pos_y = random.randint(self._arena_rect[1], self._arena_rect[1] + self._arena_rect[3])
                        spawn_action = gameengine.SpawnActorAction(actor, (rand_pos_x, rand_pos_y),
                                                                   self.gen_spawned_minion(),
                                                                   art_color=summon_color)
                        if spawn_action.is_possible(world):
                            return spawn_action

                    a_pos = world.to_grid_coords(*actor.center())
                    for n in Utils.neighbors(*a_pos):
                        attack_action = gameengine.MeleeAttackAction(actor, None, n)
                        if attack_action.is_possible(world):
                            return attack_action

                pos = world.to_grid_coords(actor.center()[0], actor.center()[1])
                return gameengine.SkipTurnAction(actor, pos)

        controller = _CaveHorrorController(self.get_level(), arena_rect, spawn_positions, husk_limit=min_n_husks)

        return enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_CAVE_HORROR, self.get_level(), controller=controller)


class TombTownZone(Zone):

    ZONE_ID = "tomb_town"

    def __init__(self):
        Zone.__init__(self, "Tomb Town", 3, filename="town.png", bg_color=colors.BLACK)

    WALL_SIGNS = {
        (255, 172, 150): ["The City of Tomb Town\nPopulation: 3"],
        (255, 173, 150): ["Necromancy Supplies and Consultancy"],
        (255, 174, 150): ["Beanskull's Tomato Grove"],
        (255, 175, 150): ["Notice Board:\n"
                          "Tax season is coming up! Late fees WILL be enforced."],
        (255, 176, 150): ["Tomb Town City Hall"],
        (205, 177, 150): ["Tomb Town Treasury\n" +
                          "Absolutely NO Unauthorized Access"],
        (255, 178, 150): ["P. Patches:    20,354.76m\n" +
                          "M. Skelly:       -150.00m\n" +
                          "B. Skull:          17.80m\n"]
    }

    BEANSKULL = (255, 170, 255)
    MAYOR = (205, 171, 255)
    MARY = (255, 172, 255)
    GLORPLE = (255, 173, 255)

    SPIDER_BOSS = (255, 170, 170)

    MUSHROOMS = (255, 175, 177)
    TOMATO_PLANTS = (255, 234, 150)
    WORKBENCH = (255, 220, 115)
    BONE_DECORATIONS = (255, 230, 115)
    RAKE = (255, 225, 115)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        dec_type_lookup = {TombTownZone.MUSHROOMS: (decoration.DecorationType.MUSHROOM, None),
                           TombTownZone.TOMATO_PLANTS: (decoration.DecorationType.PLANT, "It's a tomato plant. It looks well-maintained."),
                           TombTownZone.RAKE: (decoration.DecorationType.RAKE, None),
                           TombTownZone.WORKBENCH: (decoration.DecorationType.WORKBENCH, None)}

        for key in unknowns:
            if key in TombTownZone.WALL_SIGNS:
                pos = unknowns[key][0]
                sign = decoration.DecorationFactory.get_sign(self.get_level(), sign_text=TombTownZone.WALL_SIGNS[key])
                w.add(sign, gridcell=(pos[0], pos[1] - 1))

            elif key in dec_type_lookup:
                for pos in unknowns[key]:
                    dec_type, dec_desc = dec_type_lookup[key]
                    dec_entity = decoration.DecorationFactory.get_decoration(self.get_level(), dec_type, with_dialog=dec_desc)
                    w.add(dec_entity, gridcell=(pos[0], pos[1] - 1))
            elif key == TombTownZone.BEANSKULL:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.BEANSKULL, npc.Conversations.BEANSKULL_INTRO)
                w.add(e, gridcell=unknowns[key][0])
            elif key == TombTownZone.MAYOR:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.MAYOR, npc.Conversations.MAYOR_INTRO)
                w.add(e, gridcell=unknowns[key][0])
            elif key == TombTownZone.MARY:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_INTRO)
                w.add(e, gridcell=unknowns[key][0])
            elif key == TombTownZone.SPIDER_BOSS:
                e = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_SPIDER, self.get_level())
                max_hp = e.get_actor_state().max_hp()
                e.get_actor_state().set_hp(int(0.75 * max_hp))  # it's injured because it was fighting the town
                w.add(e, gridcell=unknowns[key][0])

        return w

    def get_music_id(self):
        return music.Songs.SPIDER_THEME


class DoorTestZone(Zone):

    ZONE_ID = "door_test"

    def __init__(self):
        Zone.__init__(self, "Main Zone", 3, filename="door_test_1.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


class DoorTestZoneL(Zone):

    ZONE_ID = "door_test_l"

    def __init__(self):
        Zone.__init__(self, "Test Zone Left", 17, filename="door_test_L.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


class DoorTestZoneR(Zone):

    ZONE_ID = "door_test_r"

    def __init__(self):
        Zone.__init__(self, "Test Zone Right", 17, filename="door_test_R.png")

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


