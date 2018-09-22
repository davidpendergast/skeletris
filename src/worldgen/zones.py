import random

from src.worldgen.worldgen import WorldFactory, WorldBlueprint, RoomFactory, BuilderUtils
import src.world.entities as entities
import src.game.spriteref as spriteref

_ALL_ZONES = {}

BLACK = (0, 0, 0)
DARK_GREY = (92, 92, 92)


def build_world(zone_id, gs):
    zone = _ALL_ZONES[zone_id]
    if zone is None:
        raise ValueError("unknown zone id: {}".format(zone_id))

    w = zone.build_world(gs)
    w.set_bg_color(zone.get_bg_color())

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        grid_xy = w.to_grid_coords(*p.center())
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)

    return w


def make(zone):
    _ALL_ZONES[zone.get_id()] = zone
    print("created zone: {}".format(zone.get_id()))


class Zone:

    def __init__(self, name, level, bg_color=DARK_GREY, music_id=None):
        self.name = name
        self.zone_id = None  # gets set by init_zones()
        self.bg_color = bg_color
        self.music_id = music_id
        self.level = level

    def get_name(self):
        return self.name

    def get_id(self):
        return self.zone_id

    def get_level(self):
        return self.level

    def get_bg_color(self):
        return self.bg_color

    def get_music_id(self):
        return self.music_id

    def build_world(self, gs):
        pass


class SleepyForestZone(Zone):

    ZONE_ID = "sleepy_forest"

    def __init__(self):
        Zone.__init__(self, "The Sleepy Forest", 1)

    def build_world(self, gs):
        w = WorldFactory.gen_world_from_rooms(self.get_level(), num_rooms=5).build_world()

        # just for debugging

        p = w.get_player()

        import src.world.entities as entities
        import src.game.npc as npc
        mayor = entities.NpcEntity(npc.NpcID.MAYOR)
        mayor.set_x(p.x() + 64)
        mayor.set_y(p.y())
        w.add(mayor)
        mary_skelly = entities.NpcEntity(npc.NpcID.MARY_SKELLY)
        mary_skelly.set_x(p.x() + 72)
        mary_skelly.set_y(p.y() + 48)
        w.add(mary_skelly)
        beanskull = entities.NpcEntity(npc.NpcID.BEANSKULL)
        beanskull.set_x(p.x() - 16)
        beanskull.set_y(p.y() + 32)
        w.add(beanskull)
        glorple = entities.NpcEntity(npc.NpcID.GLORPLE)
        glorple.set_x(p.x() - 50)
        glorple.set_y(p.y() - 50)
        w.add(glorple)
        return w


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_lair"

    def __init__(self):
        Zone.__init__(self, "Cave Horror's Lair", 15, bg_color=BLACK)

    def build_world(self, gs):
        bp = WorldBlueprint((35, 35), self.get_level())
        rooms = []
        boss_room = RoomFactory.gen_rectangular_room(5, 5)  # 7 x 7 total
        boss_room.set_offset(1, 1)
        rooms.append(boss_room)

        boss_hallway = RoomFactory.gen_rectangular_room(1, 16)  # 3 x 17
        boss_hallway.set_offset(3, 7)
        boss_hallway.add_neighbor(boss_room, (3, 6))
        rooms.append(boss_hallway)

        for r in rooms:
            bp.add_room(r)

        WorldFactory.fill_corners(bp)

        bp.player_spawn = (3, 22)

        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        for floor_xy in boss_room.all_floors():
            if random.random() < 0.15:
                w.set_floor_type(spriteref.FLOOR_CRACKED_ID, xy=floor_xy)

        tree_sprite = entities.AnimationEntity(0, 0, spriteref.Bosses.cave_horror_idle, 60, spriteref.ENTITY_LAYER, w=64*5, h=8)
        tree_sprite.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
        room_bounds = boss_room.get_bounds()
        tree_sprite.set_x_centered(False)
        tree_sprite.set_y_centered(False)
        tree_sprite.set_x(room_bounds[0])
        tree_sprite.set_y(room_bounds[1] - 112*2)
        w.add(tree_sprite)

        return w


def init_zones():
    _ALL_ZONES.clear()
    for zone_cls in Zone.__subclasses__():
        zone_instance = zone_cls()
        zone_instance.zone_id = zone_cls.ZONE_ID
        make(zone_instance)

