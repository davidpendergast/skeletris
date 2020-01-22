import re
import random
from sys import platform

from src.utils.util import Utils


class TileType:
    FLOOR = "."
    WALL = "x"  # "█"
    DOOR = "0"
    EMPTY = " "

    MONSTER = "m"
    PLAYER = "p"
    ENTRANCE = "v"
    EXIT = "e"
    CHEST = "c"
    NPC = "n"
    TRADE_NPC = "t"
    STRAY_ITEM = "i"
    SIGN = "s"
    DECORATION = "d"


def color_char(c):
    if platform == "linux" or platform == "linux2":
        if c == TileType.DOOR:
            return "\033[1;34m" + c + "\033[0;0m"  # blue
        elif c == TileType.MONSTER:
            return "\033[1;31m" + c + "\033[0;0m"  # red
        elif c == TileType.CHEST:
            return "\033[1;35m" + c + "\033[0;0m"  # magenta
        elif c == TileType.EXIT or c == TileType.PLAYER or c == TileType.ENTRANCE:
            return "\033[1;32m" + c + "\033[0;0m"  # green
        elif c == TileType.EMPTY or c == TileType.WALL or c == TileType.FLOOR:
            return c
        else:
            return "\033[1;33m" + c + "\033[0;0m"  # yellow
    else:
        return c  # don't really care about colors on other systems


class Tileish:

    def get(self, x, y):
        return TileType.EMPTY

    def w(self):
        return 0

    def h(self):
        return 0

    def coords(self):
        for x in range(0, self.w()):
            for y in range(0, self.h()):
                yield (x, y)

    def is_valid(self, x, y):
        return 0 <= x < self.w() and 0 <= y < self.h()

    def __str__(self):
        res = []
        for y in range(0, self.h()):
            for x in range(0, self.w()):
                val = self.get(x, y)
                res.append(str(color_char(val)) + " ")
            res.append("\n")
        return "".join(res)


class Tile(Tileish):

    def __init__(self, size, door_offs=3, door_len=2):
        self.grid = []
        for i in range(0, size):
            self.grid.append([TileType.EMPTY for _ in range(0, size)])

        self._door_offs = door_offs
        self._door_length = door_len

    def in_tile(self, x, y):
        return 0 <= x < self.w() and 0 <= y < self.h()

    def get(self, x, y):
        if self.in_tile(x, y):
            return self.grid[x][y]
        else:
            return TileType.EMPTY

    def set(self, x, y, val):
        self.grid[x][y] = val

    def replace(self, x, y, repl_val, val):
        if self.get(x, y) == repl_val:
            self.set(x, y, val)

    def fill(self, x1, y1, x2, y2, val):
        for x in range(x1, x2):
            for y in range(y1, y2):
                self.set(x, y, val)

    def w(self):
        return len(self.grid)

    def h(self):
        return len(self.grid[0])

    def door_coords(self, door_num):
        if door_num == 0:
            return [(self._door_offs + i, 0) for i in range(0, self._door_length)]
        elif door_num == 1:
            return [(self.w() - self._door_length - self._door_offs + i, 0) for i in range(0, self._door_length)]
        elif door_num == 2:
            return [(self.w() - 1, self._door_offs + i) for i in range(0, self._door_length)]
        elif door_num == 3:
            return [(self.w() - 1, self.h() - self._door_length - self._door_offs + i) for i in range(0, self._door_length)]
        elif door_num == 4:
            return [(self.w() - self._door_length - self._door_offs + i, self.h() - 1) for i in range(0, self._door_length)]
        elif door_num == 5:
            return [(self._door_offs + i, self.h() - 1) for i in range(0, self._door_length)]
        elif door_num == 6:
            return [(0, self.h() - self._door_length - self._door_offs + i) for i in range(0, self._door_length)]
        elif door_num == 7:
            return [(0, self._door_offs + i) for i in range(0, self._door_length)]

    @staticmethod
    def doors_on_side(side):
        """side: (1, 0), (-1, 0), (0, 1), or (0, -1)"""
        if side == (0, -1):
            return [0, 1]
        elif side == (1, 0):
            return [2, 3]
        elif side == (0, 1):
            return [4, 5]
        elif side == (-1, 0):
            return [6, 7]

    @staticmethod
    def get_door_direction(door_num):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for d in dirs:
            if door_num in Tile.doors_on_side(d):
                return d
        return None

    @staticmethod
    def connecting_door(door_num):
        if door_num % 2 == 0:
            return (door_num + 5) % 8
        else:
            return (door_num + 3) % 8

    def hub_coords(self, door_num):
        hub_size = self._door_length
        if door_num == 0 or door_num == 7:
            min_xy = (self._door_offs, self._door_offs)
        elif door_num == 1 or door_num == 2:
            min_xy = (self.w()-self._door_offs-hub_size, self._door_offs)
        elif door_num == 3 or door_num == 4:
            min_xy = (self.w()-self._door_offs-hub_size, self.h()-self._door_offs-hub_size)
        elif door_num == 5 or door_num == 6:
            min_xy = (self._door_offs, self.h()-self._door_offs-hub_size)

        res = []
        for x in range(0, hub_size):
            for y in range(0, hub_size):
                res.append((min_xy[0] + x, min_xy[1] + y))
        return res

    def hub_connection_coords(self, num):
        h1 = self.hub_coords(num*2)
        h2 = self.hub_coords(num*2 + 1)

        enclosing_rect = RectUtils.rect_containing(h1 + h2)
        return [xy for xy in RectUtils.coords_in_rect(enclosing_rect) if (xy not in h1 and xy not in h2)]


