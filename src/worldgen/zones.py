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
import src.game.globalstate as gs
from src.worldgen import worldgen2
import src.game.npc as npc
import src.game.decoration as decoration
import src.utils.colors as colors
import src.game.debug as debug
import src.game.constants as constants

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


def get_zone_id_for_save_id(save_id):
    for z_id in _STORYLINE_ZONES:
        if get_zone(z_id).get_save_id() == save_id:
            return z_id

    for z_id in all_zone_ids():
        if get_zone(z_id).get_save_id() == save_id:
            return z_id
    return None


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


def _conditionally_swapped_next_storyline_zone(normal_zone_id):
    if normal_zone_id == CaveHorrorZone.ZONE_ID:
        if gs.get_instance().is_peaceful_so_far():
            # this is where the peaceful run ends
            return CaveHorrorZonePeaceful.ZONE_ID

    return normal_zone_id


def next_storyline_zone(current_id):
    if current_id == CaveHorrorZonePeaceful.ZONE_ID:
        return _END_OF_GAME_ZONE_ID
    elif current_id not in _STORYLINE_ZONES:
        print("WARN: {} isn't a storyline zone, so there's no 'next' storyline zone".format(current_id))
        return None
    else:
        idx = _STORYLINE_ZONES.index(current_id)
        if idx + 1 < len(_STORYLINE_ZONES):
            res = _STORYLINE_ZONES[idx + 1]
            return _conditionally_swapped_next_storyline_zone(res)
        else:
            # we hit the end
            return _END_OF_GAME_ZONE_ID


def _for_each_subclass_recurs(klazz, lammy):
    for sub_klazz in klazz.__subclasses__():
        lammy(sub_klazz)
        _for_each_subclass_recurs(sub_klazz, lammy)


def _make_and_register_zone_from_class(zone_cls):
    zone_instance = zone_cls()
    zone_instance.zone_id = zone_cls.ZONE_ID
    make(zone_instance)


def init_zones():
    _ALL_ZONES.clear()
    _for_each_subclass_recurs(Zone, _make_and_register_zone_from_class)

    story_zones = []

    story_zones.append(get_zone(QuietInlet.ZONE_ID))

    caves_song = music.Songs.get_basic_caves_song()
    story_zones.append(ZoneBuilder.make_generated_zone(0, "Caves I", "caves_1", dims=(3, 1), music_id=caves_song))
    story_zones.append(ZoneBuilder.make_generated_zone(1, "Caves II", "caves_2", dims=(4, 1), music_id=caves_song))
    story_zones.append(ZoneBuilder.make_generated_zone(2, "Caves III", "caves_3", dims=(3, 2), music_id=caves_song))
    story_zones.append(get_zone(TombtownZone.ZONE_ID))

    story_zones.append(get_zone(TombtownSaveZone.ZONE_ID))

    swamp_song = music.Songs.get_basic_swamp_song()
    green_color = get_zone(FrogLairZone.ZONE_ID).get_color()
    swamp_bonus_decs_1 = [(decoration.DecorationTypes.PLANT, 0.05)]  # presumably these belong to beanskull
    mary_swamp_conv = [npc.Conversations.MARY_SKELLY_SWAMPS.get_id()]

    story_zones.append(ZoneBuilder.make_generated_zone(4, "Swamps I", "swamps_1", geo_color=green_color, music_id=swamp_song, dims=(3, 2), bonus_decorations=swamp_bonus_decs_1))
    story_zones.append(ZoneBuilder.make_generated_zone(5, "Swamps II", "swamps_2", geo_color=green_color, music_id=swamp_song, dims=(3, 2), conversation_ids=mary_swamp_conv))
    story_zones.append(ZoneBuilder.make_generated_zone(6, "Swamps III", "swamps_3", geo_color=green_color, music_id=swamp_song, dims=(4, 2)))
    story_zones.append(get_zone(FrogLairZone.ZONE_ID))
    story_zones.append(get_zone(CityGateZone.ZONE_ID))  # save point

    city_song = music.Songs.get_basic_city_song()
    blue_color = get_zone(RoboLairZone.ZONE_ID).get_color()

    story_zones.append(ZoneBuilder.make_generated_zone(8, "City I", "city_1", geo_color=blue_color, music_id=city_song, dims=(3, 2)))
    story_zones.append(ZoneBuilder.make_generated_zone(9, "City II", "city_2", geo_color=blue_color, music_id=city_song, dims=(4, 2)))
    story_zones.append(get_zone(VentilationZone.ZONE_ID))
    story_zones.append(ZoneBuilder.make_generated_zone(10, "City III", "city_3", geo_color=blue_color, music_id=city_song, dims=(3, 3)))
    story_zones.append(get_zone(RoboLairZone.ZONE_ID))
    story_zones.append(get_zone(RoboSaveZone.ZONE_ID))  # save point

    catacombs_song = music.Songs.get_basic_catacombs_song()
    red_color = get_zone(CaveHorrorZone.ZONE_ID).get_color()
    core_bonus_decs = [(decoration.DecorationTypes.BONE_PILE, 0.2),
                       (decoration.DecorationTypes.MUSHROOM, 0.1)]
    catacombs_conv = [npc.Conversations.MARY_SKELLY_CATACOMBS.get_id()]

    story_zones.append(ZoneBuilder.make_generated_zone(12, "Catacombs I", "core_1", geo_color=red_color, music_id=catacombs_song, dims=(3, 2), bonus_decorations=core_bonus_decs))
    story_zones.append(ZoneBuilder.make_generated_zone(14, "Catacombs II", "core_2", geo_color=red_color, music_id=catacombs_song, dims=(3, 3), bonus_decorations=core_bonus_decs, conversation_ids=catacombs_conv))
    story_zones.append(ZoneBuilder.make_generated_zone(14, "Catacombs III", "core_3", geo_color=red_color, music_id=catacombs_song, dims=(3, 3), bonus_decorations=core_bonus_decs))
    story_zones.append(get_zone(CaveHorrorZone.ZONE_ID))
    story_zones.append(get_zone(CaveHorrorSaveZone.ZONE_ID))  # save point

    story_zones.append(get_zone(UndergrowthZone.ZONE_ID))
    story_zones.append(get_zone(MedusaLairZone.ZONE_ID))

    story_zones.append(get_zone(EpilogueZone.ZONE_ID))

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

            bp.geo_color = get_zone(zone_id).get_color()

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
                        bp.save_station = (x, y, get_zone(zone_id).get_save_id())
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

        except Exception as e:
            print("failed to load " + str(filename))
            raise e


