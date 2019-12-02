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


def get_zone(zone_id, or_else="~fail~"):
    if zone_id not in _ALL_ZONES or _ALL_ZONES[zone_id] is None:
        if or_else == "~fail~":
            raise ValueError("unrecognized zone id: {}".format(zone_id))
        else:
            return or_else
    else:
        return _ALL_ZONES[zone_id]


def is_end_of_game(zone_id):
    return zone_id == _END_OF_GAME_ZONE_ID


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

    caves_song = music.Songs.get_basic_caves_song()
    story_zones.append(ZoneBuilder.make_generated_zone(0, "Caves I", "caves_1", dims=(3, 1), music_id=caves_song))
    story_zones.append(ZoneBuilder.make_generated_zone(1, "Caves II", "caves_2", dims=(4, 1), music_id=caves_song))
    story_zones.append(ZoneBuilder.make_generated_zone(2, "Caves III", "caves_3", dims=(3, 2), music_id=caves_song))
    story_zones.append(get_zone(TombTownZone.ZONE_ID))

    swamp_song = music.Songs.get_basic_swamp_song()
    green_color = get_zone(FrogLairZone.ZONE_ID).get_color()

    story_zones.append(ZoneBuilder.make_generated_zone(4, "Swamps I", "swamps_1", geo_color=green_color, music_id=swamp_song,
                                                       conversation_ids=[npc.Conversations.MARY_SKELLY_SWAMPS_1.get_id()]))

    story_zones.append(ZoneBuilder.make_generated_zone(5, "Swamps II", "swamps_2", geo_color=green_color, music_id=swamp_song))
    story_zones.append(ZoneBuilder.make_generated_zone(6, "Swamps III", "swamps_3", geo_color=green_color, music_id=swamp_song))
    story_zones.append(get_zone(FrogLairZone.ZONE_ID))
    story_zones.append(get_zone(CityGateZone.ZONE_ID))

    city_song = music.Songs.get_basic_city_song()
    blue_color = get_zone(RoboLairZone.ZONE_ID).get_color()

    story_zones.append(ZoneBuilder.make_generated_zone(8, "City I", "city_1", geo_color=blue_color, music_id=city_song))
    story_zones.append(ZoneBuilder.make_generated_zone(9, "City II", "city_2", geo_color=blue_color, music_id=city_song))
    story_zones.append(ZoneBuilder.make_generated_zone(10, "City III", "city_3", geo_color=blue_color, music_id=city_song))
    story_zones.append(get_zone(RoboLairZone.ZONE_ID))

    core_song = music.Songs.get_basic_core_song()
    red_color = get_zone(CaveHorrorZone.ZONE_ID).get_color()
    
    story_zones.append(ZoneBuilder.make_generated_zone(12, "Rotten Core I", "rotten_core_1", geo_color=red_color, music_id=core_song))
    story_zones.append(ZoneBuilder.make_generated_zone(13, "Rotten Core II", "rotten_core_2", geo_color=red_color, music_id=core_song))
    story_zones.append(ZoneBuilder.make_generated_zone(14, "Rotten Core III", "rotten_core_3", geo_color=red_color, music_id=core_song))
    story_zones.append(get_zone(CaveHorrorZone.ZONE_ID))

    story_zones.append(get_zone(NamelessZone.ZONE_ID))
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
    MUSIC_DOOR = (0, 175, 255)
    PLAYER_SPAWN = (0, 255, 0)
    MONSTER_SPAWN = (255, 255, 0)
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
                    elif color == ZoneLoader.MUSIC_DOOR:
                        music_id = get_zone(zone_id).get_special_door_music_id()
                        if music_id is None:
                            print("WARN: no song exists for music door at ({}, {})".format(x, y))
                            bp.set(x, y, World.DOOR)
                        else:
                            bp.set_music_door(x, y, music_id)
                    elif color == ZoneLoader.RETURN_EXIT:
                        bp.set(x, y, World.FLOOR)
                        bp.return_exit_spawns.append((x, y))
                    elif color == ZoneLoader.EXIT:
                        bp.set(x, y, World.FLOOR)
                        bp.add_exit_door(x, y, exit_id)
                    elif color == ZoneLoader.CHEST_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.chest_spawns.append((x, y))
                    elif color == ZoneLoader.MONSTER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.enemy_spawns.append((x, y))
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

        self.conversation_ids = []
        self.max_n_conversations = 1
        self.max_n_trades = 1

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

    def get_special_door_music_id(self):
        return None

    def build_world(self):
        pass

    def is_boss_zone(self):
        return False

    def get_enemies(self):
        """List of templates of enemies that can randomly spawn here."""
        return []

    def get_conversation_ids(self):
        """List of conversation_ids that can randomly spawn here"""
        return self.conversation_ids

    def get_max_n_conversations(self):
        """Max number of conversation npcs that can randomly spawn here"""
        return self.max_n_conversations

    def get_max_n_trades(self):
        """Max number of trade npcs that can randomly spawn here"""
        return self.max_n_trades


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
            if is_end_of_game(next_zone_id):
                world.add(entities.EndGameExitEnitity(x, y))
            else:
                actual_next_zone = get_zone(next_zone_id, or_else=None)
                if actual_next_zone is not None:
                    if actual_next_zone.is_boss_zone():
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

        actual_zone = get_zone(zone_id, or_else=None)

        used_npc_ids = []  # avoid duplicate NPCs popping up

        if actual_zone is not None and len(convo_npc_coords) > 0:
            valid_convos = actual_zone.get_conversation_ids()
            convo_npc_ents = npc.NpcFactory.gen_convo_npcs(valid_convos, len(convo_npc_coords),
                                                           not_npc_ids=used_npc_ids)
            random.shuffle(convo_npc_coords)
            for i in range(0, len(convo_npc_ents)):
                world.add(convo_npc_ents[i], gridcell=convo_npc_coords[i])
                used_npc_ids.append(convo_npc_ents[i].get_npc_id())

        if len(trade_npc_coords) > 0:
            trade_npc_ents = npc.NpcFactory.gen_trade_npcs(level, len(trade_npc_coords),
                                                           not_npc_ids=used_npc_ids)
            random.shuffle(trade_npc_coords)
            for i in range(0, len(trade_npc_ents)):
                world.add(trade_npc_ents[i], gridcell=trade_npc_coords[i])
                used_npc_ids.append(trade_npc_ents[i].get_npc_id())

        return world

    @staticmethod
    def generate_tile_grid(zone_id, level, dims=(3, 3), num_tries=100):
        for i in range(0, num_tries):
            try:
                res = ZoneBuilder.generate_tile_grid_dangerously(zone_id, level, dims=dims)

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
    def generate_tile_grid_dangerously(zone_id, level, dims=(3, 3)):
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

        feature_counts = {}  # feat_id -> int count

        # list of (Feature, ..., Feature, bool).
        #
        # the features represent a feature (and optional backups) to try to place
        # if bool is True, will try to place the feature near the start. False will try near the end,
        # and None will place the feature randomly.
        required_path_features = [(worldgen2.Features.START, worldgen2.Features.BACKUP_START, True),
                                  (worldgen2.Features.EXIT, False)]
        optional_path_features = []

        actual_zone = get_zone(zone_id, or_else=None)
        if actual_zone is not None and len(actual_zone.get_conversation_ids()) > 0:
            convos = [c for c in actual_zone.get_conversation_ids()]
            n_to_add = min(len(convos), actual_zone.get_max_n_conversations())
            for _ in range(0, n_to_add):
                optional_path_features.append((worldgen2.Features.STORY_NPC, None))

        all_path_features = required_path_features + optional_path_features

        for i in range(0, len(all_path_features)):
            feat_spec = all_path_features[i]
            required = i < len(required_path_features)
            near_start = feat_spec[-1]
            feats = [feat_spec[i] for i in range(0, len(feat_spec)-1)]

            candidate_rooms = []

            for p in path:
                rooms_in_p = list(room_map.get(p))
                random.shuffle(rooms_in_p)
                for r in rooms_in_p:
                    if r not in empty_rooms:
                        continue
                    candidate_rooms.append(r)

            if near_start is None:
                random.shuffle(candidate_rooms)
            elif near_start is False:
                candidate_rooms.reverse()

            feat_added, to_room = ZoneBuilder._try_to_add_a_feature_to_any_room(t_grid, feats, candidate_rooms)
            if to_room is not None:
                empty_rooms.remove(to_room)

                if feat_added.feat_id not in feature_counts:
                    feature_counts[feat_added.feat_id] = 1
                else:
                    feature_counts[feat_added.feat_id] += 1

            elif required:
                raise ValueError("failed to add feature {} to world".format(feat_spec[0].feat_id))

        while len(empty_rooms) > 0:
            r = empty_rooms.pop()
            if random.random() < 0.95:
                feat = worldgen2.Features.get_random_feature(at_level=level, current_counts=feature_counts)
                if feat is not None:
                    did_place = worldgen2.FeatureUtils.try_to_place_feature_into_rect(feat, t_grid, r)

                    if did_place:
                        if feat.feat_id not in feature_counts:
                            feature_counts[feat.feat_id] = 1
                        else:
                            feature_counts[feat.feat_id] += 1

        return t_grid

    @staticmethod
    def _try_to_add_a_feature_to_any_room(t_grid, features, rooms):
        for feat in features:
            for r in rooms:
                if worldgen2.FeatureUtils.try_to_place_feature_into_rect(feat, t_grid, r):
                    return (feat, r)
        return (None, None)

    @staticmethod
    def generate_new_world(zone, dims=None, min_dims=(3, 3), max_dims=(3, 3)):
        if dims is not None:
            grid_dims = dims
        else:
            grid_dims = (random.choice([x for x in range(min(max_dims[0], min_dims[0]), max_dims[0] + 1)]),
                         random.choice([y for y in range(min(min_dims[1], max_dims[1]), max_dims[1] + 1)]))

        t_grid = ZoneBuilder.generate_tile_grid(zone.get_id(), zone.get_level(), dims=grid_dims)

        print("INFO: generated world: level={}".format(zone.get_level()))
        print(t_grid)

        w = ZoneBuilder._tile_grid_to_world(zone.get_id(), zone.get_level(), t_grid)
        w.set_geo_color(zone.get_color())

        return w

    @staticmethod
    def make_generated_zone(level, name, zone_id, dims=None, min_dims=(3, 3), max_dims=(3, 3),
                            music_id=None, geo_color=None, conversation_ids=None):
        zone = Zone(name, level)
        zone.ZONE_ID = zone_id
        zone.zone_id = zone_id

        if conversation_ids is not None:
            zone.conversation_ids = conversation_ids
        if music_id is not None:
            zone.music_id = music_id
        if geo_color is not None:
            zone.geo_color = geo_color

        zone.build_world = lambda: ZoneBuilder.generate_new_world(zone, dims=dims,
                                                                  min_dims=min_dims, max_dims=max_dims)
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