class PartitionGrid:
    def __init__(self, grid_w, grid_h):
        self.partitions = [None] * grid_w
        for i in range(0, len(self.partitions)):
            self.partitions[i] = [None] * grid_h

    def w(self):
        return len(self.partitions)

    def h(self):
        return len(self.partitions[0])

    def get(self, x, y):
        if 0 <= x < self.w() and 0 <= y < self.h():
            return self.partitions[x][y]
        else:
            return None

    def set(self, x, y, p):
        self.partitions[x][y] = p

    def can_place_at(self, x, y, p, direction=None):
        if not (0 <= x < self.w() and 0 <= y < self.h()):
            return False
        elif direction is not None:
            n = self.get(x + direction[0], y + direction[1])
            my_doors = Tile.doors_on_side(direction)
            n_doors = Tile.doors_on_side((-direction[0], -direction[1]))
            for i in range(0, len(my_doors)):
                if p.has_door(my_doors[i]) != n.has_door(n_doors[i]):
                    return False
            return True
        else:
            return (self.can_place_at(x, y, p, direction=(0, -1)) and
                    self.can_place_at(x, y, p, direction=(1, 0)) and
                    self.can_place_at(x, y, p, direction=(0, 1)) and
                    self.can_place_at(x, y, p, direction=(-1, 0)))

    def has_door(self, x, y, door_num):
        """returns: True, False or None if partition is None"""
        p = self.get(x, y)
        if p is None:
            return None
        else:
            return p.has_door(door_num)

    def needs_door(self, x, y, door_num, prevent_boundary_doors=True):
        """returns: True or False if neighboring tile forces a door connection/disconnection, else None."""
        return self.needed_doors(x, y, prevent_boundary_doors=prevent_boundary_doors)[door_num]

    def needed_doors(self, x, y, prevent_boundary_doors=False):
        res = []
        for direction in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            if not (0 <= x + direction[0] < self.w() and 0 <= y + direction[1] < self.h()):
                res.append(False if prevent_boundary_doors else None)
                res.append(False if prevent_boundary_doors else None)
            else:
                n = self.get(x + direction[0], y + direction[1])
                if n is None:
                    res.append(None)
                    res.append(None)
                else:
                    d1 = Tile.doors_on_side((-direction[0], -direction[1]))[0]
                    d2 = Tile.doors_on_side((-direction[0], -direction[1]))[1]
                    res.append(n.has_door(d2))  # gotta flip it because it's... mirrored?
                    res.append(n.has_door(d1))
        return res

    def __str__(self):
        return str(self.partitions)


class TileGrid(Tileish):

    def __init__(self, grid_w, grid_h, tile_size=(16, 16)):
        Tileish.__init__(self)
        self.tile_size = tile_size
        self.tiles = [None] * grid_w
        for i in range(0, len(self.tiles)):
            self.tiles[i] = [None] * grid_h

    def w(self):
        return self.tile_size[0] * self.grid_w()

    def h(self):
        return self.tile_size[1] * self.grid_h()

    def grid_w(self):
        return len(self.tiles)

    def grid_h(self):
        return len(self.tiles[0])

    def get_tile(self, grid_x, grid_y):
        if 0 <= grid_x < self.grid_w() and 0 <= grid_y < self.grid_h():
            return self.tiles[grid_x][grid_y]
        else:
            return None

    def tile_at(self, x, y):
        if x < 0 or y < 0:
            return None
        else:
            return self.get_tile(int(x / self.tile_size[0]), int(y / self.tile_size[1]))

    def get(self, x, y):
        t = self.tile_at(x, y)
        if t is None:
            return TileType.EMPTY
        else:
            rel_x, rel_y = self.rel_coords(x, y)
            return t.get(rel_x, rel_y)

    def rel_coords(self, x, y):
        rel_x = x % self.tile_size[0]
        rel_y = y % self.tile_size[1]
        return (rel_x, rel_y)

    def set_tile(self, grid_x, grid_y, tile):
        self.tiles[grid_x][grid_y] = tile

    def set(self, x, y, val):
        t = self.tile_at(x, y)
        if t is None:
            if val is not TileType.EMPTY:
                raise ValueError("tile is None at ({}, {})".format(x, y))
            else:
                return
        else:
            rel_x, rel_y = self.rel_coords(x, y)
            t.set(rel_x, rel_y, val)


