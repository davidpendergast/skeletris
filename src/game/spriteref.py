import pygame
import math

import string
import collections

from src.items.cubeutils import CubeUtils
from src.utils.util import Utils
from src.game.messages import Messages

from src.renderengine.img import ImageModel 

FLOOR_LAYER = 0
SHADOW_LAYER = 5
WALL_LAYER = 10
ENTITY_LAYER = 15
UI_0_LAYER = 20
UI_TOOLTIP_LAYER = 25

"""Layers that follow the player"""
WORLD_LAYERS = (FLOOR_LAYER, SHADOW_LAYER,
                WALL_LAYER, ENTITY_LAYER)

all_imgs = []


class Cinematics:
    cine_size = (128, 72)

    # all of these are lists of ImageModels
    blank = None
    cave_horrors = None
    intro_skel_ghost_things = None
    intro_skel_slide = None
    intro_thing_slide = None
    intro_ghost_slide = None
    intro_fighting_slide = None
    frog_eye = None
    frog_body = None

    @staticmethod
    def convert(orig_coords, offset):
        if isinstance(orig_coords, list):
            return [Cinematics._convert_single(x, offset) for x in orig_coords]
        else:
            return Cinematics._convert_single(orig_coords, offset)

    @staticmethod
    def _convert_single(coord, offset):
        size = Cinematics.cine_size
        return make(offset[0] + coord[0] * size[0],
                   offset[1] + coord[1] * size[1],
                   size[0], size[1])


class Items:
    piece_small = None
    piece_small_inverted = None
    piece_bigs = []
    item_entities = {}  # cubes -> sprite

    spear_big = None
    sword_big = None
    whip_big = None
    shield_alt_big = None
    shield_big = None
    wand_big = None
    dagger_big = None
    axe_big = None
    bow_big = None
    potion_big = None

    spear_small = None
    sword_small = None
    dagger_small = None
    shield_alt_small = None
    shield_small = None
    axe_small = None
    bow_small = None
    whip_small = None
    wand_small = None
    potion_small = None

    misc_small = None

    spear_icon = None
    sword_icon = None
    axe_icon = None
    whip_icon = None
    unarmed_icon = None
    bow_icon = None
    potion_icon = None
    dagger_icon = None
    shield_icon = None
    magic_icon =None