def build_world_for_save_id(save_id):
    zone_id = get_zone_id_for_save_id(save_id)
    if zone_id is None:
        print("ERROR: unrecognized save_id, starting at very beginning: \"{}\"".format(save_id))
        return build_world(first_zone_id())
    else:
        return build_world(zone_id, spawn_at_save_point=save_id)


def build_world(zone_id, spawn_at_save_point=None, spawn_at_door_with_zone_id=None):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))

    zone = _ALL_ZONES[zone_id]
    gs.get_instance().prepare_for_new_zone(zone)
    music.play_song(zone.get_music_id())

    if not debug.never_show_tutorials():
        from src.game.tutorial import TutorialFactory
        tutorials = TutorialFactory.get_tutorials_for_level(zone.get_level(), non_complete_only=True)
        gs.get_instance().set_inactive_tutorials(tutorials)
    else:
        gs.get_instance().set_inactive_tutorials([])

    gs.get_instance().set_active_tutorial(None)

    w = zone.build_world()
    w.set_geo_color(zone.get_color())
    w.flush_new_entity_additions()
    w.set_bg_color(zone.get_bg_color())

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        special_spawn_pos = None

        if spawn_at_save_point is not None:
            for e in w.all_entities(onscreen=False):
                if e.is_save_station() and e.get_save_id() == spawn_at_save_point:
                    # TODO - animation for leaving the machine?
                    e.already_used = True
                    special_spawn_pos = w.to_grid_coords(*e.center())

        elif spawn_at_door_with_zone_id is not None:
            for e in w.all_entities(onscreen=False):
                if e.is_exit() and e.get_zone() == spawn_at_door_with_zone_id:
                    special_spawn_pos = w.to_grid_coords(*e.center())

        if special_spawn_pos is not None:
            if w.is_solid(*special_spawn_pos):
                special_spawn_pos = (special_spawn_pos[0], special_spawn_pos[1] + 1)

                if not w.is_solid(*special_spawn_pos):
                    spawn_xy = w.cell_center(*special_spawn_pos)
                    p.set_center(*spawn_xy)
                else:
                    print("ERROR: special spawn positions ({}, {}) and ({}, {}) were blocked!".format(
                        special_spawn_pos[0], special_spawn_pos[1] - 1, special_spawn_pos[0], special_spawn_pos[1]
                    ))

        grid_xy = w.to_grid_coords(*p.center())
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)
        gs.get_instance().set_camera_center_in_world(*p.center())

    return w


def get_zone_name(zone_id, or_else=None):
    if zone_id in _ALL_ZONES:
        return _ALL_ZONES[zone_id].get_name()
    else:
        return or_else


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

    def get_save_id(self):
        return self.get_id()


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
    def _tile_grid_to_world(zone_id, level, t_grid, bonus_decorations=()):
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

        # distribute bonus decorations into valid positions
        if len(bonus_decorations) > 0:
            bonus_dec_list = list(bonus_decorations)
            for x in range(0, w):
                for y in range(0, h):
                    if t_grid.get(x, y) == worldgen2.TileType.FLOOR and t_grid.get(x, y-1) == worldgen2.TileType.WALL:
                        random.shuffle(bonus_dec_list)
                        for type_and_rate in bonus_dec_list:
                            if random.random() < type_and_rate[1]:
                                dec_ent = decoration.DecorationFactory.get_decoration(level, dec_type=type_and_rate[0])
                                world.add(dec_ent, gridcell=(x, y - 1))
                                break

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

            except Exception as e:
                print("WARN: failed to generate tile grid {} time(s): level={}, dims={}".format(i+1, level, dims))
                if debug.is_dev():
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
    def generate_new_world(zone, dims=None, min_dims=(3, 3), max_dims=(3, 3), bonus_decorations=()):
        if dims is not None:
            grid_dims = dims
        else:
            grid_dims = (random.choice([x for x in range(min(max_dims[0], min_dims[0]), max_dims[0] + 1)]),
                         random.choice([y for y in range(min(min_dims[1], max_dims[1]), max_dims[1] + 1)]))

        t_grid = ZoneBuilder.generate_tile_grid(zone.get_id(), zone.get_level(), dims=grid_dims)

        print("INFO: generated world: zone={}, dims={}, level={}".format(zone.get_id(), grid_dims, zone.get_level()))

        if debug.is_dev():
            print(t_grid)
            print("\n")

        w = ZoneBuilder._tile_grid_to_world(zone.get_id(), zone.get_level(), t_grid,
                                            bonus_decorations=bonus_decorations)
        w.set_geo_color(zone.get_color())

        return w

    @staticmethod
    def make_generated_zone(level, name, zone_id, dims=None, min_dims=(3, 3), max_dims=(3, 3),
                            music_id=None, geo_color=None, conversation_ids=None,
                            bonus_decorations=()):
        zone = Zone(name, level)
        zone.ZONE_ID = zone_id
        zone.zone_id = zone_id

        if conversation_ids is not None:
            zone.conversation_ids = conversation_ids
        if music_id is not None:
            zone.music_id = music_id
        if geo_color is not None:
            zone.geo_color = geo_color

        # making sure i didn't screw up this param
        if len(bonus_decorations) > 0:
            for type_and_rate in bonus_decorations:
                if (not isinstance(type_and_rate[0], str)
                        or type_and_rate[1] < 0 or type_and_rate[1] > 1):
                    raise ValueError("invalid bonus decoration: {}".format(type_and_rate))

        zone.build_world = lambda: ZoneBuilder.generate_new_world(zone, dims=dims,
                                                                  min_dims=min_dims, max_dims=max_dims,
                                                                  bonus_decorations=bonus_decorations)
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