class GridBuilder:

    @staticmethod
    def random_path_between(p1, p2, w, h):
        path = [p1]
        bad = []
        while path[-1] != p2:
            cur = path[-1]
            neighbors = list(Utils.neighbors(cur[0], cur[1]))
            random.shuffle(neighbors)

            added_n = False
            while not added_n and len(neighbors) > 0:
                n = neighbors.pop()
                if 0 <= n[0] < w and 0 <= n[1] < h and n not in bad and n not in path:
                    path.append(n)
                    added_n = True

            if not added_n:
                bad.append(path.pop(-1))  # at a dead end

            if len(path) == 0:
                raise ValueError("failed to find path: p1={}, p2={}, w={}, h={}".format(p1, p2, w, h))

        return path

    @staticmethod
    def random_partition_grid(w, h, start=None, end=None, fully_connected=True):
        """returns: (path, partition_grid)"""
        start = start if start is not None else (random.randint(0, w - 1), random.randint(0, h - 1))
        end = end if end is not None else (random.randint(0, w - 1), random.randint(0, h - 1))

        p_grid = PartitionGrid(w, h)
        path = GridBuilder.random_path_between(start, end, w, h)

        entry_door = None
        for path_idx in range(0, len(path)):
            cur_path = path[path_idx]

            force_enabled = []
            force_disabled = []
            force_connected = []

            door_req = p_grid.needed_doors(cur_path[0], cur_path[1])
            for i in range(0, 8):
                if door_req[i] is True:
                    force_enabled.append(i)
                elif door_req[i] is False:
                    force_disabled.append(i)

            if path_idx < len(path) - 1:
                next_path = path[path_idx + 1]
                direction = (next_path[0] - cur_path[0], next_path[1] - cur_path[1])
                exit_door = random.choice(Tile.doors_on_side(direction))
                force_enabled.append(exit_door)
                if entry_door is not None:
                    force_connected = [entry_door, exit_door]

                entry_door = Tile.connecting_door(exit_door)  # setting for next loop

            p = Partition.random_partition(force_valid=True,
                                           force_doors=force_enabled,
                                           force_not_doors=force_disabled,
                                           force_connected=force_connected)

            p_grid.set(cur_path[0], cur_path[1], p)

        empty_coords = [xy for xy in RectUtils.coords_in_rect([0, 0, w, h]) if p_grid.get(xy[0], xy[1]) is None]
        random.shuffle(empty_coords)

        for (x, y) in empty_coords:
            door_req = p_grid.needed_doors(x, y)
            force_enabled = []
            force_disabled = []
            for i in range(0, 8):
                if door_req[i] is True:
                    force_enabled.append(i)
                elif door_req[i] is False:
                    force_disabled.append(i)
            p = Partition.random_partition(force_valid=True,
                                           force_doors=force_enabled,
                                           force_not_doors=force_disabled)
            p_grid.set(x, y, p)

        if fully_connected:
            disjoint_neighborhoods = list(GridBuilder.get_disconnected_neighborhoods(p_grid))
            if len(disjoint_neighborhoods) > 1:

                good_neighborhood = None  # the neighborhood that contains start and end, aka the "main one"
                for n in disjoint_neighborhoods:
                    contains_start = any([((start[0], start[1], i) in n) for i in range(0, 8)])
                    contains_end = any([((end[0], end[1], i) in n) for i in range(0, 8)])
                    if contains_start and contains_end:
                        good_neighborhood = n
                        break

                if good_neighborhood is None:
                    raise ValueError("there's no neighborhood containing the start and end positions")

                for n in disjoint_neighborhoods:
                    if n == good_neighborhood:
                        continue
                    else:
                        # now we need to surgically remove all the disconnected doors...
                        for xyd in n:
                            x, y, d = xyd
                            part = p_grid.get(x, y)
                            p_grid.set(x, y, Partition.without_door(part, d))

        return path, p_grid

    @staticmethod
    def get_disconnected_neighborhoods(p_grid):
        all_doors = set()  # list of (x, y, door_num)
        for x in range(0, p_grid.w()):
            for y in range(0, p_grid.h()):
                for door_num in range(0, 8):
                    if p_grid.has_door(x, y, door_num):
                        all_doors.add((x, y, door_num))

        res = []

        for xyd in all_doors:
            x, y, door_num = xyd
            sub_neigh = [(x, y, d) for d in p_grid.get(x, y).get_group(door_num)]

            connected_door_num = Tile.connecting_door(door_num)
            direction = Tile.get_door_direction(door_num)
            connected_door = (x + direction[0], y + direction[1], connected_door_num)
            if connected_door in all_doors:
                sub_neigh.append(connected_door)

            existing_neighborhoods = []
            for neighborhood in res:
                for door in sub_neigh:
                    if door in neighborhood and neighborhood not in existing_neighborhoods:
                        existing_neighborhoods.append(neighborhood)

            if len(existing_neighborhoods) == 0:
                new_neighborhood = set()
                new_neighborhood.update(sub_neigh)
                res.append(new_neighborhood)
            elif len(existing_neighborhoods) == 1:
                existing_neighborhoods[0].update(sub_neigh)
            else:
                for i in range(1, len(existing_neighborhoods)):
                    to_merge = existing_neighborhoods[i]
                    existing_neighborhoods[0].update(to_merge)
                    res.remove(to_merge)
                existing_neighborhoods[0].update(sub_neigh)

        return res