class UI:
    item_panel_top = None
    item_panel_middle = None
    item_panel_bottom_0 = None
    item_panel_bottom_1 = None  # if no bonus attributes

    inv_panel_top = None
    inv_panel_mid = None
    inv_panel_bot = None

    world_cursors = []

    tooltip_bg = None

    """
    0 1 2
    3 4 5
    6 7 8
    """
    text_panel_edges = []
    hover_text_edges = []
    hover_text_bottom_arrow = None

    status_bar_base = None
    health_bar_top = None
    health_bar_full = None
    health_bars_with_length = []
    status_bar_action_border = None

    locked_door_panel = None

    attack_action = None
    potion_action = None
    inspect_action = None
    inventory_action = None

    @staticmethod
    def get_health_bar(pcnt_full):
        return UI.health_bars_with_length[round(pcnt_full * 256)]


    class Cursors:

        arrow_cursor_sprite = None
        hand_cursor_sprite = None

        arrow_cursor = None
        hand_cursor = None

        @staticmethod
        def init_cursors(sheet):
            UI.Cursors.arrow_cursor = UI.Cursors.sprite_to_cursor(UI.Cursors.arrow_cursor_sprite.rect(), sheet)
            print("INFO: arrow_cursor={}".format(UI.Cursors.arrow_cursor))

            UI.Cursors.hand_cursor = UI.Cursors.sprite_to_cursor(UI.Cursors.hand_cursor_sprite.rect(), sheet, hotspot=(5, 3))
            print("INFO: hand_cursor={}".format(UI.Cursors.hand_cursor))

        @staticmethod
        def sprite_to_cursor(cursor_rect, sheet, hotspot=(0, 0)):
            lines = []
            width = 8 * (cursor_rect[2] // 8)
            height = 8 * (cursor_rect[3] // 8)
            for y in range(0, height):
                lines.append("")
                for x in range(0, width):
                    if x < cursor_rect[2] and y < cursor_rect[3]:
                        pos = (cursor_rect[0] + x, cursor_rect[1] + y)
                        c = sheet.get_at(pos)
                        if c[3] == 0:
                            lines[-1] = lines[-1] + " "
                        elif c[0] == 0:
                            lines[-1] = lines[-1] + "X"
                        else:
                            lines[-1] = lines[-1] + "."
                    else:
                        lines[-1] = lines[-1] + " "

            and_and_xors = pygame.cursors.compile(lines, black="X", white=".", xor="o")
            return ((width, height), hotspot, and_and_xors[0], and_and_xors[1])


class Bosses:

    cave_horror_idle = []

    frog_idle_1 = []
    frog_idle_2 = []
    frog_idle_mouth = []
    frog_idle_down = []
    frog_airborn_rising = []
    frog_airborn_falling = []


class Font:
    _alphabet = {}  # str -> img
    _char_mappings = {
        "→": chr(16),
        "←": chr(17),
        "↑": chr(24),
        "↓": chr(25),
        "░": chr(176),
        "▒": chr(177),
        "▓": chr(178),
        "█": chr(219),
        "▄": chr(220),
        "▀": chr(223),
    }

    @staticmethod
    def get_char(c):
        if c in Font._char_mappings:
            c = Font._char_mappings[c]

        if c in Font._alphabet:
            return Font._alphabet[c]
        elif "?" in Font._alphabet:
            return Font._alphabet["?"]
        else:
            return None


def make(x, y, w, h, shift=(0, 0), and_add_to_list=None):
    img = ImageModel(x + shift[0], y + shift[1], w, h)
    all_imgs.append(img)

    if and_add_to_list is not None:
        and_add_to_list.append(img)

    return img


player_idle_0 = make(0, 0, 16, 32)
player_idle_1 = make(16, 0, 16, 32)
player_idle_all = [player_idle_0, player_idle_1]

player_move_0 = make(32, 0, 16, 32)
player_move_1 = make(48, 0, 16, 32)
player_move_2 = make(64, 0, 16, 32)
player_move_3 = make(80, 0, 16, 32)
player_move_all = [player_move_0, player_move_1, player_move_2, player_move_3]

player_idle_arms_up_all = [make(160, 0, 16, 32), make(176, 0, 16, 32)]
player_move_arms_up_all = [make(192 + 16*i, 0, 16, 32) for i in range(0, 4)]


def get_player_sprites(moving, holding_item):
    if moving:
        if holding_item:
            return player_move_arms_up_all
        else:
            return player_move_all
    else:
        if holding_item:
            return player_idle_arms_up_all
        else:
            return player_idle_all


player_death_seq = [make(112 + 32*i, 208, 32, 32) for i in range(0, 5)]

player_attacks = [make(i*16, 208, 16, 64) for i in range(0, 5)]
player_squat = make(80, 240, 16, 32)
player_little_jump_down = [make(128 + i*16, 272, 16, 48) for i in range(0, 6)]

player_faces = [make(96 + i * 32, 0, 32, 32) for i in range(0, 2)]

att_circles = [make(112 + 48*i, 240, 48, 32) for i in range(0, 9)]

att_circle_min_size = 48
att_circle_max_size = 48 * 3
att_circles_real = []  # list of lists of frames, sorted by size, frame idx


def get_attack_circles(size):
    size_prog = (size - att_circle_min_size) / (att_circle_max_size - att_circle_min_size)
    size_idx = int(Utils.bound(size_prog, 0, 0.999) * len(att_circles_real))
    return att_circles_real[size_idx]


chest_closed = make(0, 32, 16, 16)
chest_open_0 = make(16, 32, 16, 16)
chest_open_1 = make(32, 32, 16, 16)
chest_open_all = [chest_open_0, chest_open_1]

door_v = [make(736 + i*16, 0, 16, 16) for i in range(0, 7)]
door_v_locked = [make(736 + i*16, 48, 16, 16) for i in range(0, 7)]
door_v_sensor = [make(736 + i*16, 96, 16, 16) for i in range(0, 7)]

door_h = [make(736 + i*16, 16, 16, 32) for i in range(0, 7)]
door_h_locked = [make(736 + i*16, 64, 16, 32) for i in range(0, 7)]
door_h_sensor = [make(736 + i*16, 112, 16, 32) for i in range(0, 7)]

return_door_smoke = [make(608 + i*16, 240, 16, 16) for i in range(0, 16)]

boss_door_idle = [make(224 + i*16, 80, 16, 32) for i in range(0, 2)]
boss_door_opening = [make(256 + i*16, 80, 16, 32) for i in range(0, 7)]
normal_door_idle = [make(224 + i*16, 112, 16, 32) for i in range(0, 2)]
normal_door_opening = [make(256 + i*16, 112, 16, 32) for i in range(0, 7)]

large_decs = []
wall_decoration_mushrooms = [make(0 + 32*i, 352, 32, 24, and_add_to_list=large_decs) for i in range(0, 3)]

smol_decs = []
wall_decoration_bucket = make(0, 384, 8, 16, and_add_to_list=smol_decs)
wall_decoration_plant_1 = make(8, 376, 8, 24, and_add_to_list=smol_decs)
wall_decoration_plant_2 = make(16, 376, 8, 24, and_add_to_list=smol_decs)
wall_decoration_rake = make(24, 376, 8, 24, and_add_to_list=smol_decs)
wall_decoration_bones = make(32, 376, 8, 24, and_add_to_list=smol_decs)
wall_decoration_sign = make(40, 376, 8, 24, and_add_to_list=smol_decs)
wall_decoration_switches = [make(64, 376, 16, 24), make(80, 376, 16, 24)]

standalone_sign_decoration = make(96, 368, 16, 16)

save_stations = [make(0 + 16*i, 304, 16, 32) for i in range(0, 8)]
save_station_faces = [make(272, 272 + i*32, 32, 32) for i in range(0, 2)]

enemy_glorple_all = [make(0, 144, 32, 32), make(0, 176, 32, 32)]
enemy_trilla_all = [make(32, 144, 32, 32), make(32, 176, 32, 32)]
enemy_dicel_all = [make(64, 144, 32, 32), make(64, 176, 32, 32)]
enemy_flappum_all = [make(96, 144, 32, 32), make(96, 176, 32, 32)]
enemy_muncher_all = [make(128, 144, 32, 32), make(128, 176, 32, 32)]
enemy_muncher_small_all = [make(352, 144, 32, 32), make(352, 176, 32, 32)]
enemy_muncher_alt_all = [make(160, 144, 32, 32), make(160, 176, 32, 32)]
enemy_muncher_small_alt_all = [make(384, 144, 32, 32), make(384, 176, 32, 32)]
enemy_small_trilla_all = [make(192, 176 + i * 16, 16, 16) for i in range(0, 2)]
enemy_cyclops_all = [make(208, 144 + i * 32, 32, 32) for i in range(0, 2)]
enemy_the_fallen_all = [make(240, 144 + i * 32, 16, 32) for i in range(0, 2)]
enemy_skelekid_all = [make(256, 144 + i * 32, 16, 32) for i in range(0, 2)]
enemy_fungoi_all = [make(416, 144 + i * 32, 32, 32) for i in range(0, 2)]
enemy_fungoi_down = [make(448, 176 + i * 16, 32, 16) for i in range(0, 2)]

floaty_guys = [make(192, 144 + i * 16, 16, 16) for i in range(0, 2)]

mary_skelly_all = [make(272, 144 + i*32, 16, 32) for i in range(0, 2)]
mary_skelly_faces = [make(272, 208 + i*32, 32, 32) for i in range(0, 2)]

mayor_pumpkin_all = [make(304, 144 + i*32, 32, 32) for i in range(0, 2)]
mayor_pumpkin_faces = [make(304, 208 + i*32, 32, 32) for i in range(0, 2)]

beanskull_all = [make(336, 144 + i*32, 16, 32) for i in range(0, 2)]
beanskull_faces = [make(336, 208 + i*32, 32, 32) for i in range(0, 2)]

glorple_faces = [make(368, 208 + i*32, 32, 32) for i in range(0, 2)]
skullboy_faces = [make(268, 272 + i*32, 32, 32) for i in range(0, 2)]

spinny_cubes = [make(0 + i*16, 352, 16, 16) for i in range(0, 6)]
spinny_cubes_fat = [make(0 + i*16, 368, 16, 16) for i in range(0, 6)]

doctor_all = [make(480 + i * 16, 176, 16, 32) for i in range(0, 2)]
doctor_faces = [make(336, 272 + i * 32, 32, 32) for i in range(0, 2)]


def get_item_entity_sprite(cubes):
    if cubes in Items.item_entities:
        return Items.item_entities[cubes]
    else:
        # this could break in so many ways, better to fail somewhat gracefully
        print("ERROR: Failed to get entity sprite for item: {}".format(cubes))
        return player_idle_0


small_shadow = make(80, 32, 16, 8)
medium_shadow = make(80, 40, 16, 8)
large_shadow = make(96, 32, 32, 8)
enormous_shadow = make(128, 32, 48, 16)
chest_shadow = make(96, 40, 32, 8)

floor_shadows = [make(176 + i, 32, 1, 1) for i in range(0, 8)]


def get_floor_lighting(val):
    darkness_val = Utils.bound(1-val, 0.0, 0.99)
    idx = int(darkness_val * len(floor_shadows))
    return floor_shadows[idx]


end_level_consoles = [make(i*16, 272, 16, 32) for i in range(0, 8)]
explosions = [make(i*16, 128, 16, 16) for i in range(0, 8)]
progress_spinner = [make((i // 4) * 16, (i % 4) * 4 + 336, 16, 4) for i in range(0, 16)]

_cached_text = set()
_cached_text.update(["att:", "def:", "vit:", "miss", "dodge", "inventory",
                     "lvl:", "room:", "kill:", "hp:"])
for i in range(1, 10):
    _cached_text.add("+0.{}".format(i))
for i in range(1, 100):
    _cached_text.add("+{}".format(i))
    _cached_text.add("-{}".format(i))
for message in Messages:
    for word in message.value.split():  # split on whitespace
        _cached_text.add(word)

print("caching text: {}".format(_cached_text))

_cached_lengths = set([len(t) for t in _cached_text])
cached_text_imgs = {}


def split_text(text, add_to=None):
    if add_to is None:
        add_to = []

    if len(text) == 0:
        return add_to
    elif len(text) == 1:
        add_to.append(text)
        return add_to
    else:
        for length in _cached_lengths:
            if len(text) >= length:
                if text[:length] in cached_text_imgs:
                    add_to.append(text[:length])
                    split_text(text[length:], add_to)
                    return add_to
        add_to.append(text[0])
        split_text(text[1:], add_to)
        return add_to


"""Lookup table for wall sprites:   
       0    1    2
    * -- * -- * -- *
    |  1 |  2 |  4 |
    * -- * -- * -- *
  7 |128 |  x |  8 | 3
    * -- * -- * -- *
    | 64 | 32 | 16 |
    * -- * -- * -- *  
       6    5    4
"""
walls = [None] * 256
walls_black = [None] * 256
walls_cracked = [None] * 256

WALL_NORMAL_ID = 0
WALL_BLACK_ID = 1
WALL_CRACKED_ID = 2

_wall_lookup = [walls, walls_black, walls_cracked]
_root_pos = (472, 32)
_wall_types = [(walls, [_root_pos[0], _root_pos[1], 64, 32]),
               (walls_cracked, [_root_pos[0], _root_pos[1] + 32, 64, 32]),
               (walls_black, [_root_pos[0], _root_pos[1] + 64, 64, 32])]


def get_wall(encoding, wall_type_id=WALL_NORMAL_ID):
    return _wall_lookup[wall_type_id][encoding]


"""Lookup table for floor sprites:
    * -- * -- *
    |  2 |  4 |
    * -- * -- *
    |  1 |  x |
    * -- * -- * 
"""
floor_hidden = make(608, 16, 16, 16)
floor_totally_dark = make(624, 16, 16, 16)
floors = [make(608 + i*16, 32, 16, 16) for i in range(0, 8)]
floors_alt = [make(608 + i*16, 48, 16, 16) for i in range(0, 8)]
floors_cracked = [make(608 + i*16, 64, 16, 16) for i in range(0, 8)]
floors_dark_cracked = [make(608 + i*16, 80, 16, 16) for i in range(0, 8)]
floors_hole = [make(608 + i*16, 96, 16, 16) for i in range(0, 8)]
floors_fancy = [make(608 + i*16, 112, 16, 16) for i in range(0, 8)]
floors_swamp = [make(608 + i*16, 128, 16, 16) for i in range(0, 8)]
floors_pit = [make(608 + i*16, 144, 16, 16) for i in range(0, 8)]

floor_busting_open = [make(128 + i*16, 368, 16, 16) for i in range(0, 5)]
floor_busting_open_player_frames = [make(128 + i*16, 320, 16, 48) for i in range(0, 4)]
floor_burst_shards = [make(128 + i*16, 384, 16, 16) for i in range(0, 4)]

FLOOR_NORMAL_ID = 0
FLOOR_QUAD_ID = 1
FLOOR_CRACKED_ID = 2
FLOOR_DARK_CRACKED_ID = 3
FLOOR_HOLE_ID = 4
FLOOR_FANCY_ID = 5
FLOOR_SWAMP_ID = 6
FLOOR_PIT_ID = 7
_floor_types = [floors, floors_alt, floors_cracked, floors_dark_cracked,
                 floors_hole, floors_fancy, floors_swamp, floors_pit]

floor_darkness_resolution = 8  # adjustable, used to generate floor sprites
_floor_lookup = {}  # (floor_id, encoding, darkness) -> ImageModel

for floor_id in range(0, len(_floor_types)):
    for floor_encoding in range(0, 8):
        _floor_lookup[(floor_id, floor_encoding, 0)] = _floor_types[floor_id][floor_encoding]


def get_floor(encoding, floor_type_id=FLOOR_NORMAL_ID, darkness_level=0.0):
    dark_idx = Utils.bound(int(darkness_level * floor_darkness_resolution), 0, floor_darkness_resolution - 1)
    key = (floor_type_id, encoding, dark_idx)
    if key in _floor_lookup:
        return _floor_lookup[key]
    else:
        print("WARN: floor sprite not found for (encoding={}, id={}, darkness={})".format(
            encoding, floor_type_id, darkness_level))
        return _floor_lookup[(0, FLOOR_NORMAL_ID, 0)]


def _get_wall_corner_loc(spot, bools, wall_pieces):
    if spot == "TL":
        y = 0
        x = 1*bools[7] + 2*bools[0] + 4*bools[1]
    elif spot == "TR":
        y = 1
        x = 1*bools[3] + 2*bools[2] + 4*bools[1]
    elif spot == "BL":
        y = 2
        x = 1*bools[7] + 2*bools[6] + 4*bools[5]
    else:
        y = 3
        x = 1*bools[3] + 2*bools[4] + 4*bools[5]
        
    return (wall_pieces[0] + x*8, wall_pieces[1] + y*8, 8, 8)


def _draw_ellipse(sheet, center, width, height, opacity):
    color = (255, 255, 255)
    rect = [center[0] - width, center[1] - height, width * 2, height * 2]
    pygame.draw.ellipse(sheet, color, rect, 1)

    for x in range(rect[0], rect[0] + rect[2]):
        for y in range(rect[1], rect[1] + rect[3]):
            # it's good enoughTM don't @ me
            if x < 0 or x >= sheet.get_width() or y < 0 or y >= sheet.get_height():
                continue
            if sheet.get_at((x, y)) == color:
                sheet.set_at((x, y), (color[0], color[1], color[2], int(opacity*255)))


cooldown_overlays = []


def get_cooldown_img(progress):
    return cooldown_overlays[int(progress * len(cooldown_overlays))]


def _draw_cd_image(sheet, rect, prog, color):
    c_x = rect[0] + rect[2] / 2
    c_y = rect[1] + rect[3] / 2
    for x in range(rect[0], rect[0] + rect[2]):
        for y in range(rect[1], rect[1] + rect[3]):
            if x % 2 == y % 2:
                continue
            angle_prog = (math.atan2(c_y - y, c_x - x) + math.pi) / (2 * math.pi)
            if angle_prog > prog:
                sheet.set_at((x, y), color)


def _draw_dark_floor(sheet, darkness, src_rect, dest_rect):
    sheet.blit(sheet, dest_rect, src_rect)

    MAX_CHANGE = 224

    for x in range(dest_rect[0], dest_rect[0] + dest_rect[2]):
        for y in range(dest_rect[1], dest_rect[1] + dest_rect[3]):
            rgb = list(sheet.get_at((x, y)))
            for i in range(0, 3):
                val = rgb[i] / 255
                new_val = (1 - darkness) * val ** (1 / (1 - darkness))
                new_val = max(val - MAX_CHANGE, new_val)
                rgb[i] = int(255 * new_val)
            sheet.set_at((x, y), rgb)


def build_cine_sheet(start_pos, raw_cine_img, sheet):
    sheet.blit(raw_cine_img, start_pos)

    cs = Cinematics
    cs.blank = cs.convert([(4, 0)], start_pos)
    cs.cave_horrors = cs.convert([(0, 0), (1, 0)], start_pos)
    cs.intro_skel_ghost_things = cs.convert([(2, 0), (3, 0)], start_pos)
    cs.intro_thing_vs_skeleton = cs.convert([(0, 1), (1, 1)], start_pos)
    cs.intro_fighting_slide = cs.convert([(0, 1), (1, 1)], start_pos)
    cs.intro_skel_slide = cs.convert([(2, 1), (3, 1)], start_pos)
    cs.intro_ghost_slide = cs.convert([(0, 2), (1, 2)], start_pos)
    cs.intro_thing_slide = cs.convert([(4, 1), (5, 1)], start_pos)
    cs.frog_eye = cs.convert([(2, 2), (3, 2)], start_pos)
    cs.frog_body = cs.convert([(4, 2), (5, 2)], start_pos)


def build_items_sheet(start_pos, raw_item_img, sheet):
    sheet.blit(raw_item_img, start_pos)
    Items.piece_small = make(96, 80, 4, 4, shift=start_pos)
    Items.piece_small_inverted = make(100, 80, 4, 4, shift=start_pos)
    Items.piece_bigs = [make(112 + i * 16, 80, 16, 16, shift=start_pos) for i in range(0, 6)]
    Items.item_entities = {}  # cubes -> sprite

    Items.spear_big = make(0, 0, 16, 64, shift=start_pos)
    Items.sword_big = make(16, 0, 16, 48, shift=start_pos)
    Items.whip_big = make(16, 48, 32, 32, shift=start_pos)
    Items.shield_alt_big = make(32, 0, 32, 32, shift=start_pos)
    Items.shield_big = make(48, 48, 32, 32, shift=start_pos)
    Items.wand_big = make(64, 0, 16, 48, shift=start_pos)
    Items.dagger_big = make(80, 48, 16, 32, shift=start_pos)
    Items.axe_big = make(80, 0, 32, 48, shift=start_pos)
    Items.bow_big = make(112, 0, 16, 48, shift=start_pos)
    Items.potion_big = make(144, 48, 16, 16, shift=start_pos)

    Items.spear_small = make(128, 0, 5, 16, shift=start_pos)
    Items.sword_small = make(133, 3, 5, 13, shift=start_pos)
    Items.dagger_small = make(138, 8, 5, 8, shift=start_pos)
    Items.shield_alt_small = make(143, 9, 7, 7, shift=start_pos)
    Items.shield_small = make(153, 7, 7, 9, shift=start_pos)
    Items.axe_small = make(160, 4, 7, 12, shift=start_pos)
    Items.bow_small = make(171, 5, 5, 11, shift=start_pos)
    Items.whip_small = make(176, 7, 8, 9, shift=start_pos)
    Items.wand_small = make(187, 7, 5, 9, shift=start_pos)
    Items.potion_small = make(198, 8, 6, 8, shift=start_pos)

    Items.misc_small = make(192, 12, 5, 4, shift=start_pos)

    Items.spear_icon = make(0, 80, 10, 10, shift=start_pos)
    Items.sword_icon = make(10, 80, 10, 10, shift=start_pos)
    Items.axe_icon = make(20, 80, 10, 10, shift=start_pos)
    Items.whip_icon = make(30, 80, 10, 10, shift=start_pos)
    Items.unarmed_icon = make(40, 80, 10, 10, shift=start_pos)
    Items.bow_icon = make(0, 90, 10, 10, shift=start_pos)
    Items.potion_icon = make(10, 90, 10, 10, shift=start_pos)
    Items.dagger_icon = make(20, 90, 10, 10, shift=start_pos)
    Items.shield_icon = make(30, 90, 10, 10, shift=start_pos)
    Items.magic_icon = make(40, 90, 10, 10, shift=start_pos)


def build_ui_sheet(start_pos, raw_ui_img, sheet):
    sheet.blit(raw_ui_img, start_pos)

    UI.item_panel_top = make(160, 0, 112, 64, shift=start_pos)
    UI.item_panel_middle = make(160, 64, 112, 8, shift=start_pos)
    UI.item_panel_bottom_0 = make(160, 72, 112, 8, shift=start_pos)
    UI.item_panel_bottom_1 = make(160, 80, 112, 8, shift=start_pos)  # if no bonus attributes

    UI.inv_panel_top = make(0, 0, 160, 128, shift=start_pos)
    UI.inv_panel_mid = make(0, 128, 160, 16, shift=start_pos)
    UI.inv_panel_bot = make(0, 296, 160, 16, shift=start_pos)

    UI.world_cursors = [make(0 + i*16, 280, 16, 16, shift=start_pos) for i in range(0, 2)]

    UI.attack_action = make(0, 252, 28, 28, shift=start_pos)
    UI.potion_action = make(28, 252, 28, 28, shift=start_pos)
    UI.inspect_action = make(56, 252, 28, 28, shift=start_pos)
    UI.inventory_action = make(84, 252, 28, 28, shift=start_pos)

    UI.tooltip_bg = make(48, 232, 2, 2, shift=start_pos)

    """
    0 1 2
    3 4 5
    6 7 8
    """
    UI.text_panel_edges = [make(4 * (i % 3), 232 + 4 * (i // 3), 4, 4, shift=start_pos) for i in range(0, 9)]
    UI.hover_text_edges = [make(15 + 5 * (i % 3), 230 + 5 * (i // 3), 5, 5, shift=start_pos) for i in range(0, 9)]
    UI.hover_text_bottom_arrow = make(30, 240, 5, 5, shift=start_pos)

    UI.status_bar_base = make(0, 176, 400, 53, shift=start_pos)
    UI.health_bar_top = make(64, 160, 256, 16, shift=start_pos)
    UI.health_bar_full = make(64, 160, 256, 16, shift=start_pos)
    UI.health_bars_with_length = []

    for i in range(0, 256):
        UI.health_bars_with_length.append(make(64, 160, i, 16, shift=start_pos))
    UI.health_bars_with_length.append(UI.health_bar_full)

    UI.status_bar_action_border = make(0, 252, 28, 28, shift=start_pos)

    UI.locked_door_panel = make(272, 0, 96, 112, shift=start_pos)

    UI.Cursors.arrow_cursor_sprite = make(24, 312, 24, 24, shift=start_pos)
    UI.Cursors.hand_cursor_sprite = make(48, 336, 16, 16, shift=start_pos)

    UI.Cursors.init_cursors(sheet)


def build_boss_sheet(start_pos, raw_boss_img, sheet):
    sheet.blit(raw_boss_img, start_pos)
    Bosses.cave_horror_idle = [make(i * 240, 80, 240, 240, shift=start_pos) for i in range(0, 2)]

    Bosses.frog_idle_1 = [make(0 + 48*i, 0, 48, 48, shift=start_pos) for i in range(0, 2)]
    Bosses.frog_idle_2 = [make(96 + 48*i, 0, 48, 48, shift=start_pos) for i in range(0, 2)]
    Bosses.frog_idle_mouth = [make(192 + 48*i, 0, 48, 48, shift=start_pos) for i in range(0, 2)]
    Bosses.frog_idle_down = [make(288 + 48*i, 0, 48, 48, shift=start_pos) for i in range(0, 2)]
    Bosses.frog_airborn_rising = [make(384 + 32*i, 0, 32, 80, shift=start_pos) for i in range(0, 2)]
    Bosses.frog_airborn_falling = [make(448, 0, 48, 48, shift=start_pos)]


def build_font_sheet(start_pos, raw_font_img, sheet):
    print("font_sheet start_pos={}".format(start_pos))
    sheet.blit(raw_font_img, start_pos)
    # sheet needs to be a 32x8 grid of characters
    char_w = round(raw_font_img.get_width() / 32)
    char_h = round(raw_font_img.get_height() / 8)
    for y in range(0, 8):
        for x in range(0, 32):
            c = chr(y*32 + x)
            Font._alphabet[c] = make(x * char_w, y * char_h, char_w, char_h, shift=start_pos)

    print("Font._alphabet = {}".format(Font._alphabet))


def build_spritesheet(raw_image, raw_cine_img, raw_ui_img, raw_items_img, raw_boss_img, raw_font_img):
    """
        returns: Surface
        Here's how the final sheet is arranged:
        *-------------------------------*
        | image.png   | cinematics.png  |
        |             |-----------------*
        |-------------| ui.png          |
        | gen'd stuff |                 |
        |             *-----------------*
        |             | items.png       |
        |             *-----------------*
        |             | bosses.png      |
        |             *-----------------*
        |             | font.png        |
        *-------------*-----------------*

    """
    global walls
    right_imgs = [raw_cine_img, raw_ui_img, raw_items_img, raw_boss_img, raw_font_img]
    sheet_w = raw_image.get_width() + max([im.get_width() for im in right_imgs])
    sheet_h = max(raw_image.get_height() + 2000, sum([im.get_height() for im in right_imgs]))
    sheet_size = (sheet_w, sheet_h)
    left_size = (raw_image.get_width(), sheet_size[1])

    sheet = pygame.Surface(sheet_size, pygame.SRCALPHA, 32)
    sheet.fill((255, 255, 255, 0))
    sheet.blit(raw_image, (0, 0))

    _x = raw_image.get_width()
    _y = 0
    print("building cinematics sheet...")
    build_cine_sheet((_x, _y), raw_cine_img, sheet)
    _y += raw_cine_img.get_height()

    print("building ui sheet...")
    build_ui_sheet((_x, _y), raw_ui_img, sheet)
    _y += raw_ui_img.get_height()

    print("building items sheet...")
    build_items_sheet((_x, _y), raw_items_img, sheet)
    _y += raw_items_img.get_height()

    print("building boss sheet...")
    build_boss_sheet((_x, _y), raw_boss_img, sheet)
    _y += raw_boss_img.get_height()

    print("building font sheet...")
    build_font_sheet((_x, _y), raw_font_img, sheet)
    _y += raw_font_img.get_height()

    draw_y = raw_image.get_height()

    print("building approx {} wall sprites...".format(256 * len(_wall_types)))

    for wall_type in _wall_types:
        wall_array = wall_type[0]
        pieces_location = wall_type[1]
        dupe_preventer = {}

        draw_x = 0

        for i in range(0, 256):
            bools = [int(x) for x in reversed(list('{0:0b}'.format(i)))]
            bools = bools + [0]*(8 - len(bools))

            tl = _get_wall_corner_loc("TL", bools, pieces_location)
            tr = _get_wall_corner_loc("TR", bools, pieces_location)
            bl = _get_wall_corner_loc("BL", bools, pieces_location)
            br = _get_wall_corner_loc("BR", bools, pieces_location)
            key = (tl, tr, bl, br)
            if key in dupe_preventer:
                wall_array[i] = dupe_preventer[key]
            else:
                sheet.blit(raw_image, (draw_x, draw_y), tl)
                sheet.blit(raw_image, (draw_x + 8, draw_y), tr)
                sheet.blit(raw_image, (draw_x, draw_y + 8), bl)
                sheet.blit(raw_image, (draw_x + 8, draw_y + 8), br)
                model = make(draw_x, draw_y, 16, 16)
                wall_array[i] = model
                dupe_preventer[key] = model

                draw_x += 16
                if draw_x > left_size[0] - 16:
                    draw_x = 0
                    draw_y += 16

        draw_y += 16

    draw_x = 0
    draw_y += 16

    _char_w = Font.get_char("a").width()
    _char_h = Font.get_char("a").height()
    for text in _cached_text:
        width = len(text) * _char_w
        if draw_x + width >= left_size[0]:
            draw_y += _char_h
            draw_x = 0

        cached_text_imgs[text] = make(draw_x, draw_y, width, _char_h)

        for letter in text:
            if letter != " ":
                letter_img = Font.get_char(letter)
                sheet.blit(sheet, (draw_x, draw_y), letter_img.rect())
                draw_x += _char_w

    draw_y += _char_h

    all_cube_configs = CubeUtils.get_all_possible_cube_configs(n=(4, 5, 6, 7))
    print("building {} item sprites...".format(len(all_cube_configs)))

    draw_x = 0
    for item in all_cube_configs:
        w = 1
        h = 1

        for c in item:
            dest = (draw_x + c[0]*4, draw_y + c[1]*4)
            piece_rect = Items.piece_small.rect()
            sheet.blit(sheet, dest, piece_rect)

            w = max(c[0] + 1, w)
            h = max(c[1] + 1, h)

        Items.item_entities[item] = make(draw_x, draw_y, w * 4, h * 4)

        draw_x += 20
        if draw_x > left_size[0] - 20:
            draw_x = 0
            draw_y += 20

    draw_y += 20
    draw_x = 0

    step = 8
    circle_art_heights = [y for y in range(32, 32 * 3 + 1, step)]
    circle_art_widths = [int(1.5 * y) for y in circle_art_heights]
    num_frames = 8
    anim_frames = 4

    print("drawing {} attack circle sprites...".format(len(circle_art_widths) * num_frames))

    for i in range(0, len(circle_art_widths)):
        w = circle_art_widths[i]
        h = circle_art_heights[i]
        att_circles_real.append([])
        for frame in range(0, num_frames):
            if draw_x + w > left_size[0]:
                draw_x = 0
                draw_y += h
            rect = [draw_x, draw_y, w, h]
            att_circles_real[-1].append(make(rect[0], rect[1], rect[2], rect[3]))
            center = rect[0] + w // 2, rect[1] + h // 2
            opacity = 1 - frame / (num_frames - 1)
            _draw_ellipse(sheet, center, rect[2] // 2, rect[3] // 2, opacity)

            small_circle_size = (rect[2] // 2, rect[3] // 2)
            for j in range(0, 4):
                angle = (j + (frame % anim_frames) / anim_frames) * 3.1415 / 2
                cx = int(small_circle_size[0] // 2 * math.cos(angle))
                cy = int(small_circle_size[1] // 2 * math.sin(angle))
                _draw_ellipse(sheet, (rect[0] + rect[2] // 2 + cx, rect[1] + rect[3] // 2 + cy),
                              small_circle_size[0] // 2, small_circle_size[1] // 2, opacity)
            draw_x += w

    draw_y += circle_art_heights[-1]

    n_cooldowns = 20
    cd_size = 28
    cd_color = (255, 255, 255)  # (196, 196, 196)
    print("drawing {} cooldown overlays...".format(n_cooldowns))

    for i in range(0, n_cooldowns):
        if draw_x + cd_size > left_size[0]:
            draw_x = 0
            draw_y += cd_size
        rect = [draw_x, draw_y, cd_size, cd_size]
        _draw_cd_image(sheet, rect, i / n_cooldowns, cd_color)
        cooldown_overlays.append(make(*rect))
        draw_x += cd_size

    draw_y += cd_size
    draw_x = 0

    num_floor_types = len(_floor_types)
    print("drawing {} darkened floor tiles...".format(num_floor_types * floor_darkness_resolution))
    dest_r = [0, 0, 0, 0]

    for floor_id in range(0, num_floor_types):
        for encoding in range(0, 8):
            for darkness in range(1, floor_darkness_resolution):
                fully_bright = _floor_lookup[(floor_id, encoding, 0)]
                src_r = fully_bright.rect()
                dest_r = [draw_x, draw_y, src_r[2], src_r[3]]
                if dest_r[0] + dest_r[2] > raw_image.get_width():
                    draw_x = 0
                    draw_y += src_r[3]
                    dest_r = [draw_x, draw_y, src_r[2], src_r[3]]

                _draw_dark_floor(sheet, darkness / floor_darkness_resolution, src_r, dest_r)
                _floor_lookup[(floor_id, encoding, darkness)] = make(dest_r[0], dest_r[1], dest_r[2], dest_r[3])
                draw_x += dest_r[2]

    draw_y += dest_r[3]
    draw_x = 0

    for img in all_imgs:
        img.set_sheet_size(sheet_size)
    
    # pygame.image.save(sheet, "src/spritesheet.png")
    
    return sheet


if __name__ == "__main__":
    raw = pygame.image.load("assets/image.png")
    raw2 = pygame.image.load("assets/cinematics.png")
    raw3 = pygame.image.load("assets/ui.png")
    raw4 = pygame.image.load("assets/items.png")
    raw5 = pygame.image.load("assets/bosses.png")
    raw6 = pygame.image.load("assets/font.png")
    output = build_spritesheet(raw, raw2, raw3, raw4, raw5, raw6)
    print("created {} sprites".format(len(all_imgs)))
    pygame.image.save(output, "src/spritesheet.png")
    