class QuietInlet(Zone):

    ZONE_ID = "quiet_inlet"

    def __init__(self):
        Zone.__init__(self, "Quiet Inlet", 0, filename="quiet_inlet.png")
        self._sign_color = (225, 230, 150)
        self._web_color = (255, 255, 100)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        spawn_pos = bp.player_spawn
        w = bp.build_world()

        sleep_box = entities.PlayerSleepAnimationBox(spawn_pos)
        w.add(sleep_box)

        sleep_box.update(w)   # XXX so that the player's sprite is set instantly

        if self._sign_color in unknowns:
            pos = unknowns[self._sign_color][0]
            text = "It's an epitaph. The words are too faded to read."
            sign = decoration.DecorationFactory.get_sign(self.get_level(), sign_text=text, no_sprite=True)
            w.add(sign, gridcell=(pos[0], pos[1] - 1))

        if self._web_color in unknowns:
            for web_pos in unknowns[self._web_color]:
                web_ent = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_WEB, self.get_level())
                w.add(web_ent, gridcell=(web_pos[0], web_pos[1] - 1))

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.WHITE


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
            mushroom_entity = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.MUSHROOM, m_sprite, pos[0], pos[1],
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
                mushroom_entity = entities.DecorationEntity.wall_decoration(None,  spriteref.wall_decoration_switches,
                                                                            pos[0], pos[1],
                                                                            interact_dialog=unlock_dialog)
            else:
                if i == (hidden_switch_idx + 1) % len(sp_mushrooms):
                    text = "there's nothing interesting here. it's just a large cluster of mushrooms."
                else:
                    text = "this won't help us open the door. it's just a large cluster of mushrooms."
                mushroom_entity = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.MUSHROOM,
                                                                            m_sprite, pos[0], pos[1],
                                                                            interact_dialog=dialog.PlayerDialog(text))
            w.add(mushroom_entity)

        for pos in unknowns[DesolateCaveZone.RAKE_COLOR]:
            text = "it's a rake."
            rake_entity = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.RAKE,
                                                                    spriteref.wall_decoration_rake,
                                                                    pos[0], pos[1], interact_dialog=dialog.PlayerDialog(text))
            w.add(rake_entity)

        for key in unknowns:
            if key in DesolateCaveZone.WALL_SIGNS:
                pos = unknowns[key][0]
                hover_text = DesolateCaveZone.WALL_SIGNS[key][0]
                dialog_text = Utils.listify(DesolateCaveZone.WALL_SIGNS[key][1])
                d = dialog.Dialog.link_em_up([dialog.PlayerDialog(x) for x in dialog_text])

                sign = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.SIGN,
                                                                 spriteref.wall_decoration_sign, pos[0], pos[1],
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
                ent = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.MUSHROOM)
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


class VentilationZone(Zone):

    ZONE_ID = "vents"

    def __init__(self):
        Zone.__init__(self, "The Vents", 10, filename="the_vents.png")
        self.skelekid_pos = (225, 170, 170)
        self.mary_pos = (255, 171, 171)
        self.grok_pos = (255, 172, 172)

        self._mary_pos_on_load = (225, 171, 172)

        self.sign_pos = (255, 175, 150)
        self.fan_wall_pos = (0, 170, 170)

        self.chest_pos = (255, 0, 230)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        from_load = gs.get_instance().get_loaded_from_save_id() == self.get_save_id()

        if not from_load:
            skelekid_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.SKELEKID, npc.Conversations.SKELEKID_GROK_AND_MARY_AT_VENTS)
            grok_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.GROK, skelekid_npc.get_uid())
            mary_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.MARY_SKELLY, skelekid_npc.get_uid())

            if self.skelekid_pos in unknowns:
                w.add(skelekid_npc, gridcell=unknowns[self.skelekid_pos][0])

                if self.grok_pos in unknowns:
                    w.add(grok_npc, gridcell=unknowns[self.grok_pos][0])

                if self.mary_pos in unknowns:
                    w.add(mary_npc, gridcell=unknowns[self.mary_pos][0])
        else:
            mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_AT_VENTS_AFTER_LOAD)  # TODO replace
            if self._mary_pos_on_load in unknowns:
                w.add(mary_npc, gridcell=unknowns[self._mary_pos_on_load][0])

        if self.chest_pos in unknowns:
            chest_xy = unknowns[self.chest_pos][0]

            # chest is already opened if you loaded into the zone
            chest_ent = entities.ChestEntity(chest_xy[0], chest_xy[1], is_open=from_load)
            w.add(chest_ent)

        if self.sign_pos in unknowns:
            text = "WARNING: Dangerous Fumes!"

            sign_ent = decoration.DecorationFactory.get_sign(self.get_level(), sign_text=text)
            pos = unknowns[self.sign_pos][0]
            w.add(sign_ent, gridcell=(pos[0], pos[1] - 1))

        if self.fan_wall_pos in unknowns:
            for wall_pos in unknowns[self.fan_wall_pos]:
                fan_dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.FAN)
                w.add(fan_dec, gridcell=(wall_pos[0], wall_pos[1]))

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_BLUE

    def get_save_id(self):
        return "pre_robo_fight"