class RectUtils:

    @staticmethod
    def coords_in_rect(rect):
        for x in range(rect[0], rect[0] + rect[2]):
            for y in range(rect[1], rect[1] + rect[3]):
                yield (x, y)

    @staticmethod
    def coords_around_rect(rect, include_corners=False):
        for x in range(rect[0], rect[0] + rect[2]):
            yield (x, rect[1] - 1)
            yield (x, rect[1] + rect[3])
        for y in range(rect[1], rect[1] + rect[3]):
            yield (rect[0] - 1, y)
            yield (rect[0] + rect[2], y)
        if include_corners:
            yield (rect[0] - 1, rect[1] - 1)
            yield (rect[0] + rect[2], rect[1] - 1)
            yield (rect[0] - 1, rect[1] + rect[3])
            yield (rect[0] + rect[2], rect[1] + rect[3])

    @staticmethod
    def rect_containing(xy_coords):
        min_xy = [xy_coords[0][0], xy_coords[0][1]]
        max_xy = [xy_coords[0][0], xy_coords[0][1]]
        for (x, y) in xy_coords:
            min_xy[0] = min(min_xy[0], x)
            min_xy[1] = min(min_xy[1], y)
            max_xy[0] = max(max_xy[0], x)
            max_xy[1] = max(max_xy[1], y)
        return [min_xy[0], min_xy[1], max_xy[0] - min_xy[0] + 1, max_xy[1] - min_xy[1] + 1]

    @staticmethod
    def rects_intersect(r1, r2, buffer_zone=0):
        if r1[0] + r1[2] <= r2[0] - buffer_zone or r2[0] + r2[2] <= r1[0] - buffer_zone:
            return False
        elif r1[1] + r1[3] <= r2[1] - buffer_zone or r2[1] + r2[3] <= r1[1] - buffer_zone:
            return False
        return True


class TileFiller:

    @staticmethod
    def flood_fill(tile, start_x, start_y, on_values):
        if tile.get(start_x, start_y) not in on_values:
            return
        else:
            seen = {(start_x, start_y): None}  # i don't know how to make sets rn

            q = [(start_x, start_y)]

            while len(q) > 0:
                x, y = q.pop()
                if tile.get(x, y) in on_values:
                    yield (x, y)
                    for (n_x, n_y) in Utils.neighbors(x, y):
                        if tile.in_tile(n_x, n_y) and (n_x, n_y) not in seen:
                            seen[(n_x, n_y)] = None
                            q.append((n_x, n_y))

    @staticmethod
    def calculate_partition(tile):
        all_doors = [0, 1, 2, 3, 4, 5, 6, 7]
        door_coords = {}
        for d in all_doors:
            door_coords[d] = tile.door_coords(d)[0]

        res = []
        while len(all_doors) > 0:
            d_num = all_doors.pop(0)
            d_x, d_y = tile.door_coords(d_num)[0]
            touches = [xy for xy in TileFiller.flood_fill(tile, d_x, d_y, (TileType.DOOR, TileType.FLOOR))]
            if len(touches) > 0:
                group = [d_num]
                for d in list(all_doors):
                    if door_coords[d] in touches:
                        group.append(d)
                        all_doors.remove(d)
                res.append(group)
        return Partition(res)

    @staticmethod
    def basic_door_fill(tile, partition):
        tile.fill(0, 0, tile.w(), tile.h(), TileType.EMPTY)

        for i in range(0, 8):
            for (x, y) in tile.door_coords(i):
                if i in partition.as_map:
                    tile.set(x, y, TileType.DOOR)
                else:
                    tile.set(x, y, TileType.EMPTY)

    @staticmethod
    def basic_floor_fill(tile, partition):
        TileFiller.basic_door_fill(tile, partition)
        unfilled_hubs = [0, 2, 4, 6]
        for i in range(0, 8):
            if partition.has_door(i):
                door_coords = tile.door_coords(i)
                hub_coords = tile.hub_coords(i)
                full_rect = RectUtils.rect_containing(door_coords + hub_coords)
                for (x, y) in RectUtils.coords_in_rect(full_rect):
                    tile.replace(x, y, TileType.EMPTY, TileType.FLOOR)

                if int(i/2) in unfilled_hubs:
                    unfilled_hubs.remove((i + i % 2) % 8)

        toggle_zones = [tile.hub_connection_coords(i) for i in range(0, 4)]
        for hub in unfilled_hubs:
            toggle_zones.append([xy for xy in tile.hub_coords(hub)])

        enabled = []
        for i in range(0, 2**len(toggle_zones)):  # very nice efficiency!
            enabled.append([min(2**j & i, 1) for j in range(0, len(toggle_zones))])
        random.shuffle(enabled)
        enabled.sort(key=lambda v: sum(v))

        for zone_toggle in enabled:
            for i in range(0, len(toggle_zones)):
                for (x, y) in toggle_zones[i]:
                    if zone_toggle[i]:
                        tile.set(x, y, TileType.FLOOR)
                    else:
                        tile.set(x, y, TileType.EMPTY)
            if TileFiller.calculate_partition(tile) == partition:
                return

    @staticmethod
    def basic_room_fill(tile, partition, min_rooms=1, max_rooms=4, iter_limit=300,
                        min_size=3, max_size=6, disjoint_rooms=True, connected_rooms=True):
        """
        disjoint_rooms: if True, forces rooms to be non-overlapping
        connected_rooms: if True, forces rooms to be touching existing floor tiles
        returns: list of room rectangles"""
        TileFiller.basic_floor_fill(tile, partition)

        n = random.randint(min_rooms, max_rooms)
        iteration = 0

        rooms_placed = []

        while n > 0 and iteration < iter_limit:
            iteration += 1
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(1, tile.w() - w - 2)
            y = random.randint(1, tile.h() - h - 2)

            room_rect = [x, y, w, h]

            if disjoint_rooms:
                bad_intersect = False
                for r in rooms_placed:
                    if RectUtils.rects_intersect(room_rect, r):
                        bad_intersect = True
                        break
                if bad_intersect:
                    continue

            if connected_rooms:
                not_connected = True
                for (x, y) in RectUtils.coords_around_rect(room_rect):
                    if tile.get(x, y) != TileType.EMPTY:
                        not_connected = False
                        break
                if not_connected:
                    continue

            was_empty = []
            for xy in RectUtils.coords_in_rect(room_rect):
                if tile.get(xy[0], xy[1]) == TileType.EMPTY:
                    was_empty.append(xy)
                    tile.set(xy[0], xy[1], TileType.FLOOR)

            if TileFiller.calculate_partition(tile) == partition:
                # added a room successfully!
                rooms_placed.append(room_rect)
                n -= 1
            else:
                for xy in was_empty:
                    tile.set(xy[0], xy[1], TileType.EMPTY)

        return rooms_placed


