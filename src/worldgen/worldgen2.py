import re
import random

FLOOR = "x"
WALL = "#"
DOOR = "0"

EMPTY = "."


class Tileish:

    def get(self, x, y):
        return EMPTY

    def w(self):
        return 0

    def h(self):
        return 0

    def __str__(self):
        res = []
        for y in range(0, self.h()):
            for x in range(0, self.w()):
                val = self.get(x, y)
                res.append(str(val) + " ")
            res.append("\n")
        return "".join(res)


class Tile(Tileish):

    def __init__(self, size):
        self.grid = []
        for i in range(0, size):
            self.grid.append([EMPTY for _ in range(0, size)])

        self._door_offs = 3
        self._door_length = 2

    def in_tile(self, x, y):
        return 0 <= x < self.w() and 0 <= y < self.h()

    def get(self, x, y):
        if self.in_tile(x, y):
            return self.grid[x][y]
        else:
            return EMPTY

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

    def coords(self):
        for x in range(0, self.w()):
            for y in range(0, self.h()):
                yield (x, y)

    def door_coords(self, door_num):
        if door_num == 0:
            return [(self._door_offs + i, 0) for i in range(0, self._door_length)]
        elif door_num == 1:
            return [(self.w() - 2 - self._door_offs + i, 0) for i in range(0, self._door_length)]
        elif door_num == 2:
            return [(self.w() - 1, self._door_offs + i) for i in range(0, self._door_length)]
        elif door_num == 3:
            return [(self.w() - 1, self.h() - 2 - self._door_offs + i) for i in range(0, self._door_length)]
        elif door_num == 4:
            return [(self.w() - 2 - self._door_offs + i, self.h() - 1) for i in range(0, self._door_length)]
        elif door_num == 5:
            return [(self._door_offs + i, self.h() - 1) for i in range(0, self._door_length)]
        elif door_num == 6:
            return [(0, self.h() - 2 - self._door_offs + i) for i in range(0, self._door_length)]
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

    def is_valid_at(self, x, y, p, direction=None):
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
            return (self.is_valid_at(x, y, p, direction=(0, -1)) and
                    self.is_valid_at(x, y, p, direction=(1, 0)) and
                    self.is_valid_at(x, y, p, direction=(0, 1)) and
                    self.is_valid_at(x, y, p, direction=(-1, 0)))

    def has_door(self, x, y, door_num):
        """returns: True, False or None if partition is None"""
        p = self.get(x, y)
        if p is None:
            return None
        else:
            return p.has_door(door_num)

    def needed_doors(self, x, y):
        res = []
        for dir in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            if not (0 <= x + dir[0] < self.w() and 0 <= y + dir[1] < self.h()):
                res.append(False)
                res.append(False)
            else:
                n = self.get(x + dir[0], y + dir[1])
                if n is None:
                    res.append(None)
                    res.append(None)
                else:
                    d1 = Tile.doors_on_side((-dir[0], -dir[1]))[0]
                    d2 = Tile.doors_on_side((-dir[0], -dir[1]))[1]
                    res.append(n.has_door(d2))  # gotta flip it because it's... mirrored?
                    res.append(n.has_door(d1))
        return res

    def __str__(self):
        return str(self.partitions)


class TileGrid(Tileish):

    def __init__(self, grid_w, grid_h, tile_size=(16, 16)):
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
        return self.get_tile(int(x / self.tile_size[0]), int(y / self.tile_size[1]))

    def get(self, x, y):
        t = self.tile_at(x, y)
        if t is None:
            return EMPTY
        else:
            rel_x = x % self.tile_size[0]
            rel_y = y % self.tile_size[1]
            return t.get(rel_x, rel_y)

    def set_tile(self, grid_x, grid_y, tile):
        self.tiles[grid_x][grid_y] = tile


class GridBuilder:

    @staticmethod
    def random_path_between(p1, p2, w, h):
        path = [p1]
        bad = []
        while path[-1] != p2:
            cur = path[-1]
            neighbors = list(TileFiller.neighbhors(cur[0], cur[1]))
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
    def random_connected_partition_path(coord_path):
        pass

    @staticmethod
    def random_partition_grid(w, h, start=None, end=None):
        start = start if start is not None else (random.randint(0, w - 1), random.randint(0, h - 1))
        end = end if end is not None else (random.randint(0, w - 1), random.randint(0, h - 1))

        path = GridBuilder.random_path_between(start, end, w, h)
        print("path={}".format(path))

        p_grid = PartitionGrid(w, h)
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
                # print("\ncur_path={}, entry_door={}, exit_door={}, door_req={}".format(cur_path, entry_door, exit_door, door_req))
                force_enabled.append(exit_door)
                if entry_door is not None:
                    force_connected = [entry_door, exit_door]

                entry_door = Tile.connecting_door(exit_door)  # setting for next loop
            # else:
                # print("\ncur_path={}, entry_door={}, door_req={}".format(cur_path, entry_door, door_req))

            p = Partition.random_partition(force_valid=True,
                                           force_doors=force_enabled,
                                           force_not_doors=force_disabled,
                                           force_connected=force_connected)

            p_grid.set(cur_path[0], cur_path[1], p)

        return p_grid


