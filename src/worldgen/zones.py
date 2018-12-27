import random
import pygame

from src.world.worldstate import World
from src.worldgen.worldgen import WorldFactory, WorldBlueprint, RoomFactory, BuilderUtils
from src.utils.util import Utils
import src.world.entities as entities
import src.game.enemies as enemies
import src.game.spriteref as spriteref
import src.game.npc as npc
import src.game.events as events
import src.game.dialog as dialog
import src.game.music as music
import src.game.cinematics as cinematics

_FIRST_ZONE = None
_ZONE_TRANSITIONS = {}
_ALL_ZONES = {}

BLACK = (0, 0, 0)
DARK_GREY = (92, 92, 92)


def first_zone():
    return _FIRST_ZONE


def init_zones():
    _ALL_ZONES.clear()
    for zone_cls in Zone.__subclasses__():
        zone_instance = zone_cls()
        zone_instance.zone_id = zone_cls.ZONE_ID
        make(zone_instance)

    global _FIRST_ZONE
    _FIRST_ZONE = DesolateCaveZone.ZONE_ID

    _ZONE_TRANSITIONS.clear()
    _ZONE_TRANSITIONS[DesolateCaveZone.ZONE_ID] = [DesolateCaveZone2.ZONE_ID]
    _ZONE_TRANSITIONS[DesolateCaveZone2.ZONE_ID] = [FrogLairZone.ZONE_ID]

    _ZONE_TRANSITIONS[DoorTestZone.ZONE_ID] = [DoorTestZoneL.ZONE_ID, DoorTestZoneR.ZONE_ID]

    _test_zone_sanity()


def _test_zone_sanity():
    if first_zone() not in _ALL_ZONES:
        raise ValueError("no first zone")

    return_ids = {}  # zone -> return_id

    for z1 in _ZONE_TRANSITIONS:
        if z1 not in _ALL_ZONES:
            raise ValueError("unrecognized id: {}".format(z1))

        for z2 in _ZONE_TRANSITIONS[z1]:
            if z2 not in _ALL_ZONES:
                raise ValueError("unrecognized id: {}".format(z2))
            if z2 in return_ids:
                raise ValueError("zone {} has multiple return zones: {}, {}".format(z2, z1, return_ids[z2]))
            else:
                return_ids[z2] = z1


def get_return_zone(zone_id):
    for z1 in _ZONE_TRANSITIONS:
        for z2 in _ZONE_TRANSITIONS[z1]:
            if z2 == zone_id:
                return z1
    return None


def get_exits(zone_id):
    if zone_id not in _ZONE_TRANSITIONS:
        return []
    else:
        return _ZONE_TRANSITIONS[zone_id]


class ZoneLoader:
    EMPTY = (92, 92, 92)
    WALL = (0, 0, 0)
    WALL_CRACKED = (30, 30, 30)

    FLOOR = (255, 255, 255)
    FLOOR_CRACKED = (225, 225, 225)
    FLOOR_ID_LOOKUP = {FLOOR: spriteref.FLOOR_NORMAL_ID,
                       FLOOR_CRACKED: spriteref.FLOOR_CRACKED_ID}
    HOLE = (100, 100, 100)

    DOOR = (0, 0, 255)
    LOCKED_DOOR = (0, 0, 130)
    SENSOR_DOOR = (100, 100, 255)
    PLAYER_SPAWN = (0, 255, 0)
    MONSTER_SPAWN = (255, 255, 0)
    CHEST_SPAWN = (255, 0, 255)
    SAVE_STATION = (0, 255, 255)

    EXIT = (255, 0, 0)
    RETURN_EXIT = (255, 50, 50)
    BOSS_EXIT = (255, 25, 25)

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

            return_id = get_return_zone(zone_id)
            exit_ids = get_exits(zone_id)

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
                        if return_id is not None:
                            bp.return_exit_spawns[return_id] = (x, y)
                            return_id = None
                        else:
                            print("WARN: no return zone for {} at ({}, {})".format(zone_id, x, y))
                    elif color in (ZoneLoader.EXIT, ZoneLoader.BOSS_EXIT):
                        bp.set(x, y, World.FLOOR)
                        if len(exit_ids) > 0:
                            exit_id = exit_ids[0]
                            exit_ids = exit_ids[1:]

                            if color == ZoneLoader.EXIT:
                                bp.exit_spawns[exit_id] = (x, y)
                            else:
                                bp.boss_exit_spawns[exit_id] = (x, y)
                        else:
                            print("WARN: no exit zone for {} at ({}, {})".format(zone_id, x, y))
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

            for exit_id in exit_ids:
                print("WARN: {} didn't create exit to zone {}".format(zone_id, exit_id))
            if return_id is not None:
                print("WARN: {} didn't create return exit to zone {}".format(zone_id, return_id))

            return bp, unknowns

        except ValueError as e:
            print("failed to load " + str(filename))
            raise e


def build_world(zone_id, gs, spawn_at_door_with_zone_id=None):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))

    zone = _ALL_ZONES[zone_id]
    gs.prepare_for_new_zone(zone_id)
    music.play_song(zone.get_music_id())

    w = zone.build_world(gs)
    w.flush_new_entity_additions()
    w.set_bg_color(zone.get_bg_color())

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        if spawn_at_door_with_zone_id is not None:
            for e in w.all_entities(onscreen=False):
                if e.is_exit() and e.get_zone() == spawn_at_door_with_zone_id:
                    e.set_open(True)
                    grid_xy = w.to_grid_coords(*e.center())
                    p = w.get_player()
                    size = w.cellsize()
                    p.set_center((grid_xy[0] + 0.5) * size, (grid_xy[1] + 0.5) * size)

        grid_xy = w.to_grid_coords(*p.center())
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)
        gs.set_world_camera_center(*p.center())

    return w