class TileGridBuilder:

    @staticmethod
    def is_dangly(x, y, tile_grid):
        if tile_grid.get(x, y) != TileType.EMPTY:
            count = 0
            for n in Utils.neighbors(x, y):
                if tile_grid.get(n[0], n[1]) != TileType.EMPTY:
                    count += 1
            if count <= 1:
                return True
        return False

    @staticmethod
    def clean_up_dangly_bits(tile_grid, source_xy=None):
        if source_xy is not None:
            if TileGridBuilder.is_dangly(source_xy[0], source_xy[1], tile_grid):
                tile_grid.set(source_xy[0], source_xy[1], TileType.EMPTY)
                for n in Utils.neighbors(source_xy[0], source_xy[1]):
                    TileGridBuilder.clean_up_dangly_bits(tile_grid, source_xy=n)
            else:
                return
        else:
            for x in range(0, tile_grid.w()):
                for y in range(0, tile_grid.h()):
                    if TileGridBuilder.is_dangly(x, y, tile_grid):
                        TileGridBuilder.clean_up_dangly_bits(tile_grid, source_xy=(x, y))

    @staticmethod
    def is_valid_door_coord(x, y, tile_grid):
        horz_door = (tile_grid.get(x-1, y) == TileType.FLOOR and tile_grid.get(x+1, y) == TileType.FLOOR and
                     tile_grid.get(x, y-1) == TileType.EMPTY and tile_grid.get(x, y+1) == TileType.EMPTY)
        vert_door = (tile_grid.get(x, y-1) == TileType.FLOOR and tile_grid.get(x, y+1) == TileType.FLOOR and
                     tile_grid.get(x-1, y) == TileType.EMPTY and tile_grid.get(x+1, y) == TileType.EMPTY)

        return horz_door != vert_door

    @staticmethod
    def clean_up_doors(tile_grid):
        for x in range(0, tile_grid.w()):
            for y in range(0, tile_grid.h()):
                if tile_grid.get(x, y) == TileType.DOOR and not TileGridBuilder.is_valid_door_coord(x, y, tile_grid):
                    tile_grid.set(x, y, TileType.FLOOR)

    @staticmethod
    def add_walls(tile_grid):
        needs_walls = []
        for x in range(0, tile_grid.w()):
            for y in range(0, tile_grid.h()):
                if (tile_grid.get(x, y) == TileType.EMPTY):
                    for n in Utils.neighbors(x, y, and_diags=True):
                        if tile_grid.get(n[0], n[1]) != TileType.EMPTY:
                            needs_walls.append((x, y))
                            continue
        for (x, y) in needs_walls:
            tile_grid.set(x, y, TileType.WALL)

    @staticmethod
    def flood_search(tile_grid, x, y, on_values):
        res = set()
        if tile_grid.get(x, y) not in on_values:
            return res
        else:
            seen = set()
            seen.add((x, y))
            q = [(x, y)]
            while len(q) > 0:
                pos = q.pop()
                res.add(pos)

                for n in Utils.neighbors(pos[0], pos[1]):
                    if tile_grid.is_valid(n[0], n[1]) and n not in seen and tile_grid.get(n[0], n[1]) in on_values:
                        seen.add(n)
                        q.append(n)
            return res

    @staticmethod
    def fill_empty_islands_with_walls(tile_grid, smaller_than=16):
        seen = set()
        for x in range(0, tile_grid.w()):
            for y in range(0, tile_grid.h()):
                if (x, y) in seen:
                    continue
                island = TileGridBuilder.flood_search(tile_grid, x, y, (TileType.EMPTY))
                seen.update(island)
                if 0 < len(island) < smaller_than:
                    for pos in island:
                        tile_grid.set(pos[0], pos[1], TileType.WALL)

    @staticmethod
    def search(tile_grid, for_values):
        """returns: all coordinates in the tile grid with the given values"""
        res = set()

        for xy in tile_grid.coords():
            if for_values is None or tile_grid.get(xy[0], xy[1]) in for_values:
                res.add(xy)

        return res


