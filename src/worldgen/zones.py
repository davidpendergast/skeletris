import random
import pygame

from src.world.worldstate import World
from src.worldgen.worldgen import WorldFactory, WorldBlueprint, RoomFactory, BuilderUtils
from src.utils.util import Utils
import src.world.entities as entities
import src.game.spriteref as spriteref
import src.game.npc as npc

_ALL_ZONES = {}

BLACK = (0, 0, 0)
DARK_GREY = (92, 92, 92)


class ZoneLoader:
    EMPTY = (92, 92, 92)
    WALL = (0, 0, 0)

    FLOOR = (255, 255, 255)
    FLOOR_CRACKED = (225, 225, 225)
    FLOOR_ID_LOOKUP = {FLOOR: spriteref.FLOOR_NORMAL_ID,
              FLOOR_CRACKED: spriteref.FLOOR_CRACKED_ID}

    DOOR = (0, 0, 255)
    PLAYER_SPAWN = (0, 255, 0)
    MONSTER_SPAWN = (255, 255, 0)
    CHEST_SPAWN = (255, 0, 255)
    EXIT = (255, 0, 0)

    @staticmethod
    def load_blueprint_from_file(filename, level):
        """
        returns: (BluePrint bp, dict: color -> list of (int x, int y))
        """
        try:
            filepath = "assets/zones/" + filename
            raw_img = pygame.image.load(Utils.resource_path(filepath))
            img_size = (raw_img.get_width(), raw_img.get_height())
            bp = WorldBlueprint(img_size, level)
            unknowns = {}

            for x in range(0, img_size[0]):
                for y in range(0, img_size[1]):
                    color = raw_img.get_at((x, y))
                    color = (color[0], color[1], color[2])

                    if color == ZoneLoader.EMPTY:
                        continue
                    elif color == ZoneLoader.WALL:
                        bp.set(x, y, World.WALL)
                    elif color == ZoneLoader.FLOOR:
                        bp.set(x, y, World.FLOOR)
                    elif color in ZoneLoader.FLOOR_ID_LOOKUP:
                        bp.set(x, y, World.FLOOR)
                        bp.set_alt_art(x, y, ZoneLoader.FLOOR_ID_LOOKUP[color])
                    elif color == ZoneLoader.DOOR:
                        bp.set(x, y, World.DOOR)
                    elif color == ZoneLoader.EXIT:
                        bp.set(x, y, World.FLOOR)
                        bp.exit_spawn = (x, y)
                    elif color == ZoneLoader.CHEST_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.chest_spawns.append((x, y))
                    elif color == ZoneLoader.MONSTER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.enemy_spawns.append((x, y))
                    elif color == ZoneLoader.PLAYER_SPAWN:
                        bp.set(x, y, World.FLOOR)
                        bp.player_spawn = (x, y)
                    else:
                        if color[0] == ZoneLoader.FLOOR[0]:
                            bp.set(x, y, World.FLOOR)
                        elif color[0] == ZoneLoader.WALL[0]:
                            bp.set(x, y, World.WALL)

                        pos = (x, y)
                        if color in unknowns:
                            unknowns[color].append(pos)
                        else:
                            unknowns[color] = [pos]

            return (bp, unknowns)

        except ValueError as e:
            print("failed to load " + str(filename))
            raise e


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

    def __init__(self, name, level, filename=None, bg_color=None, music_id=None):
        self.name = name
        self.zone_id = None  # gets set by init_zones()
        self.bg_color = bg_color if bg_color is not None else DARK_GREY
        self.music_id = music_id
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
        return self.music_id

    def build_world(self, gs):
        pass


class TestZone(Zone):

    ZONE_ID = "test_zone"

    def __init__(self):
        Zone.__init__(self, "Test Zone", 5)

    def build_world(self, gs):
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

                    decor = entities.DecorationEntity.wall_decoration(sprite_to_use, grid_x, grid_y, interact_text=text_to_use)
                    w.add(decor)

        # just for debugging

        p = w.get_player()

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


class DesolateCaveZone(Zone):
    """This is the tutorial / intro zone"""

    ZONE_ID = "desolate_cave"

    GLORPLE_POS_1 = (255, 150, 255)
    MUSHROOM_COLOR = (255, 175, 175)
    RAKE_COLOR = (255, 220, 175)

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave", 1, filename="desolate_cave.png")

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_file(), self.get_level())

        w = bp.build_world()

        print("unknowns={}".format(unknowns))

        glorple = entities.NpcEntity(npc.NpcID.GLORPLE)
        w.add(glorple, gridcell=unknowns[DesolateCaveZone.GLORPLE_POS_1][0])

        for pos in unknowns[DesolateCaveZone.MUSHROOM_COLOR]:
            m_sprite = random.choice(spriteref.wall_decoration_mushrooms)
            text = "it's a large cluster of mushrooms."
            mushroom_entity = entities.DecorationEntity.wall_decoration(m_sprite, pos[0], pos[1], interact_text=text)
            w.add(mushroom_entity)

        for pos in unknowns[DesolateCaveZone.RAKE_COLOR]:
            text = "it's a rake."
            rake_entity = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_rake,
                                                                    pos[0], pos[1], interact_text=text)
            w.add(rake_entity)


        return w


class SleepyForestZone(Zone):

    ZONE_ID = "sleepy_forest"

    def __init__(self):
        Zone.__init__(self, "The Sleepy Forest", 1)

    def build_world(self, gs):
        w = WorldFactory.gen_world_from_rooms(self.get_level(), num_rooms=5).build_world()
        return w


class HauntedForestZone1(Zone):

    ZONE_ID = "haunted_forest_1"

    def __init__(self):
        Zone.__init__(self, "Haunted Forest 1", 3, filename="haunted_forest_1.png", bg_color=DARK_GREY)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_file(), self.get_level())
        print("unknowns={}".format(unknowns))
        w = bp.build_world()

        return w


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_lair"

    def __init__(self):
        Zone.__init__(self, "Cave Horror's Lair", 15, filename="cave_lair.png", bg_color=BLACK)
        self._tree_color = (255, 170, 170)
        self._fight_end_door = (0, 170, 170)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)

        tree_loc = unknowns[self._tree_color][0]
        tree_sprite = entities.AnimationEntity(0, 0, spriteref.Bosses.cave_horror_idle,
                                               60, spriteref.ENTITY_LAYER, w=64*5, h=8)
        tree_sprite.set_finish_behavior(entities.AnimationEntity.LOOP_ON_FINISH)
        tree_sprite.set_x_centered(False)
        tree_sprite.set_y_centered(False)
        tree_sprite.set_x(64 * tree_loc[0] - 64)
        tree_sprite.set_y(64 * tree_loc[1] - 64 - 112*2)
        w.add(tree_sprite)

        fight_end_loc = unknowns[self._fight_end_door][0]

        return w


def init_zones():
    _ALL_ZONES.clear()
    for zone_cls in Zone.__subclasses__():
        zone_instance = zone_cls()
        zone_instance.zone_id = zone_cls.ZONE_ID
        make(zone_instance)