class RoboLairZone(Zone):

    ZONE_ID = "robo_lair"

    def __init__(self):
        Zone.__init__(self, "Server Room", 11, filename="robo_lair.png")
        self._robo_color = (255, 170, 170)

        self._mary_spawn_1 = (255, 170, 150)
        self._mary_spawn_2 = (255, 170, 151)

        self._skelekid_spawn_1 = (255, 171, 150)
        self._skelekid_spawn_2 = (255, 171, 151)

        self._grok_spawn_1 = (225, 172, 150)
        self._grok_spawn_2 = (225, 172, 151)

        self._robo_console_left = (0, 130, 150)
        self._robo_console = (0, 170, 150)
        self._robo_console_right = (0, 190, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        robo_pos = unknowns[self._robo_color][0]
        robo_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_ROBO, self.get_level())

        # end the song when the boss dies, for maximum drama
        robo_entity.add_special_death_hook("end_song", lambda _w, _e: music.play_song(self.get_music_id()))

        w.add(robo_entity, gridcell=robo_pos)

        pre_fight_npcs = self._gen_npcs(True)
        if all([(color_id in unknowns) for color_id in pre_fight_npcs]):
            for color_id in pre_fight_npcs:
                npc_ent = pre_fight_npcs[color_id]
                grid_pos = unknowns[color_id][0]
                w.add(npc_ent, gridcell=grid_pos)

                # remove npc when boss dies
                death_hook = _get_remove_entity_on_death_hook(npc_ent.get_uid(), show_explosion=True)
                robo_entity.add_special_death_hook("remove pre-fight npc {}".format(npc_ent.get_npc_id()), death_hook)

        post_fight_npcs = self._gen_npcs(False)
        if all([(color_id in unknowns) for color_id in post_fight_npcs]):
            for color_id in post_fight_npcs:
                npc_ent = post_fight_npcs[color_id]
                grid_pos = unknowns[color_id][0]
                w.add(npc_ent, gridcell=grid_pos)

        if self._robo_console_left in unknowns:
            pos = unknowns[self._robo_console_left][0]
            dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.ROBO_LEFT)
            w.add(dec, gridcell=pos)

        if self._robo_console_right in unknowns:
            pos = unknowns[self._robo_console_right][0]
            dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.ROBO_RIGHT)
            w.add(dec, gridcell=pos)

        if self._robo_console in unknowns:
            pos = unknowns[self._robo_console][0]
            dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.ROBO_CONSOLE)

            def _get_robo_sprites(_ent, _world):
                if gs.get_instance().dialog_manager().is_active():
                    dia = gs.get_instance().dialog_manager().get_dialog()
                    if dia is not None:
                        # we want to show the active sprites if robo is talking
                        # or if it's between his first and last sections of dialog.
                        after_first = False
                        before_last = False
                        t = dia
                        while t is not None:
                            if t.get_speaker_id() == npc.NpcID.ROBO:
                                after_first = True
                                break
                            t = t.get_prev()

                        if after_first:
                            t = dia
                            while t is not None:
                                if t.get_speaker_id() == npc.NpcID.ROBO:
                                    return [spriteref.wall_decoration_robo_console_skull]
                                t = t.get_next()

                return [spriteref.wall_decoration_robo_console_empty]

            dec.set_sprite_provider(_get_robo_sprites)

            w.add(dec, gridcell=pos)

        return w

    def _gen_npcs(self, pre_fight):
        if pre_fight:
            mary_pre = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.PRE_ROBO_FIGHT)
            skelekid_pre = npc.NpcFactory.gen_linked_npc(npc.NpcID.SKELEKID, mary_pre.get_uid())
            grok_pre = npc.NpcFactory.gen_linked_npc(npc.NpcID.GROK, mary_pre.get_uid())

            return {
                self._mary_spawn_1: mary_pre,
                self._skelekid_spawn_1: skelekid_pre,
                self._grok_spawn_1: grok_pre
            }
        else:
            grok_post = npc.NpcFactory.gen_convo_npc(npc.NpcID.GROK, npc.Conversations.POST_ROBO_FIGHT)
            mary_post = npc.NpcFactory.gen_linked_npc(npc.NpcID.MARY_SKELLY, grok_post.get_uid())
            skelekid_post = npc.NpcFactory.gen_linked_npc(npc.NpcID.SKELEKID, grok_post.get_uid())

            return {
                self._grok_spawn_2: grok_post,
                self._mary_spawn_2: mary_post,
                self._skelekid_spawn_2: skelekid_post
            }

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


class UndergrowthZone(Zone):

    ZONE_ID = "undergrowth"

    def __init__(self):
        Zone.__init__(self, "Undergrowth", 15, filename="undergrowth_zone.png")
        self._exit_doors = (255, 175, 80)
        self._skull_rack_color = (255, 200, 100)

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

        already_decorated = set()

        if self._skull_rack_color in unknowns:
            for xy in unknowns[self._skull_rack_color]:
                dec = decoration.DecorationFactory.get_decoration(self.get_level(),
                                                                  decoration.DecorationTypes.SKULL_RACK)
                pos = (xy[0], xy[1] - 1)
                w.add(dec, gridcell=pos)
                already_decorated.add(xy)

        for xy in mushroom_positions:
            if xy not in already_decorated:
                mushroom_sprite = random.choice(spriteref.wall_decoration_mushrooms)
                mushroom_entity = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.MUSHROOM,
                                                                            mushroom_sprite, xy[0], xy[1])
                w.add(mushroom_entity)

        return w

    def is_boss_zone(self):
        return False

    def get_color(self):
        return colors.LIGHT_PURPLE

    def get_music_id(self):
        return music.Songs.UNEARTHED


class MedusaLairZone(Zone):

    ZONE_ID = "medusa_lair"

    def __init__(self):
        Zone.__init__(self, "The Abyss", 15, filename="medusa_lair.png")
        self._medusa_color = (255, 170, 170)
        self._doctor_npc_color = (255, 170, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        medusa_pos = unknowns[self._medusa_color][0]

        mushroom_positions = _mushroomify_blueprint(bp, medusa_pos)

        w = bp.build_world()

        medusa_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_MEDUSA, self.get_level())
        w.add(medusa_entity, gridcell=medusa_pos)

        doctor_position = unknowns[self._doctor_npc_color][0]
        doctor_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.DOCTOR, npc.Conversations.DOCTOR_PRE_MEDUSA)
        w.add(doctor_npc, gridcell=doctor_position)

        for xy in mushroom_positions:
            mushroom_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            mushroom_entity = entities.DecorationEntity.wall_decoration(decoration.DecorationTypes.MUSHROOM,
                                                                        mushroom_sprite, xy[0], xy[1])
            w.add(mushroom_entity)

        return w

    def is_boss_zone(self):
        return True

    def get_color(self):
        return colors.LIGHT_PURPLE

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_special_door_music_id(self):
        return music.Songs.MEDUSA_THEME