def _get_remove_entity_on_death_hook(entity_uid, show_explosion=True):
    def remove_entity_hook(world, entity):
        if entity_uid is not None:
            ent = world.get_entity(entity_uid, onscreen=False)
            if ent is not None:
                world.remove(ent)

                c_xy = ent.center()
                if show_explosion:
                    world.show_explosion(c_xy[0], c_xy[1], 20)
    return remove_entity_hook


class FrogLairZone(Zone):

    ZONE_ID = "frog_lair"

    FROG_BOSS_SPAWN = (255, 170, 170)
    FROG_SPAWN = (255, 194, 194)

    NPC_SPAWN_1 = (255, 172, 150)
    NPC_SPAWN_2 = (255, 172, 151)

    def __init__(self):
        Zone.__init__(self, "The Dark Pool", 7, filename="frog_lair.png")

    def gen_frog_boss_entity(self, positions):

        import src.game.gameengine as gameengine

        class _FrogBossController(gameengine.EnemyController):

                def __init__(self, positions, min_leap_chance=0.1, max_leap_chance=0.6):
                    gameengine.EnemyController.__init__(self)
                    self._arena_positions = positions
                    self._min_leap_chance = min_leap_chance
                    self._max_leap_chance = max_leap_chance

                def get_special_leap_action_if_possible(self, actor, world):
                    player = world.get_player()
                    if player is None:
                        return None

                    if not actor.is_visible_in_world(world):
                        return None

                    player_xy = world.to_grid_coords(*player.center())
                    actor_xy = world.to_grid_coords(*actor.center())

                    # don't leap if you can attack directly
                    if Utils.dist_manhattan(player_xy, actor_xy) <= 1:
                        return None

                    scrambled_positions = [x for x in self._arena_positions]
                    random.shuffle(scrambled_positions)

                    for p in scrambled_positions:
                        act = gameengine.FrogLeapAction(actor, p)
                        if act.is_possible(world):
                            return act

                    return None

                def get_next_action(self, actor, world):
                    hp_pct = actor.get_actor_state().hp() / actor.get_actor_state().max_hp()
                    leap_chance = Utils.linear_interp(self._min_leap_chance, self._max_leap_chance, 1 - hp_pct)

                    if random.random() < leap_chance:
                        special_leap = self.get_special_leap_action_if_possible(actor, world)
                        if special_leap is not None:
                            return special_leap

                    return super().get_next_action(actor, world)

        controller = _FrogBossController(positions, min_leap_chance=0.6, max_leap_chance=0.9)

        return enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_FROG,
                                              self.get_level(),
                                              controller=controller)

    def _gen_npc(self, pre_fight):
        if pre_fight:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_PRE_FROG_FIGHT)
        else:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_POST_FROG_FIGHT)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        boss_spawn = unknowns[FrogLairZone.FROG_BOSS_SPAWN][0]

        # do a flood-fill search around the boss's spawn to find the area positions
        arena_positions = set()
        for pos in bp.flood_search(boss_spawn[0], boss_spawn[1], allow_types=(World.FLOOR,)):
            arena_positions.add(pos)
        positions = [x for x in arena_positions]

        boss_entity = self.gen_frog_boss_entity(positions)

        # end the song when the boss dies, for maximum drama
        boss_entity.add_special_death_hook("end_song", lambda _w, _e: music.play_song(self.get_music_id()))

        w.add(boss_entity, gridcell=boss_spawn)

        if FrogLairZone.FROG_SPAWN in unknowns:
            for frog_spawn in unknowns[FrogLairZone.FROG_SPAWN]:
                frog_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_SMALL_FROG, self.get_level())
                w.add(frog_entity, gridcell=frog_spawn)

        pre_fight_npc_uid = None

        if FrogLairZone.NPC_SPAWN_1 in unknowns:
            pre_fight_npc_pos = unknowns[FrogLairZone.NPC_SPAWN_1][0]
            pre_fight_npc = self._gen_npc(True)
            if pre_fight_npc is not None:
                pre_fight_npc_uid = pre_fight_npc.get_uid()
                w.add(pre_fight_npc, gridcell=pre_fight_npc_pos)

        if FrogLairZone.NPC_SPAWN_2 in unknowns:
            post_fight_npc_pos = unknowns[FrogLairZone.NPC_SPAWN_2][0]
            post_fight_npc = self._gen_npc(False)
            if post_fight_npc is not None:
                w.add(post_fight_npc, gridcell=post_fight_npc_pos)

        # remove the pre-fight NPC when the boss dies.
        if pre_fight_npc_uid is not None:
            death_hook = _get_remove_entity_on_death_hook(pre_fight_npc_uid, show_explosion=True)
            boss_entity.add_special_death_hook("remove pre-fight npc", death_hook)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_special_door_music_id(self):
        return music.Songs.AMPHIBIAN

    def is_boss_zone(self):
        return True

    def get_color(self):
        return colors.LIGHT_GREEN