_ALL_FEATURES = {}  # feat_id -> Feature


class Feature(Tileish):

    def __init__(self, feat_id, replace, place, appear_rate=1, can_rotate=True,
                 max_per_zone=-1, min_level=-1, max_level=-1,
                 on_critical_path=False):
        self.feat_id = feat_id
        self.replace = replace
        self.place = place
        self.can_rotate = can_rotate
        self._appear_rate = appear_rate
        self._max_per_zone = max_per_zone
        self._min_level = min_level
        self._max_level = max_level

        self._on_critical_path_only = on_critical_path

        self._validate()

        # don't overwrite a feature when we're producing a rotated version~
        if self.feat_id not in _ALL_FEATURES:
            _ALL_FEATURES[self.feat_id] = self

    def __repr__(self):
        return str(self.feat_id)

    def _validate(self):
        if len(self.replace) == 0 or len(self.replace[0]) == 0:
            raise ValueError("empty feature {}".format(self.feat_id))
        for row in self.replace:
            if len(row) != len(self.replace[0]):
                raise ValueError("non-rectangular feature {}".format(self.feat_id))

        if len(self.replace) != len(self.place):
            raise ValueError("invalid feature {}: mismatched place/replace heights {} != {}".format(
                self.feat_id, len(self.replace), len(self.place)
            ))
        for i in range(0, len(self.replace)):
            place_width = len(self.replace[i])
            replace_width = len(self.place[i])
            if place_width != replace_width:
                raise ValueError("invalid feature {}: mismatched place/replace widths on row {}: {} != {}".format(
                    self.feat_id, i, place_width, replace_width
                ))

    def appear_rate(self, at_level=None, cur_count=0):
        if at_level is not None:
            if self._min_level != -1 and at_level < self._min_level:
                return 0
            if self._max_level != -1 and at_level > self._max_level:
                return 0

        if self._max_per_zone != -1 and cur_count >= self._max_per_zone:
            return 0
        else:
            return self._appear_rate

    def is_on_critical_path(self):
        return self._on_critical_path_only

    def w(self):
        return len(self.replace[0])

    def h(self):
        return len(self.replace)

    def get(self, x, y):
        if self.is_valid(x, y):
            return self.replace[y][x]
        else:
            return TileType.EMPTY

    def get_place_val(self, x, y):
        return self.place[y][x]

    def rotated(self, rots=1):
        if rots <= 0:
            return self
        elif not self.can_rotate:
            return ValueError("can't rotate feature: {}".format(self.feat_id))

        replace = ["" for _ in range(0, self.w())]
        place = ["" for _ in range(0, self.w())]

        for i in range(0, self.w()):
            for j in range(self.h()-1, -1, -1):
                replace[i] = replace[i] + self.replace[j][i]
                place[i] = place[i] + self.place[j][i]

        return Feature(self.feat_id, replace, place, can_rotate=True,
                       appear_rate=self._appear_rate,
                       max_level=self._max_level,
                       min_level=self._min_level,
                       max_per_zone=self._max_per_zone,
                       on_critical_path=self._on_critical_path_only).rotated(rots=rots-1)

    def can_place_at(self, tilish, x, y):
        for feat_x in range(0, self.w()):
            for feat_y in range(0, self.h()):
                feat_val = self.get(feat_x, feat_y)
                if feat_val == "?":
                    continue
                elif not tilish.is_valid(x + feat_x, y + feat_y):
                    return False
                elif feat_val != tilish.get(x + feat_x, y + feat_y):
                    return False
        return True

    def __str__(self):
        return "Feature:[{}, replace={}, place={}]".format(self.feat_id, self.replace, self.place)


class FeatureUtils:

    @staticmethod
    def all_possible_placements_overlapping_rect(feature, tilish, rect):
        """returns: list of valid feature placements (x, y)"""
        res = []
        for x in range(rect[0] - feature.w() + 1, rect[0] + rect[2]):
            for y in range(rect[1] - feature.h(), rect[1] + rect[3]):
                if feature.can_place_at(tilish, x, y):
                    res.append((x, y))
        return res

    @staticmethod
    def try_to_place_feature_into_rect(feature, tilish, rect):
        rots = [0]
        if feature.can_rotate:
            rots.extend([1, 2, 3])

        random.shuffle(rots)
        for rot in rots:
            rotated_feature = feature.rotated(rot)
            possible_placements = FeatureUtils.all_possible_placements_overlapping_rect(rotated_feature, tilish, rect)
            if len(possible_placements) > 0:
                placement = random.choice(possible_placements)
                FeatureUtils.write_into(rotated_feature, tilish, placement[0], placement[1])
                return True

        return False

    @staticmethod
    def write_into(feature, tile_grid, x, y):
        for feat_x in range(0, feature.w()):
            for feat_y in range(0, feature.h()):
                feat_val = feature.get_place_val(feat_x, feat_y)
                cur_val = tile_grid.get(x + feat_x, y + feat_y)
                if feat_val != "?" and cur_val != feat_val:
                    tile_grid.set(x + feat_x, y + feat_y, feat_val)

    CHAR_MAP = {"W": TileType.WALL,
                "-": TileType.FLOOR,
                ".": TileType.EMPTY,
                "p": TileType.PLAYER,
                "v": TileType.ENTRANCE,
                "e": TileType.EXIT,
                "m": TileType.MONSTER,
                "c": TileType.CHEST,
                "i": TileType.STRAY_ITEM,
                "n": TileType.NPC,
                "t": TileType.TRADE_NPC,
                "s": TileType.SIGN,
                "d": TileType.DECORATION}

    @staticmethod
    def convert_char(c):
        if c in FeatureUtils.CHAR_MAP:
            return FeatureUtils.CHAR_MAP[c]
        else:
            return c

    @staticmethod
    def convert(feature_def):
        res = []
        for word in feature_def:
            new_word = "".join(FeatureUtils.convert_char(c) for c in word)
            res.append(new_word)
        return res