class EpilogueZone(Zone):

    ZONE_ID = "epilogue"

    def __init__(self):
        Zone.__init__(self, "Epilogue", 15, filename="epilogue.png")
        self._doc_color = (255, 170, 150)
        self._scorp_color = (255, 171, 150)
        self._mary_color = (255, 172, 150)
        self._mathilda_color = (255, 173, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        w = bp.build_world()

        if self._doc_color in unknowns and self._scorp_color in unknowns:
            doc_pos = unknowns[self._doc_color][0]
            doc_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.DOCTOR, npc.Conversations.DOCTOR_SCORP_EPILOGUE)
            w.add(doc_npc, gridcell=doc_pos),

            scorp_pos = unknowns[self._scorp_color][0]
            scorp_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.WANDERER, npc.Conversations.SCORP_EPILOGUE)
            w.add(scorp_npc, gridcell=scorp_pos)

        if self._mary_color in unknowns and self._mathilda_color in unknowns:
            mary_pos = unknowns[self._mary_color][0]
            mathilda_pos = unknowns[self._mathilda_color][0]

            mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_MATHILDA_EPILOGUE)
            mathilda_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.MATHILDA_INCOMPLETE, mary_npc.get_uid())

            w.add(mary_npc, gridcell=mary_pos)
            w.add(mathilda_npc, gridcell=mathilda_pos)

        return w

    def get_color(self):
        return colors.LIGHT_PURPLE

    def get_music_id(self):
        return music.Songs.MEDUSA_THEME


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_horror_lair"

    def __init__(self):
        Zone.__init__(self, "The Vault", 15, filename="cave_horror.png")
        self._tree_color = (255, 170, 170)
        self._husk_color = (255, 194, 194)
        self._bounds_color = (255, 190, 0)
        self._rake_color = (255, 220, 175)
        self._bucket_color = (225, 200, 0)
        self._mushroom_colors = [(255, 175, 100), (225, 175, 100)]  # mushrooms for varying floor types
        self._skull_rack_colors = [(255, 200, 100), (225, 200, 100)]

        self._mary_spawn_1 = (255, 172, 150)
        self._mary_spawn_2 = (255, 172, 151)

        self._doctor_spawn = (255, 173, 151)

    def build_decorations(self, w, unknowns):
        if self._rake_color in unknowns:
            for xy in unknowns[self._rake_color]:
                dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.RAKE)
                w.add(dec, gridcell=(xy[0], xy[1] - 1))

        if self._bucket_color in unknowns:
            for xy in unknowns[self._bucket_color]:
                dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.BUCKET)
                w.add(dec, gridcell=(xy[0], xy[1] - 1))

        for mushroom_color in self._mushroom_colors:
            if mushroom_color in unknowns:
                for xy in unknowns[mushroom_color]:
                    dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.MUSHROOM,
                                                                      with_dialog=None)
                    w.add(dec, gridcell=(xy[0], xy[1] - 1))

        for skull_rack_color in self._skull_rack_colors:
            if skull_rack_color in unknowns:
                for xy in unknowns[skull_rack_color]:
                    d_text = "Their collective groans overwhelm you. You can't make out a word."
                    dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.SKULL_RACK,
                                                                      with_dialog=d_text)
                    w.add(dec, gridcell=(xy[0], xy[1] - 1))

    def build_boss_fight_stuff(self, w, unknowns, special_door_pos):
        bounds_rect = Utils.get_rect_containing_points(unknowns[self._bounds_color], inclusive=True)

        inital_husk_spawns = unknowns[self._husk_color]

        tree_pos = unknowns[self._tree_color][0]
        tree_entity = self.gen_tree_entity(bounds_rect, inital_husk_spawns, min_n_husks=2)

        # end the song when the boss dies, for maximum drama
        tree_entity.add_special_death_hook("end_song", lambda _w, _e: music.play_song(self.get_music_id()))

        def do_death_animations(_world, _ent):
            ent_center = _ent.get_render_center(ignore_perturbs=True)
            corpse_ent = entities.AnimationEntity(ent_center[0], ent_center[1], spriteref.CaveHorror.cave_horror_dead,
                                                  duration=30, layer_id=spriteref.ENTITY_LAYER, scale=1)
            corpse_ent.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
            corpse_ent.set_shadow_sprite(None)

            # XXX wowza this is hacky, but it needs to be below everything else
            corpse_ent.get_depth = lambda: 10_000

            _world.add(corpse_ent)

            ent_cell = _world.to_grid_coords(*_ent.center())
            left_explosion_pos = _world.cell_center(ent_cell[0] - 2, ent_cell[1])
            center_explosion_pos = _world.cell_center(ent_cell[0], ent_cell[1])
            right_explosion_pos = _world.cell_center(ent_cell[0] + 2, ent_cell[1])

            _world.show_explosion(left_explosion_pos[0], left_explosion_pos[1], 18, color=colors.LIGHT_GRAY,
                                  offs=(0, -_world.cellsize() * 0.5), scale=3)
            _world.show_explosion(right_explosion_pos[0], right_explosion_pos[1], 24, color=colors.LIGHT_GRAY,
                                  offs=(0, -_world.cellsize() * 0.5), scale=3)
            _world.show_explosion(center_explosion_pos[0], center_explosion_pos[1], 40, color=colors.WHITE,
                                  offs=(0, -_world.cellsize() * 1), scale=5)

        tree_entity.add_special_death_hook("do_death_animations", do_death_animations)

        w.add(tree_entity, gridcell=tree_pos)

        import src.world.cameramodifiers as cameramodifiers
        camera_shift_rect = Utils.rect_expand(bounds_rect, left_expand=1)  # gotta encompass the door's square too
        camera_shifter = cameramodifiers.SnapToEntityModifier(camera_shift_rect, tree_entity, fade_out_time=30)
        w.add_camera_modifier(camera_shifter)

        tree_uid = tree_entity.get_uid()

        special_door = w.get_door_in_cell(*special_door_pos)
        if special_door is None:
            raise ValueError("there's no door in the cell: {}".format(special_door_pos))

        def entry_door_action(_world):
            tree_ent_in_world = w.get_entity(tree_uid, onscreen=False)
            if tree_ent_in_world is not None:
                # want it to wait a few turns before it starts summoning
                import src.game.statuseffects as statuseffects
                tree_ent_in_world.get_actor_state().try_to_add_status_effect(statuseffects.StatusEffectTypes.SUMMON_SICKNESS, 2)

        special_door.add_special_open_hook("cave_horror_main_door", entry_door_action)

        return tree_entity

    def build_npc_stuff(self, w, unknowns, tree_entity):
        pre_fight_npcs = self._gen_npcs(True)
        if all([color_id in unknowns for color_id in pre_fight_npcs]):
            for color_id in pre_fight_npcs:
                npc_for_id = pre_fight_npcs[color_id]
                npc_pos = unknowns[color_id][0]
                w.add(npc_for_id, gridcell=npc_pos)

                # remove npc when boss dies
                death_hook = _get_remove_entity_on_death_hook(npc_for_id.get_uid(), show_explosion=True)
                tree_entity.add_special_death_hook("remove pre-fight npc: {}".format(npc_for_id.get_npc_id()),
                                                   death_hook)

        post_fight_npcs = self._gen_npcs(False)
        if all([color_id in unknowns for color_id in post_fight_npcs]):
            for color_id in post_fight_npcs:
                npc_for_id = post_fight_npcs[color_id]
                npc_pos = unknowns[color_id][0]
                w.add(npc_for_id, gridcell=npc_pos)

    def _gen_npcs(self, pre_fight):
        if pre_fight:
            mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY_WITH_HEAD, npc.Conversations.MARY_PRE_CAVE_HORROR)

            return {
                self._mary_spawn_1: mary_npc
            }
        else:
            doctor_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.DOCTOR, npc.Conversations.MARY_DOCTOR_POST_CAVE_HORROR)
            mary_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.MARY_SKELLY_WITH_HEAD, doctor_npc.get_uid())

            return {
                self._mary_spawn_2: mary_npc,
                self._doctor_spawn: doctor_npc
            }

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        self.build_decorations(w, unknowns)

        if len(bp.music_doors) != 1:
            raise ValueError("should be exactly one special door in zone: {}".format(len(bp.music_doors)))
        special_door_pos = list(bp.music_doors.keys())[0]

        tree_entity = self.build_boss_fight_stuff(w, unknowns, special_door_pos)

        self.build_npc_stuff(w, unknowns, tree_entity)

        return w

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