def get_zone_name(zone_id):
    if zone_id not in _ALL_ZONES:
        raise ValueError("unknown zone id: {}".format(zone_id))
    return _ALL_ZONES[zone_id].get_name()


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

                    decor = entities.DecorationEntity.wall_decoration(sprite_to_use, grid_x, grid_y,
                                                                      interact_dialog=dialog.PlayerDialog(text_to_use))
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

    MUSHROOM_COLOR = (255, 175, 175)
    MUSHROOM_COLOR_SP = (255, 175, 177)  # these can have a switch behind them
    RAKE_COLOR = (255, 220, 175)
    DIALOG_TRIGGER_1_COLOR = (255, 95, 95)

    WALL_SIGNS = {
            (255, 133, 0): ("read", "it's a schedule. it says:\n\nplanted:    5.164  5.162  8.164\n""harvests:       3      9      2"),
            (255, 186, 150): ("[i] to read", "use [i] to pick up items, interact with things, and dismiss text."),
            (255, 184, 150): ("[i] to read", "doors and chests will open on their own if you stand next to them for a little while."),
            (255, 182, 150): ("[i] to read", ["use [r] to open inventory.", "items in the top 5x5 grid are currently equipped. the bottom grid is for storage."]),
            (255, 180, 150): ("[i] to read", ["stand on the chest to open it. then, use the mouse to equip some items. right-click rotates the active item.", "you can't fit everything, so use your equipment grid squares wisely."]),
            (255, 178, 150): ("[i] to read", "use [j] to attack. you can't be hit while in the air."),
            (255, 176, 150): ("[i] to read", "use [k] to heal. healing potions can be collected from chests and slain enemies."),
            (255, 174, 150): ("[i] to read", "the controls are also on the hotbar at the bottom of the screen."),
            (255, 172, 150): ("[i] to read", "good luck! deaths are permanent.")
    }

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave", 1, filename="desolate_cave.png",
                      music_id=music.Songs.AN_ADVENTURE_UNFOLDS)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
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
                action = lambda _e, _w, _gs, : nearest_door.do_unlock()
                listener = events.EventListener(action, events.EventType.DIALOG_EXIT,
                                                lambda event: event.get_uid() == unlock_dialog.get_uid(),
                                                single_use=True)
                gs.add_trigger(listener)
                mushroom_entity = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_switches,
                                                                            pos[0], pos[1],
                                                                            interact_dialog=unlock_dialog,
                                                                            hover_text="activate")
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
                                                                 interact_dialog=d, hover_text=hover_text)
                w.add(sign)

        wasd_message_pos = bp.player_spawn
        wasd_message_box = entities.MessageTriggerBox("[WASD] to move", wasd_message_pos, delay=120, just_once=False)
        w.add(wasd_message_box)

        return w


class DesolateCaveZone2(Zone):

    ZONE_ID = "desolate_cave_2"

    def __init__(self):
        Zone.__init__(self, "The Desolate Cave II", 1, filename="desolate_cave_2.png",
                      music_id=music.Songs.AN_ADVENTURE_UNFOLDS)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w

    def get_return_id(self):
        return DesolateCaveZone.ZONE_ID


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
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        print("unknowns={}".format(unknowns))
        w = bp.build_world()

        return w


class FrogLairZone(Zone):

    ZONE_ID = "frog_lair"

    FROG_SPAWN = (255, 203, 203)

    def __init__(self):
        Zone.__init__(self, "The Dark Pool", 15, filename="frog_lair.png", bg_color=BLACK)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()
        w.set_wall_type(spriteref.WALL_NORMAL_ID)
        w.set_floor_type(spriteref.FLOOR_NORMAL_ID)

        frog_spawn = unknowns[FrogLairZone.FROG_SPAWN][0]
        frog_entity = enemies.EnemyFactory.gen_enemy(self.get_level(), force_template=enemies.TEMPLATE_FROG_BOSS)
        w.add(frog_entity, gridcell=frog_spawn)

        def kill_action(_event, _world, _gs):
            print("INFO: unlocking all doors")
            for e in _world.all_entities(onscreen=False):
                if e.is_door() and e.is_locked():
                    e.do_unlock()

        gs.add_trigger(events.EventListener(kill_action, events.EventType.ENEMY_KILLED,
                                            lambda evt: evt.get_uid() == frog_entity.get_uid(),
                                            single_use=True))

        gs.play_cinematic(cinematics.frog_intro)

        return w

    def get_music_id(self):
        return music.Songs.AMPHIBIAN


class CaveHorrorZone(Zone):

    ZONE_ID = "cave_lair"

    def __init__(self):
        Zone.__init__(self, "Cave Horror's Lair", 15, filename="cave_lair.png", bg_color=BLACK)
        self._tree_color = (255, 170, 170)
        self._fight_end_door = (0, 170, 170)

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
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


class DoorTestZone(Zone):

    ZONE_ID = "door_test"

    def __init__(self):
        Zone.__init__(self, "Main Zone", 15, filename="door_test_1.png")

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


class DoorTestZoneL(Zone):

    ZONE_ID = "door_test_l"

    def __init__(self):
        Zone.__init__(self, "Test Zone Left", 17, filename="door_test_L.png")

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


class DoorTestZoneR(Zone):

    ZONE_ID = "door_test_r"

    def __init__(self):
        Zone.__init__(self, "Test Zone Right", 17, filename="door_test_R.png")

    def build_world(self, gs):
        bp, unknowns = ZoneLoader.load_blueprint_from_file(self.get_id(), self.get_file(), self.get_level())
        w = bp.build_world()

        return w


