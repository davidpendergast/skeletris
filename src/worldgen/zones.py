import random
import pygame

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
from src.game.storystate import StoryStateKey
from src.worldgen import worldgen2
import src.game.npc as npc

_FIRST_ZONE_ID = None
_ZONE_TRANSITIONS = {}
_ALL_ZONES = {}

NUM_GENERATED_ZONES = 16

BLACK = (0, 0, 0)
DARK_GREY = (92, 92, 92)


def first_zone_id():
    return _FIRST_ZONE_ID


def first_zone():
    return get_zone(_FIRST_ZONE_ID)


def n_generated_zones():
    return NUM_GENERATED_ZONES


def all_zone_ids():
    return [z for z in _ALL_ZONES]


def get_zone(zone_id):
    return _ALL_ZONES[zone_id]


def _generated_zone_id(level):
    return "generated_{}".format(level)


def get_storyline_zone_id(level):
    if level == 7:
        return FrogLairZone.ZONE_ID
    elif level <= 15:
        return _generated_zone_id(level)
    else:
        return _generated_zone_id(15)


def init_zones():
    _ALL_ZONES.clear()
    for zone_cls in Zone.__subclasses__():
        zone_instance = zone_cls()
        zone_instance.zone_id = zone_cls.ZONE_ID
        make(zone_instance)

    for i in range(0, NUM_GENERATED_ZONES):
        _ALL_ZONES[_generated_zone_id(i)] = ZoneBuilder.build_me_a_zone(i)

    global _FIRST_ZONE_ID
    _FIRST_ZONE_ID = _generated_zone_id(0)


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
    LOCKED_DOOR = (0, 0, 130)
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

            exit_id = get_storyline_zone_id(level + 1)

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
                    elif color == ZoneLoader.LOCKED_DOOR:
                        bp.set_locked_door(x, y)
                    elif color == ZoneLoader.SENSOR_DOOR:
                        bp.set_sensor_door(x, y)
                    elif color == ZoneLoader.RETURN_EXIT:
                        bp.set(x, y, World.FLOOR)
                        bp.return_exit_spawns.append((x, y))
                    elif color == ZoneLoader.EXIT:
                        bp.set(x, y, World.FLOOR)
                        if exit_id in _ALL_ZONES:
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


def build_world(zone_id, spawn_at_door_with_zone_id=None, spawn_at_save_station=False):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))

    zone = _ALL_ZONES[zone_id]
    gs.get_instance().prepare_for_new_zone(zone)
    music.play_song(zone.get_music_id())

    w = zone.build_world()
    w.flush_new_entity_additions()
    w.set_bg_color(zone.get_bg_color())

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        spawn_at_entity = None
        if spawn_at_save_station:
            for e in w.all_entities(onscreen=False):
                if e.is_save_station():
                    spawn_at_entity = e

        elif spawn_at_door_with_zone_id is not None:
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
    print("INFO: created zone: {}".format(zone.get_id()))