class CaveHorrorZonePeaceful(CaveHorrorZone):

    ZONE_ID = "peaceful_end"

    def __init__(self):
        CaveHorrorZone.__init__(self)

    def _build_tree_animation_ent(self, grid_pos, world, arena_bounds):
        grid_center = world.cell_center(grid_pos[0], grid_pos[1])
        anim_cx, anim_cy = grid_center

        anim_cy += enemies.TEMPLATE_CAVE_HORROR.get_sprite_offset()[1]

        anim_sprites = spriteref.CaveHorror.cave_horror_idle

        anim_ent = entities.AnimationEntity(anim_cx, anim_cy, anim_sprites,
                                            duration=60, layer_id=spriteref.ENTITY_LAYER, scale=1,
                                            anim_rate=enemies.TEMPLATE_CAVE_HORROR.get_idle_anim_rate())

        anim_ent.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
        anim_ent.set_shadow_sprite(None)
        anim_ent.set_visible_in_darkness(True)

        # needs to be below everything else
        anim_ent.get_depth = lambda: 10_000

        world.add(anim_ent)

        import src.game.stats as stats
        light_level = enemies.TEMPLATE_CAVE_HORROR.get_stats().stat_value(stats.StatTypes.LIGHT_LEVEL)
        light_emitter = entities.LightEmitterAnimation(grid_center[0], grid_center[1], 60, light_level, light_level)
        light_emitter.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
        world.add(light_emitter)

        import src.world.cameramodifiers as cameramodifiers
        camera_shift_rect = Utils.rect_expand(arena_bounds, left_expand=1)  # gotta encompass the door's square too
        camera_shifter = cameramodifiers.SnapToEntityModifier(camera_shift_rect, light_emitter, fade_out_time=30)
        world.add_camera_modifier(camera_shifter)

        return anim_ent

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())

        new_locked_door_positions = []
        for sensor_door_pos in bp.sensor_doors:
            new_locked_door_positions.append(sensor_door_pos)

        # sensors will become normal doors
        bp.sensor_doors.clear()

        w = bp.build_world()

        # XXX if we aren't careful about adding new sensor doors,
        # we could easily create a softlock here
        for door_pos in new_locked_door_positions:
            door_ent = w.get_door_in_cell(*door_pos)
            if door_ent is not None:
                door_ent.set_locked(True)

        self.build_decorations(w, unknowns)

        bounds_rect = Utils.get_rect_containing_points(unknowns[self._bounds_color], inclusive=True)

        top_3_positions = [
            (bounds_rect[0] + bounds_rect[2] // 2 - 1, bounds_rect[1]),
            (bounds_rect[0] + bounds_rect[2] // 2, bounds_rect[1]),
            (bounds_rect[0] + bounds_rect[2] // 2 + 1, bounds_rect[1]),
        ]

        anim_trigger_dialog = dialog.Dialog("Our conquest has only just begun.")

        d = [dialog.Dialog("My flesh has many memories of you."),
             dialog.Dialog("Memories of... mercy."),
             dialog.Dialog("You didn't harm a single one of my vestiges on your journey here, even to protect yourself."),
             dialog.Dialog("Thank you for this. Your love has been felt, and it will be repaid."),
             # dialog.Dialog("We aren't so different, you and I."),  # TODO - this is a bit on-the-nose
             # dialog.Dialog("We're both born of fungus and flesh. Did you know that?"),
             # dialog.Dialog("That's why I couldn't bend you. Your mind is strong - and already shaped by a strand other than my own."),
             dialog.Dialog("I have memories... of them entombing you, long ago."),
             dialog.Dialog("They were fearful of you - and what you might become."),
             dialog.Dialog("You hold great power. And yet, you came in peace."),
             dialog.Dialog("Soon we'll become one. Two equals - enjoined."),
             dialog.Dialog("Rest, my child, and dream deeply."),
             anim_trigger_dialog,
             dialog.Dialog("...")
             ]

        dia = dialog.Dialog.link_em_up(d)

        for pos in top_3_positions:
            absorb_box = entities.DialogTriggerBox(dia, pos, delay=15)
            w.add(absorb_box)

        self._build_tree_animation_ent(unknowns[self._tree_color][0], w, bounds_rect)

        def do_absorb_anim_and_game_win(_evt, _w):
            print("INFO: starting peaceful end-of-game animation sequence")

            get_down_duration = 90
            lay_duration = 60
            grab_duration = 30
            absorb_duration = 120

            total_anim_duration = (get_down_duration + lay_duration + grab_duration + absorb_duration)

            p = _w.get_player()
            if p is not None:
                p.set_sprite_override(spriteref.invisible_pixel)
                p.set_shadow_sprite_override(spriteref.invisible_pixel)  # shadows are baked into the sprites
                p.set_visually_held_item_override(False)

                p_pos = _w.to_grid_coords(*p.center())
                cell_center = _w.cell_center(*p_pos)
                anim_ent = entities.PlayerAbsorbAnimation(cell_center[0], cell_center[1],
                                                          get_down_duration=get_down_duration,
                                                          lay_duration=lay_duration,
                                                          grab_duration=grab_duration,
                                                          absorb_duration=absorb_duration)
                _w.add(anim_ent)

            delay_between_anim_and_fade = 150

            fade_duration = constants.STANDARD_FADE_DURATION
            gs.get_instance().do_fade_sequence(0.0, 1.0, fade_duration,
                                               start_delay=total_anim_duration + delay_between_anim_and_fade,
                                               end_delay=10)  # buffer

            delay_til_game_end = total_anim_duration + delay_between_anim_and_fade + fade_duration

            gs.get_instance().pause_world_updates(delay_til_game_end + 10)  # just some buffer

            game_win_evt = events.GameWinEvent()
            gs.get_instance().add_event(game_win_evt, delay=delay_til_game_end)

        anim_listener = events.EventListener(do_absorb_anim_and_game_win,
                                             events.EventType.DIALOG_EXIT,
                                             lambda evt: evt.get_uid() == anim_trigger_dialog.get_uid(),
                                             scope=events.EventListenerScope.ZONE,
                                             single_use=False)  # no softlock pls
        gs.get_instance().add_trigger(anim_listener)

        return w


class TombtownZone(Zone):

    ZONE_ID = "tomb_town"

    def __init__(self):
        Zone.__init__(self, "Tombtown", 3, filename="town.png", bg_color=colors.BLACK)

        self.music_id = music.Songs.SILENCE
        self.fight_music_id = music.Songs.ARACHNID
        self.post_fight_music_id = music.Songs.get_basic_caves_song()

    WALL_SIGNS = {
        (255, 172, 150): [" - Outpost 53 - \nWelcome to Tombtown!"],
        (255, 173, 150): ["Mary's Adventure Tours"],
        (255, 174, 150): ["Beanskull's Tomato Grove"],
        (255, 179, 150): ["Mathilda's Blade and Sword"],
        (255, 175, 150): ["Notice Board:\n"
                          "Tax season is coming up! Late fees WILL be enforced."],
        (255, 176, 150): ["Tombtown City Hall"],
        (205, 177, 150): ["Tombtown Treasury\n" +
                          "Absolutely NO Unauthorized Access"],
        (255, 178, 150): ["P. Patches:         20,354.76m\n" +
                          "Ms. & Ms. Skelly:      702.10m\n" +
                          "B. Skull:               37.80m\n"]
    }

    BEANSKULL = (255, 170, 255)
    MAYOR = (205, 171, 255)
    MARY = (255, 172, 255)
    MARY_2 = (255, 177, 255)
    GROK = (255, 173, 255)

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

        dec_type_lookup = {TombtownZone.MUSHROOMS: (decoration.DecorationTypes.MUSHROOM, None),
                           TombtownZone.TOMATO_PLANTS: (decoration.DecorationTypes.PLANT, "It's a tomato plant. It looks well-maintained."),
                           TombtownZone.RAKE: (decoration.DecorationTypes.RAKE, None),
                           TombtownZone.WORKBENCH: (decoration.DecorationTypes.WORKBENCH, None),
                           TombtownZone.BONE_DECORATIONS: (decoration.DecorationTypes.BONES, "It appears to be a memorial plate of some kind. The bones are made from stone."),
                           TombtownZone.BUCKET: (decoration.DecorationTypes.BUCKET, None)}

        mary_pre_fight_ent_uid = None
        mary_pos_2 = None

        spider_ent = None

        for key in unknowns:
            if key in TombtownZone.WALL_SIGNS:
                pos = unknowns[key][0]
                sign = decoration.DecorationFactory.get_sign(self.get_level(), sign_text=TombtownZone.WALL_SIGNS[key])
                w.add(sign, gridcell=(pos[0], pos[1] - 1))

            elif key in dec_type_lookup:
                for pos in unknowns[key]:
                    dec_type, dec_desc = dec_type_lookup[key]
                    if dec_desc is None:
                        dec_entity = decoration.DecorationFactory.get_decoration(self.get_level(), dec_type)  # default description
                    else:
                        dec_entity = decoration.DecorationFactory.get_decoration(self.get_level(), dec_type, with_dialog=dec_desc)
                    w.add(dec_entity, gridcell=(pos[0], pos[1] - 1))

            elif key == TombtownZone.BEANSKULL:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.BEANSKULL, npc.Conversations.BEANSKULL_INTRO)
                w.add(e, gridcell=unknowns[key][0])
            elif key == TombtownZone.MAYOR:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.MAYOR, npc.Conversations.MAYOR_INTRO)
                w.add(e, gridcell=unknowns[key][0])
            elif key == TombtownZone.MARY:
                e = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_SKELLY_PRE_SPIDER_FIGHT)
                w.add(e, gridcell=unknowns[key][0])
                mary_pre_fight_ent_uid = e.get_uid()
            elif key == TombtownZone.MARY_2:
                mary_pos_2 = unknowns[key][0]
            elif key == TombtownZone.SPIDER_BOSS:
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


