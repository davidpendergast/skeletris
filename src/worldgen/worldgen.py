import random

from src.world.worldstate import World
from src.game.enemies import EnemyFactory

import src.world.entities as entities
import src.utils.colors as colors
import src.game.music as music


NEIGHBORS = [(-1, 0), (0, -1), (1, 0), (0, 1)]
DIAGS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]


class Room:

    def __init__(self):
        self.x = 0
        self.y = 0
        self._floor = set()
        self._walls = set()

        self._adj_rooms = []
        self._doors = []

    def offset(self):
        return (self.x, self.y)

    def set_offset(self, x, y):
        self.x = x
        self.y = y
        return self

    def add_neighbor(self, room, door_pos):
        self._adj_rooms.append(room)
        self._doors.append((door_pos[0] - self.x, door_pos[1] - self.y))

    def all_floors(self):
        for f in self._floor:
            yield (f[0] + self.x, f[1] + self.y)

    def all_walls(self):
        for w in self._walls:
            yield (w[0] + self.x, w[1] + self.y)

    def all_doors(self):
        for d in self._doors:
            yield (d[0] + self.x, d[1] + self.y)

    def get_adorable_walls(self):
        """
            it's a pun, get it? adorable == door-able. walls that can be replaced with doors.
        """
        res = []
        for w in self.all_walls():
            # needs to be wall, floor, wall, empty clockwise
            for i in range(0, 4):
                ns = []
                for j in range(0, len(NEIGHBORS)):
                    ns.append((w[0] + NEIGHBORS[(j + i) % 4][0], w[1] + NEIGHBORS[(j + i) % 4][1]))

                if (self.has_wall_at(ns[0]) and self.has_floor_at(ns[1])
                        and self.has_wall_at(ns[2]) and self.is_empty_at(ns[3])):
                    res.append(w)
        return res

    def get_bounds(self):
        wallz = [w for w in self.all_walls()]
        if len(wallz) == 0:
            return None
        else:
            min_x = min(w[0] for w in wallz)
            min_y = min(w[1] for w in wallz)
            max_x = max(w[0] for w in wallz)
            max_y = max(w[0] for w in wallz)
            return [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1]

    def autofill_walls(self):
        for f in self._floor:
            for n in NEIGHBORS:
                p = (f[0] + n[0], f[1] + n[1])
                if p not in self._floor:
                    self._walls.add(p)

    def is_empty_at(self, xy):
        return not self.has_floor_at(xy) and not self.has_wall_at(xy)

    def has_wall_at(self, xy):
        return (xy[0] - self.x, xy[1] - self.y) in self._walls

    def has_floor_at(self, xy):
        return (xy[0] - self.x, xy[1] - self.y) in self._floor


class RoomFactory:

    @staticmethod
    def gen_room(self):
        pass

    @staticmethod
    def gen_rand_rectangular_room(w_range, h_range):
        w = w_range[0] + int((w_range[1] - w_range[0]) * random.random())
        h = h_range[0] + int((h_range[1] - h_range[0]) * random.random())
        return RoomFactory.gen_rectangular_room(w, h)

    @staticmethod
    def gen_rectangular_room(w, h):
        """generates a room with floor tiles w x h"""
        res = Room()
        for x in range(0, w):
            for y in range(0, h):
                res._floor.add((x, y))
        res.autofill_walls()
        return res