class Features:

    START = Feature("start",
                    FeatureUtils.convert(["?-?",
                                          "WWW",
                                          "..."]),
                    FeatureUtils.convert(["?p?",
                                          "WvW",
                                          "WWW"]), can_rotate=False, appear_rate=0)

    # we fall back to this style of a start if there's nowhere to place the fancy type
    BACKUP_START = Feature("backup_start",
                           FeatureUtils.convert(["-", "W"]),
                           FeatureUtils.convert(["p", "W"]), can_rotate=False, appear_rate=0)

    EXIT = Feature("exit_door",
                   FeatureUtils.convert(["W", "-"]),
                   FeatureUtils.convert(["W", "e"]), can_rotate=False, appear_rate=0)

    SMALL_MONSTER = Feature("monster_2x2",
                            FeatureUtils.convert(["--", "--"]),
                            FeatureUtils.convert(["m-", "--"]), appear_rate=13)

    LARGE_MONSTER = Feature("monster_3x3",
                            FeatureUtils.convert(["---", "---", "---"]),
                            FeatureUtils.convert(["m--", "--m", "-m-"]), appear_rate=9)

    CHEST = Feature("chest",
                    FeatureUtils.convert(["W", "-"]),
                    FeatureUtils.convert(["W", "c"]), can_rotate=True, appear_rate=2)

    STRAY_ITEM = Feature("stray_item",
                         FeatureUtils.convert(["-"]),
                         FeatureUtils.convert(["i"]), appear_rate=0)  # TODO these suck, just delete

    DECORATION = Feature("decoration",
                         FeatureUtils.convert(["W", "-"]),
                         FeatureUtils.convert(["W", "d"]), can_rotate=False, appear_rate=6)

    SIGN = Feature("sign",
                   FeatureUtils.convert(["W", "-"]),
                   FeatureUtils.convert(["W", "s"]), can_rotate=False, appear_rate=0)  # these just suck

    STORY_NPC = Feature("conversation_npc",
                        FeatureUtils.convert(["?W?", "?-?", "---"]),
                        FeatureUtils.convert(["?W?", "?n?", "---"]), can_rotate=True,
                        appear_rate=0)  # handled as a special case

    TRADE_NPC = Feature("trade_npc",
                        FeatureUtils.convert(["?W?", "?-?", "---"]),
                        FeatureUtils.convert(["?W?", "?t?", "---"]), can_rotate=True, appear_rate=2,
                        min_level=3, max_per_zone=3)

    @staticmethod
    def get_random_feature(at_level=None, current_counts=None):
        weighted_feats = []
        for feat_id in _ALL_FEATURES:
            cur_count = 0
            if current_counts is not None and feat_id in current_counts:
                cur_count = current_counts[feat_id]

            appear_rate = _ALL_FEATURES[feat_id].appear_rate(at_level=at_level, cur_count=cur_count)
            for _ in range(0, appear_rate):
                weighted_feats.append(feat_id)

        if len(weighted_feats) > 0:
            return _ALL_FEATURES[random.choice(weighted_feats)]
        else:
            print("WARN: no valid features for level: {}" + at_level)
            return None