class TombtownSaveZone(Zone):

    ZONE_ID = "town_save"

    def __init__(self):
        Zone.__init__(self, "Tombtown", 3, filename="town_save.png")

        self._rake_id = (255, 220, 115)
        self._mary_id = (255, 172, 255)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        if self._rake_id in unknowns:
            for pos in unknowns[self._rake_id]:
                sign = decoration.DecorationFactory.get_decoration(self.get_level(), 
                                                                   dec_type=decoration.DecorationTypes.RAKE,
                                                                   with_dialog=None)
                w.add(sign, gridcell=(pos[0], pos[1] - 1))

        if self._mary_id in unknowns:
            mary_pos = unknowns[self._mary_id][0]

            if gs.get_instance().get_loaded_from_save_id() == self.get_save_id():
                if gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT) > 0:
                    mary_ent = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_POST_CLONING_WITH_DEATHS)
                else:
                    mary_ent = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_POST_CLONING_NO_DEATHS_YET)
            else:
                mary_ent = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_CLONING_EXPLANATION)

                def _already_did_clone_no_deaths(world, interact_count):
                    # XXX so that the hovering "!" doesn't pop until the end of the cloning animation
                    if gs.get_instance().world_updates_paused():
                        return False

                    death_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT)
                    cp_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.CHECKPOINT_COUNT)
                    return death_count == 0 and cp_count > 0

                mary_ent.add_conditional_conversation(_already_did_clone_no_deaths, npc.Conversations.MARY_POST_CLONING_NO_DEATHS_YET)

            w.add(mary_ent, gridcell=mary_pos)

        return w

    def get_save_id(self):
        return "post_tombtown"

    def get_music_id(self):
        return music.Songs.SILENCE


