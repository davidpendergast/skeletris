from enum import Enum

from src.world.worldstate import World
from src.world.entities import Player

class BossID(Enum):

    CAVE_HORROR = "CAVE_HORROR"


class BossFightController:

    def __init__(self, boss_id):
        self._boss_id = boss_id

    def get_boss_id(self):
        return self._boss_id

    def build_world(self):
        return None

    def get_opening_cinematic(self):
        return []

    def get_ending_cinematic(self):
        return []

    def update(self, world, gs, input_state, render_engine):
        pass


class CaveHorrorController(BossFightController):

    def __init__(self):
        BossFightController.__init__(self, BossID.CAVE_HORROR)

    def build_world(self):
        w = World(7, 7)
        for x in range(0, 7):
            for y in range(0, 7):
                if x == 0 or x == 6 or y == 0 or y == 6:
                    w.set_geo(x, y, World.WALL)
                else:
                    w.set_geo(x, y, World.FLOOR)
        w.add(Player(0, 0), gridcell=(2, 2), next_update=False)

        return w
    

def get_boss_controller(boss_id):
    if boss_id == BossID.CAVE_HORROR:
        return CaveHorrorController()
    else:
        return None

