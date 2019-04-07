import re
import random

EMPTY = "."
FLOOR = "x"
WALL = "#"
DOOR = "0"


class Tile:

    def __init__(self, size):
        self.grid = []
        for i in range(0, size):
            self.grid.append([" " for _ in range(0, size)])

        self._door_offs = 3
        self._door_length = 2

    def in_tile(self, x, y):
        return 0 <= x < self.w() and 0 <= y < self.h()

    def get(self, x, y):
        return self.grid[x][y]

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

    def __str__(self):
        res = []
        for y in range(0, self.h()):
            for x in range(0, self.w()):
                val = self.get(x, y)
                res.append(str(val) + " ")
            res.append("\n")
        return "".join(res)


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
        return [i for i in [0, 1, 2, 3, 4, 5, 6, 7] if i in self.as_map]

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

    def __str__(self):
        res = "Partition:{}".format(self.p)
        if not self.is_valid():
            res += " (invalid)"
        return res

    def __eq__(self, other):
        return self.p == other.p  # should both have been sorted the same

    @staticmethod
    def random_partition(min_doors=0, max_doors=8):
        num_doors = random.randint(min_doors, max_doors)
        doors = list(random.sample([0, 1, 2, 3, 4, 5, 6, 7], num_doors))
        if len(doors) == 0:
            return Partition([])

        n_groups = 1 + int((len(doors) - 1) * random.random())
        res = []
        random.shuffle(doors)
        for i in range(0, n_groups):
            res.append([doors[i]])
        if n_groups == len(doors):
            return Partition(res)

        for i in range(n_groups, len(doors)):
            res[int(n_groups * random.random())].append(doors[i])

        return Partition(res)


if __name__ == "__main__":
    t = Tile(17)

    p = None
    while p is None or not p.is_valid():
       p = Partition.random_partition(min_doors=2)

    # p = Partition([[0, 3, 4, 7], [1, 2], [5, 6]])
    TileFiller.basic_room_fill(t, p)
    print(t)
    print(p)