class CityGateZone(Zone):

    ZONE_ID = "city_gate"

    def __init__(self):
        Zone.__init__(self, "City Gate", 7, filename="city_gate.png")
        self._mary_npc = (255, 172, 150)
        self._head_npc = (255, 173, 150)

        self._mary_npc_from_load = (225, 172, 150)

        self._gate_left = (255, 234, 150)
        self._gate_right = (255, 235, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        dec_lookup = {
            self._gate_left: decoration.DecorationTypes.GATE_LEFT,
            self._gate_right: decoration.DecorationTypes.GATE_RIGHT
        }

        from_load = gs.get_instance().get_loaded_from_save_id() == self.get_save_id()
        has_deaths = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT) > 0

        head_pos = None
        mary_pos = None
        mary_pos_from_load = None

        for key in unknowns:
            for pos in unknowns[key]:
                if key in dec_lookup:
                    dec_type = dec_lookup[key]
                    ent = decoration.DecorationFactory.get_decoration(self.get_level(), dec_type)
                    w.add(ent, gridcell=(pos[0], pos[1] - 1))

            if key == self._mary_npc:
                mary_pos = unknowns[key][0]

            if key == self._mary_npc_from_load:
                mary_pos_from_load = unknowns[key][0]

            if key == self._head_npc:
                head_pos = unknowns[key][0]

        if mary_pos is not None and head_pos is not None:
            # XXX there's no way to tell if you loaded from a death or a legitimate quit, so we assume all
            # loads are from death if there have been any deaths thus far.
            if from_load and has_deaths:
                head_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.HEAD, npc.Conversations.HEAD_AT_GATE_AFTER_LOAD)
                w.add(head_npc, gridcell=head_pos)

                mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY, npc.Conversations.MARY_AT_GATE_AFTER_LOAD)
                w.add(mary_npc, gridcell=mary_pos_from_load)
            else:
                head_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.HEAD, npc.Conversations.MARY_AND_HEAD_AT_GATE)
                w.add(head_npc, gridcell=head_pos)

                mary_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.MARY_SKELLY, head_npc.get_uid())
                w.add(mary_npc, gridcell=mary_pos)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_GREEN

    def get_save_id(self):
        return "post_frog_fight"


class RoboSaveZone(Zone):

    ZONE_ID = "robo_save"

    def __init__(self):
        Zone.__init__(self, "Server Room", 11, filename="robo_save.png")
        self.fan_wall_id = (0, 170, 170)
        self.mary_id = (225, 172, 150)
        self.grok_id = (225, 173, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        if self.fan_wall_id in unknowns:
            for wall_pos in unknowns[self.fan_wall_id]:
                fan_dec = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.FAN)
                w.add(fan_dec, gridcell=(wall_pos[0], wall_pos[1]))

        loaded_from_save = gs.get_instance().get_loaded_from_save_id() == self.get_save_id()
        has_deaths = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT) > 0

        # XXX there's no way to tell if you loaded from a death or a legitimate quit, so we assume all
        # loads are from death if there have been any deaths thus far.
        if loaded_from_save and has_deaths:
            mary_pos = None
            if self.mary_id in unknowns:
                mary_pos = unknowns[self.mary_id][0]

            grok_pos = None
            if self.grok_id in unknowns:
                grok_pos = unknowns[self.grok_id][0]

            if mary_pos is not None and grok_pos is not None:
                mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY,
                                                        npc.Conversations.MARY_AND_GROK_AT_SERVER_AFTER_LOAD)
                w.add(mary_npc, gridcell=mary_pos)

                grok_npc = npc.NpcFactory.gen_linked_npc(npc.NpcID.GROK, mary_npc.get_uid())
                w.add(grok_npc, gridcell=grok_pos)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_BLUE

    def get_save_id(self):
        return "post_robo_fight"


class CaveHorrorSaveZone(Zone):

    ZONE_ID = "cave_horror_save"

    def __init__(self):
        Zone.__init__(self, "The Vault", 15, filename="cave_horror_save.png")
        self.mushroom_id = (255, 234, 150)
        self.mary_id = (225, 172, 150)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        if self.mushroom_id in unknowns:
            for pos in unknowns[self.mushroom_id]:
                ent = decoration.DecorationFactory.get_decoration(self.get_level(), decoration.DecorationTypes.MUSHROOM)
                w.add(ent, gridcell=(pos[0], pos[1] - 1))

        loaded_from_save = gs.get_instance().get_loaded_from_save_id() == self.get_save_id()
        has_deaths = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT) > 0

        if loaded_from_save and has_deaths:
            if self.mary_id in unknowns:
                mary_pos = unknowns[self.mary_id][0]
                mary_npc = npc.NpcFactory.gen_convo_npc(npc.NpcID.MARY_SKELLY_WITH_HEAD,
                                                        npc.Conversations.MARY_AT_VAULT_AFTER_LOAD)
                w.add(mary_npc, gridcell=mary_pos)

        return w

    def get_music_id(self):
        return music.Songs.SILENCE

    def get_color(self):
        return colors.LIGHT_RED

    def get_save_id(self):
        return "post_cave_horror"


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