class CityGateZone(Zone):

    ZONE_ID = "city_gate"

    def __init__(self):
        Zone.__init__(self, "City Gate", 7, filename="city_gate.png")
        self._mary_npc = (255, 172, 150)
        self._head_npc = (255, 173, 150)

        self._gate_left = (255, 234, 150)
        self._gate_right = (255, 235, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        dec_lookup = {
            self._gate_left: decoration.DecorationType.GATE_LEFT,
            self._gate_right: decoration.DecorationType.GATE_RIGHT
        }

        head_npc = None
        mary_pos = None

        for key in unknowns:
            for pos in unknowns[key]:
                if key in dec_lookup:
                    dec_type = dec_lookup[key]
                    ent = decoration.DecorationFactory.get_decoration(self.get_level(), dec_type)
                    w.add(ent, gridcell=(pos[0], pos[1] - 1))

            if key == self._mary_npc:
                mary_pos = unknowns[key][0]

            elif key == self._head_npc:
                head_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.HEAD, npc.Conversations.MARY_AND_HEAD_AT_GATE)
                w.add(head_npc, gridcell=unknowns[key][0])

        if mary_pos is not None and head_npc is not None:
            mary_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.MARY_SKELLY, head_npc.get_uid())
            w.add(mary_npc, gridcell=mary_pos)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_GREEN