class BuilderUtils:

    @staticmethod
    def can_place_room(room, room_list):
        for floor_pos in room.all_floors():
            blocked_positions = [(floor_pos[0] + n[0], floor_pos[1] + n[1]) for n in NEIGHBORS]
            blocked_positions.append(floor_pos)
            for existing_room in room_list:
                for b in blocked_positions:
                    if existing_room.has_floor_at(b):
                        return False
        return True

    @staticmethod
    def attempt_to_add_room(to_place, to_attach_to, all_rooms, num_attempts=300):
        to_place.set_offset(0, 0)
        doors1 = to_place.get_adorable_walls()
        doors2 = to_attach_to.get_adorable_walls()

        if len(doors1) == 0 or len(doors2) == 0:
            return False
        else:
            for _ in range(0, num_attempts):
                d1 = doors1[int(len(doors1) * random.random())]
                d2 = doors2[int(len(doors2) * random.random())]
                offs = (d2[0] - d1[0], d2[1] - d1[1])
                # print("trying position {}".format(offs))
                to_place.set_offset(*offs)
                if BuilderUtils.can_place_room(to_place, all_rooms):
                    print("placing room at {}".format(to_place.offset()))
                    to_place.add_neighbor(to_attach_to, d2)
                    to_attach_to.add_neighbor(to_place, d2)
                    all_rooms.append(to_place)
                    return True
        return False

    @staticmethod
    def shift_to_origin_and_get_size(room_list):
        bounds = None
        for room in room_list:
            for w in room.all_walls():
                if bounds is None:
                    bounds = [w[0], w[1], w[0], w[1]]
                else:
                    bounds[0] = min(w[0], bounds[0])
                    bounds[1] = min(w[1], bounds[1])
                    bounds[2] = max(w[0], bounds[2])
                    bounds[3] = max(w[1], bounds[3])

        size = (bounds[2] - bounds[0] + 1, bounds[3] - bounds[1] + 1)
        for room in room_list:
            offs = room.offset()
            room.set_offset(offs[0] - bounds[0], offs[1] - bounds[1])

        return size