class Zone:

    def __init__(self, name, level, filename=None, bg_color=None):
        self.name = name
        self.zone_id = None  # gets set by init_zones()
        self.bg_color = bg_color if bg_color is not None else BLACK
        self.level = level
        self.blueprint_file = filename

    def get_name(self):
        return self.name

    def get_file(self):
        return self.blueprint_file

    def get_id(self):
        return self.zone_id

    def get_level(self):
        return self.level

    def get_bg_color(self):
        return self.bg_color

    def get_music_id(self):
        return music.Songs.SILENCE

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
    def _add_entities_for_tile(level, x, y, tile_type, world):
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
            next_zone_id = get_storyline_zone_id(level + 1)
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
            dec_sprite = random.choice(spriteref.large_decs + spriteref.smol_decs)
            dec_ent = entities.DecorationEntity.wall_decoration([dec_sprite], x, y)
            dec_ent.set_interact_dialog(dialog.Dialog("It seems to be a decoration of some kind."))
            world.add(dec_ent)
        elif tile_type == worldgen2.TileType.SIGN:
            sign_ent = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_sign, x, y)
            sign_ent.set_interact_dialog(dialog.get_sign_dialog(level))
            world.add(sign_ent)

    @staticmethod
    def _tile_grid_to_world(level, t_grid):
        w = t_grid.w()
        h = t_grid.h()
        world = World(t_grid.w(), t_grid.h())

        npc_coords = []

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
                    npc_coords.append((x, y))
                else:
                    ZoneBuilder._add_entities_for_tile(level, x, y, tile_type, world)

        if len(npc_coords) > 0:
            npc_ents = npc.NpcFactory.get_npcs(level, len(npc_coords))
            random.shuffle(npc_coords)
            for i in range(0, len(npc_ents)):
                world.add(npc_ents[i], gridcell=npc_coords[i])

        return world

    @staticmethod
    def generate_tile_grid(level):
        dims = (3, 3)
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

        if len(empty_rooms) < 4:
            raise ValueError("super low number of rooms..?")

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
            print("INFO: falling back to non-fancy start")
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
            if random.random() > 0.05:
                feat = worldgen2.Features.get_random_feature()
                worldgen2.FeatureUtils.try_to_place_feature_into_rect(feat, t_grid, r)

        return t_grid

    @staticmethod
    def generate_new_world(level):
        t_grid = ZoneBuilder.generate_tile_grid(level)

        print("INFO: generated world: level={}".format(level))
        print(t_grid)

        return ZoneBuilder._tile_grid_to_world(level, t_grid)

    @staticmethod
    def build_me_a_zone(level):
        zone = Zone("Depth {}".format(level), level, bg_color=BLACK)
        zone.zone_id = get_storyline_zone_id(level)
        zone.ZONE_ID = zone.zone_id

        zone.build_world = lambda: ZoneBuilder.generate_new_world(level)

        return zone


class DesolateCaveZone(Zone):
    """This is the tutorial / intro zone"""

    ZONE_ID = "desolate_cave"

    MUSHROOM_COLOR = (255, 175, 175)
    MUSHROOM_COLOR_SP = (255, 175, 177)  # these can have a switch behind them
    RAKE_COLOR = (255, 220, 175)
    DIALOG_TRIGGER_1_COLOR = (255, 95, 95)

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

        #bp.enemy_spawns.append((spawn[0] - 5, spawn[1]))
        #bp.enemy_spawns.append((spawn[0] - 7, spawn[1] - 1))
        #bp.enemy_spawns.append((spawn[0] - 6, spawn[1] + 1))

        for n in Utils.neighbors(*spawn, and_diags=True):
            bp.chest_spawns.append((n[0], n[1]))

        w = bp.build_world()

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
                                             cond=lambda ent: isinstance(ent, entities.LockedDoorEntity))
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


class HauntedForestZone1(Zone):

    ZONE_ID = "haunted_forest_1"

    def __init__(self):
        Zone.__init__(self, "Haunted Forest 1", 3, filename="haunted_forest_1.png", bg_color=DARK_GREY)

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

    FROG_SPAWN = (255, 203, 203)

    def __init__(self):
        Zone.__init__(self, "The Dark Pool", 7, filename="frog_lair.png", bg_color=BLACK)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        frog_spawn = unknowns[FrogLairZone.FROG_SPAWN][0]

        frog_entity = enemies.EnemyFactory.gen_enemy(enemies.TEMPLATE_FROG, self.get_level())
        w.add(frog_entity, gridcell=frog_spawn)

        # TODO this doesn't work
        # gs.get_instance().get_cinematics_queue().extend(cinematics.frog_intro)

        return w

    def frog_dead_song(self):
        return music.Songs.SILENCE

    def get_music_id(self):
        return music.Songs.AMPHIBIAN

    def is_boss_zone(self):
        return True


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_lair"

    def __init__(self):
        Zone.__init__(self, "Cave Horror's Lair", 15, filename="cave_lair.png", bg_color=BLACK)
        self._tree_color = (255, 170, 170)
        self._fight_end_door = (0, 170, 170)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        #tree_loc = unknowns[self._tree_color][0]
        #tree_sprite = entities.AnimationEntity(0, 0, spriteref.Bosses.cave_horror_idle,
        #                                       60, spriteref.ENTITY_LAYER, w=64*5, h=8)
        #tree_sprite.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
        #tree_sprite.set_x_centered(False)
        #tree_sprite.set_y_centered(False)
        #tree_sprite.set_x(64 * tree_loc[0] - 64)
        #tree_sprite.set_y(64 * tree_loc[1] - 64 - 112*2)
        #w.add(tree_sprite)

        fight_end_loc = unknowns[self._fight_end_door][0]

        return w

    def is_boss_zone(self):
        return True