class RoboLairZone(Zone):

    ZONE_ID = "robo_lair"

    def __init__(self):
        Zone.__init__(self, "Server Room", 11, filename="robo_lair.png")
        self._robo_color = (255, 170, 170)
        self._npc_spawn_1 = (255, 172, 150)
        self._npc_spawn_2 = (255, 172, 151)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        robo_pos = unknowns[self._robo_color][0]
        robo_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_ROBO, self.get_level())

        # end the song when the boss dies, for maximum drama
        robo_entity.add_special_death_hook("end_song", lambda _w, _e: music.play_song(self.get_music_id()))

        w.add(robo_entity, gridcell=robo_pos)

        if self._npc_spawn_1 in unknowns:
            pre_fight_npc_pos = unknowns[self._npc_spawn_1][0]
            pre_fight_npc = self._gen_npc(True)
            if pre_fight_npc is not None:
                pre_fight_npc_uid = pre_fight_npc.get_uid()
                w.add(pre_fight_npc, gridcell=pre_fight_npc_pos)

                # remove npc when boss dies
                death_hook = _get_remove_entity_on_death_hook(pre_fight_npc_uid, show_explosion=True)
                robo_entity.add_special_death_hook("remove pre-fight npc", death_hook)

        if self._npc_spawn_2 in unknowns:
            post_fight_npc_pos = unknowns[self._npc_spawn_2][0]
            post_fight_npc = self._gen_npc(False)
            if post_fight_npc is not None:
                w.add(post_fight_npc, gridcell=post_fight_npc_pos)

        return w

    def _gen_npc(self, pre_fight):
        if pre_fight:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_PRE_FROG_FIGHT)
        else:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_POST_FROG_FIGHT)

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_special_door_music_id(self):
        return music.Songs.DEAD_CITY

    def get_color(self):
        return colors.LIGHT_BLUE

    def is_boss_zone(self):
        return True