class WorldBlueprint:

    def __init__(self, size, level):
        self.size = size
        self.level = level
        self.geo = []
        self.geo_alt_art = []
        for i in range(0, size[0]):
            self.geo.append([World.EMPTY] * size[1])
            self.geo_alt_art.append([None] * size[1])
        self.geo_color = colors.WHITE
        self.player_spawn = (1, 1)
        self.enemy_spawns = []
        self.chest_spawns = []
        self.exit_spawns = {}         # (x, y) -> zone_id
        self.boss_exit_spawns = {}    # (x, y) -> zone_id
        self.end_of_game_spawns = []  # list of (x, y)
        self.return_exit_spawns = []  # list of (x, y)
        self.save_station = None      # (x, y, save_id)
        self.sensor_doors = []
        self.music_doors = {}         # (x, y) -> music_id
        self.global_floor_alt_art = None
        self.global_wall_alt_art = None
        self.enemy_supplier = None  # lambda: int x, int y -> Enemy

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    def get(self, x, y):
        if self.is_valid(x, y):
            return self.geo[x][y]
        else:
            return World.EMPTY

    def set(self, x, y, val):
        if self.is_valid(x, y):
            self.geo[x][y] = val
            if (x, y) in self.sensor_doors and val != World.DOOR:
                raise ValueError("tried to stomp out a sensor door at {}, {}".format(x, y))
            if (x, y) in self.music_doors and val != World.DOOR:
                raise ValueError("tried to stomp out a music door at {}, {}".format(x, y))

    def set_alt_art(self, x, y, val):
        if self.is_valid(x, y):
            self.geo_alt_art[x][y] = val

    def get_alt_art(self, x, y):
        if self.is_valid(x, y):
            return self.geo_alt_art[x][y]
        else:
            return None

    def set_global_wall_alt_art(self, val):
        self.global_wall_alt_art = val

    def set_global_floor_alt_art(self, val):
        self.global_floor_alt_art = val

    def set_sensor_door(self, x, y):
        self.set(x, y, World.DOOR)
        self.sensor_doors.append((x, y))

    def set_music_door(self, x, y, music_id):
        self.set(x, y, World.DOOR)
        self.music_doors[(x, y)] = music_id

    def set_enemy_supplier(self, supplier):
        """:param supplier: lambda: int x, int y -> Enemy"""
        self.enemy_supplier = supplier

    def add_exit_door(self, x, y, exit_id):
        import src.worldgen.zones as zones
        if zones.is_end_of_game(exit_id):
            self.end_of_game_spawns.append((x, y))
        else:
            z = zones.get_zone(exit_id, or_else=None)
            if z is None:
                print("WARN: no exit zone for {} at ({}, {})".format(exit_id, x, y))
            elif z.is_boss_zone():
                self.boss_exit_spawns[(x, y)] = exit_id
            else:
                self.exit_spawns[(x, y)] = exit_id

    def has_exit_at(self, x, y):
        if (x, y) in self.exit_spawns:
            return True
        if (x, y) in self.boss_exit_spawns:
            return True
        if (x, y) in self.return_exit_spawns:
            return True
        if (x, y) in self.end_of_game_spawns:
            return True
        else:
            return False

    def flood_search(self, x, y, allow_types=(World.FLOOR,)):
        if not self.is_valid(x, y):
            yield

        seen = set()
        seen.add((x, y))
        q = []
        q.append((x, y))

        while len(q) > 0:
            p = q.pop()
            if self.get(p[0], p[1]) in allow_types:
                yield p

                for n in NEIGHBORS:
                    p_n = (p[0] + n[0], p[1] + n[1])
                    if self.is_valid(p_n[0], p_n[1]) and p_n not in seen:
                        seen.add(p_n)
                        q.append(p_n)

    def is_valid(self, x, y):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1]

    def add_room(self, room):
        for w in room.all_walls():
            self.set(*w, World.WALL)
        for f in room.all_floors():
            self.set(*f, World.FLOOR)
        for d in room.all_doors():
            self.set(*d, World.DOOR)

    def build_world(self):
        w = World(*self.size)
        for x in range(0, self.size[0]):
            for y in range(0, self.size[1]):
                xy_geo = self.geo[x][y]
                w.set_geo(x, y, xy_geo)

                alt_art = self.geo_alt_art[x][y]
                if alt_art is None:
                    if xy_geo == World.WALL:
                        alt_art = self.global_wall_alt_art
                    elif xy_geo == World.FLOOR:
                        alt_art = self.global_floor_alt_art

                if alt_art is not None:
                    if xy_geo == World.WALL:
                        w.set_wall_type(alt_art, xy=(x, y))
                    elif xy_geo == World.FLOOR:
                        w.set_floor_type(alt_art, xy=(x, y))

                if self.geo[x][y] == World.DOOR:
                    if (x, y) in self.sensor_doors:
                        door_ent = entities.SensorDoorEntity(x, y)
                    else:
                        door_ent = entities.DoorEntity(x, y)

                    if (x, y) in self.music_doors:
                        door_music_id = self.music_doors[(x, y)]
                        door_ent.add_special_open_hook("play_song_{}".format(door_music_id),
                                                       lambda _: music.play_song(door_music_id))
                    w.add(door_ent)

        for spawn_pos in self.enemy_spawns:
            if self.enemy_supplier is None:
                enemy = EnemyFactory.gen_enemy(None, self.level)
            else:
                enemy = self.enemy_supplier(spawn_pos[0], spawn_pos[1])

            if enemy is not None:
                w.add(enemy, gridcell=spawn_pos)

        if self.save_station is not None:
            pos = (self.save_station[0], self.save_station[1])
            w.add(entities.SaveStation(pos, self.save_station[2], color=self.geo_color))

        for chest_pos in self.chest_spawns:
            w.add(entities.ChestEntity(chest_pos[0], chest_pos[1]))

        w.add(entities.Player(0, 0), gridcell=self.player_spawn)

        if len(self.exit_spawns) > 0:
            for xy in self.exit_spawns:
                w.add(entities.ExitEntity(*xy, self.exit_spawns[xy]))

        if len(self.boss_exit_spawns) > 0:
            for xy in self.boss_exit_spawns:
                w.add(entities.BossExitEntity(*xy, self.boss_exit_spawns[xy]))

        if len(self.return_exit_spawns) > 0:
            for return_pos in self.return_exit_spawns:
                w.add(entities.ReturnExitEntity(return_pos[0], return_pos[1], None))

        if len(self.end_of_game_spawns) > 0:
            for pos in self.end_of_game_spawns:
                w.add(entities.EndGameExitEnitity(pos[0], pos[1]))

        w.flush_new_entity_additions()
        return w