class RectUtils:

    @staticmethod
    def coords_in_rect(rect):
        for x in range(rect[0], rect[0] + rect[2]):
            for y in range(rect[1], rect[1] + rect[3]):
                yield (x, y)

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


class TileFiller:

    @staticmethod
    def neighbhors(x, y):
        yield (x + 1, y)
        yield (x, y + 1)
        yield (x - 1, y)
        yield (x, y - 1)

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
                    for (n_x, n_y) in TileFiller.neighbhors(x, y):
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
            touches = [xy for xy in TileFiller.flood_fill(tile, d_x, d_y, (DOOR, FLOOR))]
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
        tile.fill(0, 0, tile.w(), tile.h(), EMPTY)

        for i in range(0, 8):
            for (x, y) in tile.door_coords(i):
                if i in partition.as_map:
                    tile.set(x, y, DOOR)
                else:
                    tile.set(x, y, EMPTY)

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
                    tile.replace(x, y, EMPTY, FLOOR)

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
                        tile.set(x, y, FLOOR)
                    else:
                        tile.set(x, y, EMPTY)
            if TileFiller.calculate_partition(tile) == partition:
                return
        # raise ValueError("couldn't produce partition={}".format(partition))

    @staticmethod
    def basic_room_fill(tile, partition, min_rooms=1, max_rooms=4, iter_limit=300, min_size=4, max_size=7):
        TileFiller.basic_floor_fill(tile, partition)

        n = random.randint(min_rooms, max_rooms)
        iteration = 0

        while n > 0 and iteration < iter_limit:
            iteration += 1
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(1, tile.w() - w - 2)
            y = random.randint(1, tile.h() - h - 2)

            was_empty = []
            for xy in RectUtils.coords_in_rect([x, y, w, h]):
                if tile.get(xy[0], xy[1]) == EMPTY:
                    was_empty.append(xy)
                    tile.set(xy[0], xy[1], FLOOR)

            if TileFiller.calculate_partition(tile) == partition:
                # added a room successfully!
                n -= 1
            else:
                for xy in was_empty:
                    tile.set(xy[0], xy[1], EMPTY)


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

    def __repr__(self):
        res = "Partition:{}".format(self.p)
        if not self.is_valid():
            res += " (invalid)"
        return res

    def __eq__(self, other):
        return self.p == other.p  # should both have been sorted the same

    @staticmethod
    def random_partition(force_valid=True, min_doors=0, max_doors=8, force_doors=[], force_not_doors=[], force_connected=[]):

        #print(
        #    "called random_partition(force_valid={}, min_doors={}, max_doors={}, force_doors={}, force_not_doors={}, force_connected={})".format(
        #        force_valid, min_doors, max_doors, force_doors, force_not_doors, force_connected
        #    ))

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

        #print("  --> {}".format(p))
        return p

if __name__ == "__main__":
    #t = Tile(17)

    #p = Partition.random_partition(force_valid=True, min_doors=2)

    # p = Partition([[0, 3, 4, 7], [1, 2], [5, 6]])
    #TileFiller.basic_room_fill(t, p)
    #print(t)
    #print(p)

    grid_size = (3, 1)
    tile_grid = TileGrid(grid_size[0], grid_size[1])

    for x in range(0, grid_size[0]):
        for y in range(0, grid_size[1]):
            t = Tile(17)
            p = Partition.random_partition(force_valid=True, min_doors=2)
            TileFiller.basic_room_fill(t, p)
            tile_grid.set_tile(x, y, t)

    print(tile_grid)

    dims = (3, 2)
    p_grid = GridBuilder.random_partition_grid(dims[0], dims[1], start=(0, 0), end=(dims[0]-1, dims[1]-1))

    t_grid = TileGrid(dims[0], dims[1])

    for x in range(0, dims[0]):
        for y in range(0, dims[1]):
            part = p_grid.get(x, y)
            if part is not None:
                tile = Tile(17)
                TileFiller.basic_room_fill(tile, part)
                t_grid.set_tile(x, y, tile)

    print(t_grid)
    print(p_grid)