def _mushroomify_blueprint(bp, focus_pos, close_chance=0.5, far_chance=0.25):
    min_dist = 10
    max_dist = 75

    mushroom_positions = []

    for x in range(0, bp.width()):
        for y in range(0, bp.height()):
            geo = bp.get(x, y)
            if geo == World.EMPTY:
                continue

            dist = Utils.dist((x, y), focus_pos)
            dist = Utils.bound(dist, min_dist, max_dist)
            dist_pct = (dist - min_dist) / (max_dist - min_dist)

            chance_to_fungify = Utils.linear_interp(far_chance, close_chance, 1 - dist_pct)
            chance_to_crack = chance_to_fungify / 2  # take it easy with the floor/wall cracking...

            if geo == World.FLOOR:
                if random.random() < chance_to_crack or (x, y) == bp.player_spawn:
                    bp.set_alt_art(x, y, spriteref.FLOOR_CRACKED_ID)
                if y != 0 and bp.get(x, y - 1) == World.WALL and not bp.has_exit_at(x, y):
                    if random.random() < chance_to_fungify:
                        mushroom_positions.append((x, y))
            elif geo == World.WALL:
                if random.random() < chance_to_crack:
                    bp.set_alt_art(x, y, spriteref.WALL_CRACKED_ID)

    return mushroom_positions