class TombTownZone(Zone):

    ZONE_ID = "tomb_town"

    def __init__(self):
        Zone.__init__(self, "Tomb Town", 16, filename="town.png", bg_color=DARK_GREY)

    WALL_SIGNS = {
            (255, 172, 150): ("read", "dear ugly frog,\nyou're so ugly. please go away.\nsincerely,\nmary"),
            (255, 173, 150): ("read", "mary skelly's bone repair shop\ntwists: 3m\ncracks: 6m\nbreaks: 10m"),
            (255, 174, 150): ("read", "beanskull's tea shop\nmushroom tea: free"),
            (255, 175, 150): ("read", "Tombtown's City Hall\n")
    }

    BEANSKULL = (255, 170, 255)
    MAYOR = (255, 171, 255)
    MARY = (255, 172, 255)
    MUSHROOMS = (255, 175, 177)
    PLAYER_STAND_POS = (255, 215, 255)

    def build_world(self):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        for key in unknowns:
            if key in TombTownZone.WALL_SIGNS:
                pos = unknowns[key][0]
                hover_text = TombTownZone.WALL_SIGNS[key][0]
                dialog_text = Utils.listify(TombTownZone.WALL_SIGNS[key][1])
                d = dialog.Dialog.link_em_up([dialog.PlayerDialog(x) for x in dialog_text])

                sign = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_sign, pos[0], pos[1],
                                                                 interact_dialog=d)
                w.add(sign)
            elif key == TombTownZone.MUSHROOMS:
                for pos in unknowns[key]:
                    m_sprite = random.choice(spriteref.wall_decoration_mushrooms)
                    d = dialog.PlayerDialog("These mushrooms look healthy and well cared for.")
                    mushroom = entities.DecorationEntity.wall_decoration(m_sprite, pos[0], pos[1], interact_dialog=d)
                    w.add(mushroom)
            #elif key == TombTownZone.BEANSKULL:
            #    e = entities.NpcEntity(npc.NpcID.BEANSKULL)
            #    w.add(e, gridcell=unknowns[key][0])
            #elif key == TombTownZone.MAYOR:
            #    e = entities.NpcEntity(npc.NpcID.MAYOR)
            #    w.add(e, gridcell=unknowns[key][0])
            #elif key == TombTownZone.MARY:
            #    e = entities.NpcEntity(npc.NpcID.MARY_SKELLY)
            #    w.add(e, gridcell=unknowns[key][0])

        def door_open_action(event, world):
            pass

        gs.get_instance().add_trigger(events.EventListener(door_open_action, events.EventType.DOOR_OPENED, None,
                                                           single_use=True))

        return w

    def get_music_id(self):
        return music.Songs.AN_ADVENTURE_UNFOLDS


class DoorTestZone(Zone):

    ZONE_ID = "door_test"

    def __init__(self):
        Zone.__init__(self, "Main Zone", 15, filename="door_test_1.png")

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