class Partition:

    def __init__(self, p):
        for g in p:
            g.sort()
        p.sort()

        self.p = p
        self.as_map = {}  # door_number -> group number

        for i in range(0, len(p)):
            group = p[i]
            if len(group) == 0:
                raise ValueError("empty group in partition: {}".format(p))
            for door_num in group:
                if door_num in self.as_map:
                    raise ValueError("door {} appears multiple times: {}".format(door_num, p))
                self.as_map[door_num] = i

    def get_doors(self):
        return [i for i in range(0, 8) if i in self.as_map]

    def has_door(self, door_num):
        return door_num in self.as_map

    def num_groups(self):
        return len(self.p)

    def is_valid(self):
        # doors that share the same corner must connect if both are present.
        corners = [(0, 7), (1, 2), (3, 4), (5, 6)]
        for c in corners:
            if c[0] in self.as_map and c[1] in self.as_map:
                if self.as_map[c[0]] != self.as_map[c[1]]:
                    return False

        ordered_groups = []
        for door_num in range(0, 8):
            if door_num in self.as_map:
                group_num = self.as_map[door_num]
                if len(ordered_groups) == 0:
                    ordered_groups.append(group_num)
                elif ordered_groups[-1] != group_num:
                    if door_num != 7 or group_num != ordered_groups[0]:
                        ordered_groups.append(group_num)
        as_str = "".join([str(v) for v in ordered_groups])

        # two groups cannot make an A-B-A-C pattern
        pattern = re.compile(r'(\d)[^\1]+\1[^\1]')
        if pattern.search(as_str) is not None:
            return False

        # or an A-B-C-B pattern
        pattern = re.compile(r'(\d)([^\1])[^\2]+\2')
        if pattern.search(as_str) is not None:
            return False

        return True

    def get_group(self, door_num):
        for g in self.p:
            if door_num in g:
                return g
        return None

    def __repr__(self):
        res = "Partition:{}".format(self.p)
        if not self.is_valid():
            res += " (invalid)"
        return res

    def __eq__(self, other):
        return self.p == other.p  # should both have been sorted the same

    @staticmethod
    def without_door(partition, door_num):
        if not partition.has_door(door_num):
            return partition
        else:
            new_p = []
            for group in partition.p:
                new_group = [d for d in group if d != door_num]
                if len(new_group) > 0:
                    new_p.append(new_group)
            return Partition(new_p)

    @staticmethod
    def random_partition(force_valid=True, min_doors=0, max_doors=8, force_doors=[], force_not_doors=[], force_connected=[]):

        p = None
        while p is None or (force_valid and not p.is_valid()):

            doors = [i for i in range(0, 8) if i in force_doors or i in force_connected]
            optional_doors = [i for i in range(0, 8) if (i not in doors and i not in force_not_doors)]

            to_choose = random.randint(min_doors - len(doors), max_doors - len(doors))
            if to_choose < 0:
                to_choose = 0
            elif to_choose > len(optional_doors):
                to_choose = len(optional_doors)

            doors.extend(random.sample(optional_doors, to_choose))

            if len(doors) == 0:
                return Partition([])

            res = []

            if len(force_connected) > 0:
                for d in force_connected:
                    doors.remove(d)

            if len(doors) == 0:
                if len(force_connected) > 0:
                    return Partition([list(force_connected)])
                else:
                    return Partition([])

            n_groups = 1 + int((len(doors) - 1) * random.random())
            random.shuffle(doors)
            for i in range(0, n_groups):
                res.append([doors[i]])

            if n_groups < len(doors):
                for i in range(n_groups, len(doors)):
                    res[int(n_groups * random.random())].append(doors[i])

            if len(force_connected) > 0:
                i = random.randint(0, n_groups)
                if i == n_groups:
                    res.append(list(force_connected))
                else:
                    res[i].extend(force_connected)

            p = Partition(res)

        return p


if __name__ == "__main__":
    dims = (3, 3)
    start = (0, 0)
    end = (dims[0]-1, dims[1]-1)
    t_size = 12
    path, p_grid = GridBuilder.random_partition_grid(dims[0], dims[1], start=start, end=end)

    t_grid = TileGrid(dims[0], dims[1], tile_size=(t_size, t_size))

    room_map = {}  # (grid_x, grid_y) -> list of room_rects
    empty_rooms = []

    for x in range(0, dims[0]):
        for y in range(0, dims[1]):
            part = p_grid.get(x, y)
            if part is not None:
                tile = Tile(t_size + 1, door_len=1, door_offs=3)
                rooms_in_tile = TileFiller.basic_room_fill(tile, part, disjoint_rooms=True, connected_rooms=True)
                rooms = [[x*t_size + r[0], y*t_size + r[1], r[2], r[3]] for r in rooms_in_tile]

                if len(rooms) > 0:
                    room_map[(x, y)] = rooms
                    empty_rooms.extend(rooms)

                t_grid.set_tile(x, y, tile)

    TileGridBuilder.clean_up_dangly_bits(t_grid)
    TileGridBuilder.clean_up_doors(t_grid)

    if len(empty_rooms) < 4:
        raise ValueError("super low number of rooms..?")

    start_placed = False
    for p in path:
        rooms_in_p = list(room_map.get(p))
        random.shuffle(rooms_in_p)
        for r in rooms_in_p:
            if r not in empty_rooms:
                continue
            if FeatureUtils.try_to_place_feature_into_rect(Features.START, t_grid, r):
                start_placed = True
                empty_rooms.remove(r)
                break
        if start_placed:
            break

    if not start_placed:
        raise ValueError("failed to place start anywhere on path...")

    end_placed = False
    for p in reversed(path):
        rooms_in_p = list(room_map.get(p))
        random.shuffle(rooms_in_p)
        for r in rooms_in_p:
            if r not in empty_rooms:
                continue
            if FeatureUtils.try_to_place_feature_into_rect(Features.EXIT, t_grid, r):
                end_placed = True
                empty_rooms.remove(r)
                break
        if end_placed:
            break

    if not start_placed:
        raise ValueError("failed to place end anywhere on path...")

    while len(empty_rooms) > 0:
        r = empty_rooms.pop()
        feat = Features.get_random_feature()
        if feat is not None and random.random() > 0.333:
            FeatureUtils.try_to_place_feature_into_rect(feat, t_grid, r)

    TileGridBuilder.add_walls(t_grid)