class NamelessZone(Zone):

    ZONE_ID = "???_zone"

    def __init__(self):
        Zone.__init__(self, "Unearth", 15, filename="???_zone.png")
        self._exit_doors = (255, 175, 80)

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

        # pick one of n door positions randomly
        exit_door_pos = random.choice(unknowns[self._exit_doors])

        next_zone_id = next_storyline_zone(self.get_id())

        bp.add_exit_door(exit_door_pos[0], exit_door_pos[1], next_zone_id)
        for d in unknowns[self._exit_doors]:
            if d != exit_door_pos:
                bp.chest_spawns.append(d)

        mushroom_positions = _mushroomify_blueprint(bp, exit_door_pos)

        bp.set_enemy_supplier(lambda _x, _y: self.gen_mushroom_enemy())

        w = bp.build_world()

        for xy in mushroom_positions:
            mushroom_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            mushroom_entity = entities.DecorationEntity.wall_decoration(mushroom_sprite, xy[0], xy[1])
            w.add(mushroom_entity)

        return w

    def is_boss_zone(self):
        return False

    def get_color(self):
        return colors.LIGHT_PURPLE

    def get_music_id(self):
        return music.Songs.UNEARTHED


class NamelessLairZone(Zone):

    ZONE_ID = "???_lair"

    def __init__(self):
        Zone.__init__(self, "??? Lair", 15, filename="???_lair.png")
        self._nameless_color = (255, 170, 170)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        nameless_pos = unknowns[self._nameless_color][0]

        mushroom_positions = _mushroomify_blueprint(bp, nameless_pos)

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
        return music.Songs.SILENCE

    def get_special_door_music_id(self):
        return music.Songs.NAMELESS_THEME


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

        self._npc_spawn_1 = (255, 172, 150)
        self._npc_spawn_2 = (255, 172, 151)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        if len(bp.music_doors) != 1:
            raise ValueError("should be exactly one special door in zone: {}".format(len(bp.music_doors)))
        special_door_pos = list(bp.music_doors.keys())[0]

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

        # end the song when the boss dies, for maximum drama
        tree_entity.add_special_death_hook("end_song", lambda _w, _e: music.play_song(self.get_music_id()))

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
            tree_ent_in_world = w.get_entity(tree_uid, onscreen=False)
            if tree_ent_in_world is not None:
                # want it to wait a few turns before it starts summoning
                import src.game.statuseffects as statuseffects
                no_summon_effect = statuseffects.new_summoning_sickness_effect(2)
                tree_ent_in_world.get_actor_state().add_status_effect(no_summon_effect)

        special_door.add_special_open_hook("cave_horror_main_door", entry_door_action)

        if self._npc_spawn_1 in unknowns:
            pre_fight_npc_pos = unknowns[self._npc_spawn_1][0]
            pre_fight_npc = self._gen_npc(True)
            if pre_fight_npc is not None:
                pre_fight_npc_uid = pre_fight_npc.get_uid()
                w.add(pre_fight_npc, gridcell=pre_fight_npc_pos)

                # remove npc when boss dies
                death_hook = _get_remove_entity_on_death_hook(pre_fight_npc_uid, show_explosion=True)
                tree_entity.add_special_death_hook("remove pre-fight npc", death_hook)

        if self._npc_spawn_2 in unknowns:
            post_fight_npc_pos = unknowns[self._npc_spawn_2][0]
            post_fight_npc = self._gen_npc(False)
            if post_fight_npc is not None:
                w.add(post_fight_npc, gridcell=post_fight_npc_pos)

        return w

    def _gen_npc(self, pre_fight):
        if pre_fight:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_PRE_FROG_FIGHT)
        else:
            return npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_POST_FROG_FIGHT)

    def is_boss_zone(self):
        return True

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_special_door_music_id(self):
        return music.Songs.TREE_THEME

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

        self.music_id = music.Songs.SILENCE
        self.fight_music_id = music.Songs.ARACHNID
        self.post_fight_music_id = music.Songs.get_basic_caves_song()

    WALL_SIGNS = {
        (255, 172, 150): [" - Outpost 53 - \nWelcome to Tomb Town!"],
        (255, 173, 150): ["Mary's Necromancy Consultancy"],
        (255, 174, 150): ["Beanskull's Tomato Grove"],
        (255, 175, 150): ["Notice Board:\n"
                          "Tax season is coming up! Late fees WILL be enforced."],
        (255, 176, 150): ["Tomb Town City Hall"],
        (205, 177, 150): ["Tomb Town Treasury\n" +
                          "Absolutely NO Unauthorized Access"],
        (255, 178, 150): ["P. Patches:    20,354.76m\n" +
                          "M. Skelly:       -150.00m\n" +
                          "S. Skelly:          0.00m\n" +
                          "B. Skull:          17.80m\n"],
        (255, 179, 150): ["Shelly's Swords and Daggers"]
    }

    BEANSKULL = (255, 170, 255)
    MAYOR = (205, 171, 255)
    MARY = (255, 172, 255)
    MARY_2 = (255, 177, 255)
    GLORPLE = (255, 173, 255)

    SPIDER_BOSS = (255, 170, 170)

    MUSHROOMS = (255, 175, 177)
    TOMATO_PLANTS = (255, 234, 150)
    WORKBENCH = (255, 220, 115)
    BONE_DECORATIONS = (255, 230, 115)
    RAKE = (255, 225, 115)
    BUCKET = (255, 235, 115)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        dec_type_lookup = {TombTownZone.MUSHROOMS: (decoration.DecorationType.MUSHROOM, None),
                           TombTownZone.TOMATO_PLANTS: (decoration.DecorationType.PLANT, "It's a tomato plant. It looks well-maintained."),
                           TombTownZone.RAKE: (decoration.DecorationType.RAKE, None),
                           TombTownZone.WORKBENCH: (decoration.DecorationType.WORKBENCH, None),
                           TombTownZone.BONE_DECORATIONS: (decoration.DecorationType.BONES, "It appears to be a memorial plate of some kind. The bones are made from stone."),
                           TombTownZone.BUCKET: (decoration.DecorationType.BUCKET, None)}

        mary_pre_fight_ent_uid = None
        mary_pos_2 = None

        spider_ent = None

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
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_PRE_SPIDER_FIGHT)
                w.add(e, gridcell=unknowns[key][0])
                mary_pre_fight_ent_uid = e.get_uid()
            elif key == TombTownZone.MARY_2:
                mary_pos_2 = unknowns[key][0]
            elif key == TombTownZone.SPIDER_BOSS:
                pos = unknowns[key][0]
                spider_ent = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_SPIDER, self.get_level())
                w.add(spider_ent, gridcell=pos)

        # setting up all the death hooks on the spider
        if spider_ent is not None:

            on_death_song = self.post_fight_music_id
            if mary_pre_fight_ent_uid is not None:
                rm_entity_hook = _get_remove_entity_on_death_hook(mary_pre_fight_ent_uid, show_explosion=True)
                spider_ent.add_special_death_hook("rm mary", rm_entity_hook)

            spider_ent.add_special_death_hook("play on-death song",
                                              lambda _w, _ent: music.play_song(on_death_song))

            if mary_pos_2 is not None:
                def add_new_mary_hook(_w, _ent):
                    mary_2 = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY,
                                                          npc.Conversations.MARY_SKELLY_POST_SPIDER_FIGHT)

                    if not _w.is_solid(mary_pos_2[0], mary_pos_2[1], including_entities=True):
                        _w.add(mary_2, gridcell=mary_pos_2)
                    else:
                        print("WARN: failed to add npc because position was solid: {}, at {}".format(mary_2, mary_pos_2))
                spider_ent.add_special_death_hook("add mary 2", add_new_mary_hook)

        return w

    def get_music_id(self):
        return self.music_id

    def get_special_door_music_id(self):
        return self.fight_music_id

    def is_boss_zone(self):
        return True


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