def is_perfect_door_location(bp, x, y):
    left_geo = bp.get(x - 1, y)
    right_geo = bp.get(x + 1, y)
    up_geo = bp.get(x, y - 1)
    down_geo = bp.get(x, y + 1)

    config = (left_geo, right_geo, up_geo, down_geo)
    v_door = (World.WALL, World.WALL, World.FLOOR, World.FLOOR)
    h_door = (World.FLOOR, World.FLOOR, World.WALL, World.WALL)
    return config == v_door or config == h_door


def rand_iterate_through_points(x, y, w, h):
    all_points = []
    for x_i in range(x, x + w):
        for y_i in range(y, y + h):
            all_points.append((x_i, y_i))
    random.shuffle(all_points)
    return all_points


class WorldFactory:
    MAX_SIZE = (15, 10)
    ROOM_NUM_BOUNDS = [10, 30]

    @staticmethod
    def gen_world_from_rooms(level, num_rooms=8):
        size_range = (3, 8)
        rooms = []
        idx = 0

        while len(rooms) < num_rooms:
            r = RoomFactory.gen_rand_rectangular_room(size_range, size_range)
            if len(rooms) == 0:
                rooms.append(r)
            else:
                to_add_to = rooms[idx]
                if BuilderUtils.attempt_to_add_room(r, to_add_to, rooms, num_attempts=3):
                    idx = len(rooms) - 1
                else:
                    idx = (idx - 1) % len(rooms)

        size = BuilderUtils.shift_to_origin_and_get_size(rooms)

        bp = WorldBlueprint(size, level)
        for room in rooms:
            bp.add_room(room)

        WorldFactory.fill_corners(bp)

        flrs = [f for f in rooms[0].all_floors()]
        random.shuffle(flrs)
        bp.player_spawn = flrs[0]

        bp.enemy_spawns = WorldFactory._get_random_floors(bp, num_rooms)
        bp.chest_spawns = WorldFactory._get_random_floors(bp, num_rooms // 3)

        # bp.exit_spawn = WorldFactory._get_random_exit_pos(bp)

        return bp

    @staticmethod
    def _get_random_exit_pos(bp):
        for pt in rand_iterate_through_points(0, 0, bp.size[0], bp.size[1]):
            if bp.get(*pt) == World.FLOOR and bp.get(pt[0], pt[1] - 1) == World.WALL:
                return pt

    @staticmethod
    def _get_random_floors(bp, max_num_to_grab):
        res = []
        for pt in rand_iterate_through_points(0, 0, bp.size[0], bp.size[1]):
            if bp.get(*pt) == World.FLOOR:
                res.append(pt)
                if len(res) >= max_num_to_grab:
                    return res

        return res

    @staticmethod
    def fill_corners(bp):
        for x in range(0, bp.size[0]):
            for y in range(0, bp.size[1]):
                if bp.get(x, y) == World.FLOOR:
                    for n in DIAGS:
                        if bp.get(x + n[0], y + n[1]) == World.EMPTY:
                            bp.set(x + n[0], y + n[1], World.WALL)

    @staticmethod
    def gen_test_world(level):
        width, height = WorldFactory.MAX_SIZE
        bp = WorldBlueprint((width, height), level)

        for x in range(0, width):
            for y in range(0, height):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    bp.geo[x][y] = World.WALL
                elif x < 3 and y < 3:
                    bp.geo[x][y] = World.FLOOR
                else:
                    if random.random() < 0.33:
                        bp.geo[x][y] = World.WALL
                    else:
                        bp.geo[x][y] = World.FLOOR

        for x in range(0, width):
            for y in range(0, height):
                if bp.geo[x][y] == World.FLOOR:
                    if is_perfect_door_location(bp, x, y):
                        if random.random() < 0.5:
                            bp.set(x, y, World.DOOR)

                    elif random.random() < 0.05:
                        bp.enemy_spawns.append((x, y))

                    elif random.random() < 0.05:
                        bp.chest_spawns.append((x, y))

        # bp.exit_spawn = WorldFactory._get_random_exit_pos(bp)

        return bp


if __name__ == "__main__":
    room1 = RoomFactory.gen_rectangular_room(3, 3)
    room2 = RoomFactory.gen_rectangular_room(7, 3)
    print(room2.get_adorable_walls())
    BuilderUtils.attempt_to_add_room(room1, room2, [room2])
