import random

from src.world.worldstate import World
from src.game.enemies import EnemyFactory
from src.world.entities import Player, ExitEntity, DoorEntity, ChestEntity


class WorldBlueprint:

    def __init__(self, size, level):
        self.size = size
        self.level = level
        self.geo = []
        for i in range(0, size[0]):
            self.geo.append([World.EMPTY] * size[1])

        self.player_spawn = [1, 1]
        self.enemy_spawns = []
        self.chest_spawns = []
        self.exit_spawn = [2, 1]

    def get(self, x, y):
        if self.is_valid(x, y):
            return self.geo[x][y]
        else:
            return World.EMPTY

    def set(self, x, y, val):
        if self.is_valid(x, y):
            self.geo[x][y] = val

    def is_valid(self, x, y):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1]

    def build_world(self):
        w = World(*self.size)
        for x in range(0, self.size[0]):
            for y in range(0, self.size[1]):
                w.set_geo(x, y, self.geo[x][y])
                if self.geo[x][y] == World.DOOR:
                    w.add(DoorEntity(x, y))

        for spawn_pos in self.enemy_spawns:
            enemies = EnemyFactory.gen_enemies(self.level)
            for e in enemies:
                w.add(e, gridcell=spawn_pos)

        for chest_pos in self.chest_spawns:
            w.add(ChestEntity(0, 0), gridcell=chest_pos)

        w.add(Player(0, 0), gridcell=self.player_spawn)
        w.add(ExitEntity(*self.exit_spawn))

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


class WorldFactory:
    MAX_SIZE = (15, 10)
    ROOM_NUM_BOUNDS = [10, 30]

    @staticmethod
    def gen_world(level):
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

        return bp
