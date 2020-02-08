import math

from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.items.item as item_module
from src.utils.util import Utils
from src.game.stats import StatTypes
import src.game.globalstate as gs
import src.utils.colors as colors
from src.renderengine.engine import RenderEngine
from src.game.events import EventType
import src.game.debug as debug
import src.game.sound_effects as sound_effects
import src.game.soundref as soundref
import src.game.gameengine as gameengine
import src.game.constants as constants


BG_DEPTH = 10
FG_DEPTH = 5

BG_DEPTH_SUPER = 1
FG_DEPTH_SUPER = 0


class ItemGridImage:

    def __init__(self, x, y, grid, layer, scale, depth):
        self.x = x
        self.y = y
        self.grid = grid
        self.layer = layer
        self.scale = scale
        self.depth = depth
        
        self.item_images = []
        
        self._build_images()
        
    def _build_images(self):
        cellsize = spriteref.Items.piece_bigs[0].size()
        for item in self.grid.all_items():
            pos = self.grid.get_pos(item)
            x_pos = self.x + pos[0] * cellsize[0] * self.scale
            y_pos = self.y + pos[1] * cellsize[1] * self.scale
            self.item_images.append(ItemImage(x_pos, y_pos, item, self.layer, self.scale, self.depth))
        
    def all_bundles(self):
        for item_img in self.item_images:
            for bun in item_img.all_bundles():
                yield bun


class InteractableImage:
    """Piece of UI that can be 'interacted with' using the mouse."""

    def contains_point(self, x, y):
        return False

    def on_click(self, x, y, button=1):
        """returns: True if click was absorbed, False otherwise"""
        for c in self.all_child_imgs():
            if c.contains_point(x, y):
                if c.on_click(x, y):
                    return True
        return False

    def get_cursor_at(self, x, y):
        for c in self.all_child_imgs():
            if c.contains_point(x, y):
                return c.get_cursor_at(x, y)
        return spriteref.UI.Cursors.arrow_cursor

    def get_tooltip_target_at(self, x, y):
        for c in self.all_child_imgs():
            if c.contains_point(x, y):
                target = c.get_tooltip_target_at(x, y)
                if target is not None:
                    return target
        return None

    def is_dirty(self):
        return True

    def all_child_imgs(self):
        """yields all the sub-InteractableImages of this one"""
        return []

    def update_images(self):
        for c in self.all_child_imgs():
            if c.is_dirty():
                c.update_images()

    def all_bundles(self):
        for c in self.all_child_imgs():
            for bun in c.all_bundles():
                yield bun


class SidePanelTypes:
    INVENTORY = "INVENTORY"
    MAP = "MAP"
    # HELP = "HELP"


class SidePanel(InteractableImage):

    def __init__(self, panel_type):
        InteractableImage.__init__(self)
        self._panel_type = panel_type

        self.layer = spriteref.UI_0_LAYER

        self.sc = 1
        self.text_sc = 0.5

        self.title_color = colors.LIGHT_GRAY
        self.title_rect = [8 * self.sc, (0 + 2) * self.sc,
                           80 * self.sc, (16 - 2) * self.sc]

    def get_panel_type(self):
        return self._panel_type

    def get_rect(self):
        return [0, 0, 0, 0]

    def contains_point(self, x, y):
        r = self.get_rect()
        return r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]

    def update(self, world):
        pass

    def build_title_img(self, text, rect=None):
        if rect is None:
            rect = self.title_rect

        res = TextImage(rect[0], 0, text, self.layer, scale=self.text_sc, color=self.title_color)
        new_y = rect[1] + (rect[3] - res.line_height()) // 2

        return res.update(new_y=new_y)

    def needs_rebuild(self):
        return False


class MapPanel(SidePanel):

    def __init__(self):
        SidePanel.__init__(self, SidePanelTypes.MAP)

        self.top_img = None
        self.mid_img = None  # in this house we  s t r e t c h
        self.bot_img = None

        self.title_text_img = None

        border_thickness = 8

        # TODO - make this configurable
        map_w = (spriteref.UI.map_panel_top.width() - border_thickness * 2) * self.sc

        self.map_rect = [8 * self.sc, 16 * self.sc, map_w, 224 * self.sc]

        total_w = map_w + border_thickness * 2 * self.sc
        total_h = self.map_rect[1] + self.map_rect[3] + border_thickness * 2 * self.sc
        self.total_rect = [0, 0, total_w, total_h]

        self.map_center = None  # gets updated when player moves
        self.map_dims = constants.MAP_DIMS

        self.map_raw_text = None  # TextBuilder
        self.map_text_img = None

        self.build_images()

        self.map_dirty = False

    def get_rect(self):
        return self.total_rect

    def is_dirty(self):
        return self.map_dirty

    def needs_rebuild(self):
        return False

    def build_images(self):
        y = 0
        self.top_img = ImageBundle(spriteref.UI.map_panel_top, 0, y, layer=self.layer, scale=self.sc, depth=BG_DEPTH)
        y += self.top_img.height()

        self.mid_img = ImageBundle(spriteref.UI.map_panel_mid, 0, y, layer=self.layer, scale=self.sc, depth=BG_DEPTH)
        mid_img_h = spriteref.UI.map_panel_mid.height() * self.sc
        mid_img_ratio = (1, self.map_rect[3] / mid_img_h)
        self.mid_img = self.mid_img.update(new_ratio=mid_img_ratio)
        y += self.mid_img.height()

        self.bot_img = ImageBundle(spriteref.UI.map_panel_bot, 0, y, layer=self.layer, scale=self.sc, depth=BG_DEPTH)

        self.title_text_img = self.build_title_img("Map")

    def update(self, world):

        old_map_text = self.map_raw_text

        # assuming the map only needs updating after an action is completed~
        if gs.get_instance().event_queue().has_event(types=EventType.ACTION_FINISHED):
            self.map_raw_text = None

        player = world.get_player()
        if player is not None:
            self.map_center = world.to_grid_coords(*player.center())

        # keeps using an old cached center if player is missing
        if self.map_raw_text is None and self.map_center is not None:
            rect = [self.map_center[0] - self.map_dims[0] // 2,
                    self.map_center[1] - self.map_dims[1] // 2,
                    self.map_dims[0], self.map_dims[1]]
            self.map_raw_text = world.get_map_text_for_cells(rect, ignore_visiblity=debug.map_sees_all())

        if self.map_raw_text != old_map_text:
            self.map_dirty = True

    def update_images(self):
        render_eng = RenderEngine.get_instance()
        has_map_text = self.map_raw_text is not None and len(self.map_raw_text.text()) > 0
        if not has_map_text and self.map_text_img is not None:
            for bun in self.map_text_img.all_bundles():
                render_eng.remove(bun)
            self.map_text_img = None

        if has_map_text and self.map_dirty:
            if self.map_text_img is None:
                self.map_text_img = TextImage(0, 0, "~not built?~", spriteref.UI_0_LAYER, depth=FG_DEPTH,
                                              x_kerning=1, x_leading_kerning=0, y_kerning=0)

            self.map_text_img = self.map_text_img.update(new_text=self.map_raw_text.text(),
                                                         new_custom_colors=self.map_raw_text.custom_colors())
            size = self.map_text_img.size()
            x = self.map_rect[0] + self.map_rect[2] // 2 - size[0] // 2
            y = self.map_rect[1] + self.map_rect[3] // 2 - size[1] // 2

            self.map_text_img = self.map_text_img.update(new_x=x, new_y=y)

            for bun in self.map_text_img.all_bundles():
                render_eng.update(bun)

        self.map_dirty = False

    def all_bundles(self):
        if self.top_img is not None:
            yield self.top_img
        if self.mid_img is not None:
            yield self.mid_img
        if self.bot_img is not None:
            yield self.bot_img
        if self.title_text_img is not None:
            for bun in self.title_text_img.all_bundles():
                yield bun
        if self.map_text_img is not None:
            for bun in self.map_text_img.all_bundles():
                yield bun


class InventoryPanel(SidePanel):

    def __init__(self):
        SidePanel.__init__(self, SidePanelTypes.INVENTORY)

        self.player_state = gs.get_instance().player_state()
        self.state = self.player_state.inventory()
        self.layer = spriteref.UI_0_LAYER

        self.top_img = None
        self.mid_imgs = []
        self.bot_img = None

        self.eq_title_text_img = None
        self.inv_title_text_img = None

        self.sc = 1
        self.text_sc = 0.5

        total_w = spriteref.UI.inv_panel_top.width() * self.sc
        total_h = (128 + 16 * self.state.rows) * self.sc
        self.total_rect = [0, 0, total_w, total_h]

        self.equip_grid_rect = [8 * self.sc, 16 * self.sc, 80 * self.sc, 80 * self.sc]
        self.inv_grid_rect = [8 * self.sc, 112 * self.sc, 144 * self.sc, 16 * self.state.rows * self.sc]
        self.stats_rect = [96 * self.sc, 16 * self.sc, 56 * self.sc, 80 * self.sc]

        self.inv_title_rect = [8 * self.sc, (96 + 2) * self.sc, 80 * self.sc, (16 - 2) * self.sc]

        self.lvl_text = None
        self.att_text = None
        self.def_text = None
        self.vit_text = None
        self.hp_text = None
        self.spd_text = None
        
        self.equip_img = None
        self.inv_img = None
        
        self._build_images()
        self.state.set_clean()

    def get_rect(self):
        return self.total_rect

    def get_grid_and_cell_at_pos(self, x, y):
        pos_in_panel = (x - self.total_rect[0],
                        y - self.total_rect[1])

        eq_rect = self.equip_grid_rect
        if Utils.rect_contains(eq_rect, pos_in_panel):
            grid = self.state.equip_grid
            x = int((pos_in_panel[0] - eq_rect[0])/eq_rect[2]*grid.w())
            y = int((pos_in_panel[1] - eq_rect[1])/eq_rect[3]*grid.h())
            return (grid, (x, y))

        inv_rect = self.inv_grid_rect
        if Utils.rect_contains(inv_rect, pos_in_panel):
            grid = self.state.inv_grid
            x = int((pos_in_panel[0] - inv_rect[0])/inv_rect[2]*grid.w())
            y = int((pos_in_panel[1] - inv_rect[1])/inv_rect[3]*grid.h())
            return (grid, (x, y))

        return (None, None)

    def get_item_at_pos(self, x, y):
        grid, cell = self.get_grid_and_cell_at_pos(x, y)
        if grid is None or cell is None:
            return None
        else:
            return grid.item_at_position(cell)
        
    def _build_images(self):
        self.top_img = ImageBundle(spriteref.UI.inv_panel_top, 0, 0, layer=self.layer, scale=self.sc, depth=BG_DEPTH)
        for i in range(0, self.state.rows - 1):
            y = (128 + i * 16) * self.sc
            self.mid_imgs.append(ImageBundle(spriteref.UI.inv_panel_mid, 0, y, layer=self.layer, scale=self.sc, depth=BG_DEPTH))
        y = (128 + self.state.rows * 16 - 16) * self.sc
        self.bot_img = ImageBundle(spriteref.UI.inv_panel_bot, 0, y, layer=self.layer, scale=self.sc, depth=BG_DEPTH)

        # despite being called the inventory panel, the title of the panel is actually "Equipment".
        # (because the equipment grid is above the inventory grid.)
        self.eq_title_text_img = self.build_title_img("Equipment")
        self.inv_title_text_img = self.build_title_img("Inventory", rect=self.inv_title_rect)

        self.lvl_text = TextImage(0, 0, "lvl", self.layer, scale=self.text_sc, depth=FG_DEPTH, x_leading_kerning=2)
        self.att_text = TextImage(0, 0, "att", self.layer, scale=self.text_sc, color=StatTypes.ATT.get_color(), depth=FG_DEPTH, x_leading_kerning=2)
        self.def_text = TextImage(0, 0, "def", self.layer, scale=self.text_sc, color=StatTypes.DEF.get_color(), depth=FG_DEPTH, x_leading_kerning=2)
        self.vit_text = TextImage(0, 0, "vit", self.layer, scale=self.text_sc, color=StatTypes.VIT.get_color(), depth=FG_DEPTH, x_leading_kerning=2)
        self.spd_text = TextImage(0, 0, "spd", self.layer, scale=self.text_sc, color=StatTypes.SPEED.get_color(), depth=FG_DEPTH, x_leading_kerning=2)
        self.hp_text = TextImage(0, 0, "hp", self.layer, scale=self.text_sc, color=colors.LIGHT_GRAY, depth=FG_DEPTH, x_leading_kerning=2)

        self.update_stats_imgs()
        self.update_item_grid_imgs()

    def update_item_grid_imgs(self):
        if self.state.is_dirty():
            if self.equip_img is not None:
                for bun in self.equip_img.all_bundles():
                    RenderEngine.get_instance().remove(bun)
                self.equip_img = None
            if self.inv_img is not None:
                for bun in self.inv_img.all_bundles():
                    RenderEngine.get_instance().remove(bun)
                self.inv_img = None

        if self.equip_img is None:
            e_xy = (self.equip_grid_rect[0], self.equip_grid_rect[1])
            self.equip_img = ItemGridImage(*e_xy, self.state.equip_grid, self.layer, self.sc, FG_DEPTH)

        if self.inv_img is None:
            inv_xy = (self.inv_grid_rect[0], self.inv_grid_rect[1])
            self.inv_img = ItemGridImage(*inv_xy, self.state.inv_grid, self.layer, self.sc, FG_DEPTH)

        self.state.set_clean()

    def update_stats_imgs(self):
        s_xy = [self.stats_rect[0], self.stats_rect[1]]

        render_eng = RenderEngine.get_instance()

        lvl_txt = "Depth:{}".format(gs.get_instance().get_zone_level() + 1)
        if lvl_txt != self.lvl_text.get_text():
            self.lvl_text = self.lvl_text.update(new_text=lvl_txt, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.lvl_text)
        s_xy[1] += self.lvl_text.line_height()

        att_value = self.player_state.stat_value(StatTypes.ATT)
        att_str = "ATT:{}".format(att_value if att_value < 100 else "99+")
        if att_str != self.att_text.get_text():
            self.att_text = self.att_text.update(new_text=att_str, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.att_text)
        s_xy[1] += self.att_text.line_height()

        def_str = "DEF:{}".format(self.player_state.stat_value(StatTypes.DEF))
        if def_str != self.def_text.get_text():
            self.def_text = self.def_text.update(new_text=def_str, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.def_text)
        s_xy[1] += self.def_text.line_height()

        vit_str = "VIT:{}".format(self.player_state.stat_value(StatTypes.VIT))
        if vit_str != self.vit_text.get_text():
            self.vit_text = self.vit_text.update(new_text=vit_str, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.vit_text)
        s_xy[1] += self.vit_text.line_height()

        spd_str = "SPD:{}".format(self.player_state.speed())
        if spd_str != self.spd_text.get_text():
            self.spd_text = self.spd_text.update(new_text=spd_str, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.spd_text)
        s_xy[1] += self.spd_text.line_height()

        hp_str = "HP: {}/{}".format(self.player_state.hp(), self.player_state.max_hp())
        if hp_str != self.hp_text.get_text():
            self.hp_text = self.hp_text.update(new_text=hp_str, new_x=s_xy[0], new_y=s_xy[1])
            render_eng.update(self.hp_text)
        s_xy[1] += self.hp_text.line_height()

    def all_stat_text_bundles(self):
        for bun in self.lvl_text.all_bundles():
            yield bun
        for bun in self.att_text.all_bundles():
            yield bun
        for bun in self.def_text.all_bundles():
            yield bun
        for bun in self.vit_text.all_bundles():
            yield bun
        for bun in self.spd_text.all_bundles():
            yield bun
        for bun in self.hp_text.all_bundles():
            yield bun

    def on_click(self, x, y, button=1):
        """returns: True if click was absorbed, False otherwise"""
        if super().on_click(x, y, button=button):
            return True

        w, player = gs.get_instance().get_world_and_player()
        if player is None:
            return

        pc = player.get_controller()
        screen_pos = (x, y)

        if button == 1:
            held_item = gs.get_instance().held_item()

            if held_item is not None:
                # when holding an item, gotta offset the click to the top left corner
                item_size = ItemImage.calc_size(held_item, 1)
                grid_click_pos = Utils.add(screen_pos, (-item_size[0] // 2, -item_size[1] // 2))
                grid_click_pos = Utils.add(grid_click_pos, (8, 8))  # plus some fudge XXX
            else:
                grid_click_pos = screen_pos

            grid, cell = self.get_grid_and_cell_at_pos(*grid_click_pos)

            if grid is not None and cell is not None:
                if held_item is not None:
                    put_item_action = gameengine.AddItemToGridAction(player, held_item, grid, grid_position=cell)

                    if put_item_action.is_possible(w):
                        pc.add_requests(put_item_action, priority=pc.HIGHEST_PRIORITY)
                    else:
                        sound_effects.play_sound(soundref.item_cant_place)

                else:
                    clicked_item = grid.item_at_position(cell)
                    if clicked_item is not None:
                        take_item_action = gameengine.RemoveItemFromGridAction(player, clicked_item, grid)
                        pc.add_requests(take_item_action, priority=pc.HIGHEST_PRIORITY)

        elif button == 3:
            item_to_apply = gs.get_instance().held_item()

            if item_to_apply is None:
                item_to_apply = self.get_item_at_pos(x, y)

            if item_to_apply is not None:
                action = gameengine.get_right_click_action_for_item(item_to_apply)
                if action is not None and action.is_possible(w):
                    pc.add_requests(action, pc.HIGHEST_PRIORITY)
                else:
                    sound_effects.play_sound(soundref.item_cant_place)

        return True  # need to prevent clicks from falling through to world

    def get_cursor_at(self, x, y):
        if self.get_item_at_pos(x, y) is not None:
            return spriteref.UI.Cursors.hand_cursor
        else:
            return super().get_cursor_at(x, y)

    def get_tooltip_target_at(self, x, y):
        if self.get_item_at_pos(x, y) is not None:
            return self.get_item_at_pos(x, y)
        else:
            return super().get_cursor_at(x, y)

    def is_dirty(self):
        return True

    def needs_rebuild(self):
        return self.state.is_dirty()

    def all_child_imgs(self):
        """yields all the sub-InteractableImages of this one"""
        return []

    def update_images(self):
        super().update_images()
        self.update_stats_imgs()

    def all_bundles(self):
        yield self.top_img
        for img in self.mid_imgs:
            yield img
        yield self.bot_img
        for bun in self.inv_title_text_img.all_bundles():
            yield bun
        for bun in self.eq_title_text_img.all_bundles():
            yield bun
        for bun in self.all_stat_text_bundles():
            yield bun
        for bun in self.equip_img.all_bundles():
            yield bun 
        for bun in self.inv_img.all_bundles():
            yield bun
        for bun in super().all_bundles():
            yield bun


class DialogPanel(InteractableImage):

    BORDER_SIZE = 4, 4
    SIZE = (248, 40)

    def __init__(self, dialog):
        self._dialog = dialog

        self._rect = [0, 0, 0, 0]

        self._speaker_img = None
        self._text_img = None
        self._border_imgs = []
        self._bg_img = None

        self._text_displaying = ""
        self._cur_sprite = None
        self._sprite_on_left_side = True

        self.sc = 1
        self.text_sc = 0.5

        self._dirty = True

    def get_dialog(self):
        return self._dialog

    def _calc_rect(self):
        # TODO this assumes that Healthbar's scale is the same as the dialog's scale
        return [
            RenderEngine.get_instance().get_game_size()[0] // 2 - self.sc * DialogPanel.SIZE[0] // 2,
            RenderEngine.get_instance().get_game_size()[1] - self.sc * (HealthBarPanel.SIZE[1] + DialogPanel.SIZE[1]),
            DialogPanel.SIZE[0] * self.sc,
            DialogPanel.SIZE[1] * self.sc
        ]

    def update_images(self):
        text = self._text_displaying if len(self._text_displaying) > 0 else " "
        sprite = self._cur_sprite
        left_side = self._sprite_on_left_side

        x = self._rect[0]
        y = self._rect[1]
        w = self._rect[2]
        h = self._rect[3]

        lay = spriteref.UI_0_LAYER

        while len(self._border_imgs) < 5:
            # scale intentionally set to 1 and not self.sc because ratio is used to size these
            self._border_imgs.append(ImageBundle.new_bundle(lay, depth=BG_DEPTH_SUPER, scale=1))

        border_sprites = spriteref.UI.text_panel_edges

        # top border
        top_border_sprite = border_sprites[1]
        top_border_ratio = (w // top_border_sprite.width(), self.sc)
        self._border_imgs[0] = self._border_imgs[0].update(new_model=top_border_sprite, new_x=x,
                                                           new_y=y - top_border_sprite.height() * top_border_ratio[1],
                                                           new_ratio=top_border_ratio)
        # left border
        left_border_sprite = border_sprites[3]
        left_border_ratio = (self.sc, h // left_border_sprite.height())
        self._border_imgs[1] = self._border_imgs[1].update(new_model=left_border_sprite,
                                                           new_x=x - left_border_sprite.width() * left_border_ratio[0],
                                                           new_y=y, new_ratio=left_border_ratio)
        # right border
        right_border_sprite = border_sprites[5]
        right_border_ratio = (self.sc, h // right_border_sprite.height())
        self._border_imgs[2] = self._border_imgs[2].update(new_model=right_border_sprite,
                                                           new_x=x + w, new_y=y, new_ratio=right_border_ratio)

        # top-left corner border
        tl_border_sprite = border_sprites[0]
        tl_border_ratio = (self.sc, self.sc)
        self._border_imgs[3] = self._border_imgs[3].update(new_model=tl_border_sprite,
                                                           new_x=x - tl_border_sprite.width() * tl_border_ratio[0],
                                                           new_y=y - tl_border_sprite.height() * tl_border_ratio[1],
                                                           new_ratio=tl_border_ratio)
        # top-right corner border
        tr_border_sprite = border_sprites[2]
        tr_border_ratio = (self.sc, self.sc)
        self._border_imgs[4] = self._border_imgs[4].update(new_model=tr_border_sprite,
                                                           new_x=x + w,
                                                           new_y=y - tr_border_sprite.height() * tr_border_ratio[1],
                                                           new_ratio=tr_border_ratio)

        if self._bg_img is None:
            self._bg_img = ImageBundle.new_bundle(lay, scale=1, depth=BG_DEPTH_SUPER)

        # black background rectangle
        bg_sprite = spriteref.UI.text_panel_edges[4]
        bg_ratio = (w // bg_sprite.width(), h // bg_sprite.height())
        self._bg_img = self._bg_img.update(new_model=bg_sprite, new_x=x, new_y=y, new_ratio=bg_ratio)

        text_buffer = 3, 2
        text_area = [x + self.sc * text_buffer[0],
                     y + self.sc * text_buffer[1],
                     w - self.sc * text_buffer[0] * 2,
                     h - self.sc * text_buffer[1] * 2]

        # speaker sprite
        if sprite is not None:
            sprite_x_buffer = 3

            if self._speaker_img is None:
                self._speaker_img = ImageBundle.new_bundle(lay, scale=self.sc, depth=FG_DEPTH_SUPER)

            sprite_y_pos = y + h // 2 - self.sc * sprite.height() // 2

            text_x1 = text_area[0]
            text_x2 = text_area[0] + text_area[2]

            if left_side:
                sprite_x_pos = x + self.sc * sprite_x_buffer
                text_x1 = sprite_x_pos + self.sc * sprite.width() + self.sc * sprite_x_buffer
            else:
                sprite_x_pos = x + w - self.sc * (sprite.width() + sprite_x_buffer)
                text_x2 = sprite_x_pos - self.sc * sprite_x_buffer

            text_area[0] = text_x1
            text_area[2] = text_x2 - text_x1

            self._speaker_img = self._speaker_img.update(new_model=sprite, new_x=sprite_x_pos, new_y=sprite_y_pos)

        elif self._speaker_img is not None:
            render_eng = RenderEngine.get_instance()
            render_eng.remove(self._speaker_img)
            self._speaker_img = None

        # the text
        if len(text) > 0:
            if self._text_img is None:
                self._text_img = TextImage(0, 0, " ", lay, scale=self.text_sc, y_kerning=2, depth=FG_DEPTH_SUPER)

            wrapped_text = TextImage.wrap_words_to_fit(text, self.text_sc, text_area[2], self._text_img.x_kerning)
            self._text_img = self._text_img.update(new_text=wrapped_text, new_x=text_area[0], new_y=text_area[1])

        elif self._text_img is not None:
            render_eng = RenderEngine.get_instance()
            for bun in self._text_img.all_bundles():
                render_eng.remove(bun)
            self._text_img = None

    def update(self):
        self._rect = self._calc_rect()
        self._text_displaying = self._dialog.get_visible_text(invisible_sub=TextImage.INVISIBLE_CHAR)
        self._cur_sprite = self._dialog.get_visible_sprite()
        self._sprite_on_left_side = self._dialog.get_sprite_side()

        self.update_images()

        render_eng = RenderEngine.get_instance()
        for bun in self.all_bundles():
            render_eng.update(bun)

    def contains_point(self, x, y):
        return True  # when it's open, we block ALL clicks

    def on_click(self, x, y, button=1):
        gs.get_instance().dialog_manager().interact()
        return True

    def get_tooltip_target_at(self, x, y):
        # we gotta block things underneath the panel from making their own tooltips on top
        return TextBuilder()

    def is_dirty(self):
        return True

    def all_bundles(self):
        if self._bg_img is not None:
            yield self._bg_img
        for bord in self._border_imgs:
            yield bord
        if self._speaker_img is not None:
            yield self._speaker_img
        if self._text_img is not None:
            for bun in self._text_img.all_bundles():
                yield bun
        for bun in super().all_bundles():
            yield bun


class MappedActionImage(InteractableImage):

    def __init__(self, action_prov, rect):
        self.action_prov = action_prov
        self.rect = rect

        self._border_img = None
        self._icon_img = None

        # the text that appears at the bottom right of the action icon
        self._info_text_img = None

        self.sc = rect[2] // 28

    def contains_point(self, x, y):
        if self.action_prov is None:
            return False
        else:
            return (self.rect[0] <= x < self.rect[0] + self.rect[2] and
                    self.rect[1] <= y < self.rect[1] + self.rect[3])

    def on_click(self, x, y, button=1):
        """returns: True if click was absorbed, False otherwise"""
        if self.action_prov is not None:
            targeting_action = gs.get_instance().get_targeting_action_provider()
            if self.action_prov == targeting_action:
                gs.get_instance().set_targeting_action_provider(None)
                sound_effects.play_sound(soundref.action_deactivate)
            else:
                gs.get_instance().set_targeting_action_provider(self.action_prov)
                sound_effects.play_sound(soundref.action_activate)
            return True
        return False

    def get_cursor_at(self, x, y):
        return super().get_cursor_at(x, y)

    def get_tooltip_target_at(self, x, y):
        return self.action_prov

    def is_dirty(self):
        return True

    def get_hotbar_idx(self):
        if self.action_prov is None:
            return None
        else:
            for i in range(0, 6):
                if gs.get_instance().get_mapped_action(i) == self.action_prov:
                    return i
            return None

    def get_info_text_and_color(self):
        if self.action_prov is None:
            return (None, None)

        ps = gs.get_instance().player_state()
        if self.action_prov.get_type() == gameengine.ActionType.ATTACK:
            action_item = ps.get_item_in_possession_with_uid(self.action_prov.get_item_uid())

            att_value = ps.stat_value_with_item(StatTypes.ATT, action_item)
            if att_value < 0:
                text = "0"
            elif att_value > 99:
                text = "99+"
            else:
                text = str(att_value)

            color = colors.RED
            if action_item is not None:
                for item_stat in action_item.all_applied_stats():
                    if not item_stat.is_hidden() and item_stat.is_local():
                        color = item_stat.color()  # hope it's a good one~
                        break

            return (text, color)

        return (None, None)

    def update_images(self):
        if self.action_prov is None:
            if self._border_img is not None:
                RenderEngine.get_instance().remove(self._border_img)
                self._border_img = None
            if self._icon_img is not None:
                RenderEngine.get_instance().remove(self._icon_img)
                self._icon_img = None
        else:
            targeting_action = gs.get_instance().get_targeting_action_provider()
            if self.action_prov == targeting_action:
                color = self.action_prov.get_hotbar_color()
            else:
                color = colors.WHITE

            if self._icon_img is None:
                self._icon_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2 * self.sc, depth=FG_DEPTH)
            self._icon_img = self._icon_img.update(new_model=self.action_prov.get_icon(), new_color=color,
                                                   new_x=self.rect[0] + 4 * self.sc, new_y=self.rect[1] + 4 * self.sc)
            if self._border_img is None:
                self._border_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=self.sc, depth=FG_DEPTH)
            self._border_img = self._border_img.update(new_model=spriteref.UI.status_bar_action_border, new_color=color,
                                                       new_x=self.rect[0], new_y=self.rect[1])

        info_text, info_color = self.get_info_text_and_color()
        if info_text is None or len(info_text) == 0 or self.action_prov is None:
            if self._info_text_img is not None:
                for bun in self._info_text_img.all_bundles():
                    RenderEngine.get_instance().remove(bun)
                self._info_text_img = None
        else:
            text_sc = self.sc
            if self._info_text_img is None:
                self._info_text_img = OutlinedTextImage(0, 0, info_text, spriteref.UI_0_LAYER,
                                                        font_lookup=spriteref.tiny_font_lookup,
                                                        outline_diagonals=True,
                                                        x_kerning=1)

            char_size = (TextImage.calc_width("a", text_sc, font_lookup=spriteref.tiny_font_lookup),
                         TextImage.calc_line_height(text_sc, font_lookup=spriteref.tiny_font_lookup))

            inset = 2 * self.sc + text_sc

            x_pos = self.rect[0] + inset
            y_pos = self.rect[1] + self.rect[3] - char_size[1] - inset

            self._info_text_img = self._info_text_img.update(new_text=info_text, new_scale=text_sc,
                                                             new_color=info_color,
                                                             new_x=x_pos,
                                                             new_y=y_pos,
                                                             new_depth=FG_DEPTH - 2,
                                                             new_outline_thickness=text_sc,
                                                             new_outline_depth=FG_DEPTH - 1.25)

    def all_bundles(self):
        if self._border_img is not None:
            yield self._border_img
        if self._icon_img is not None:
            yield self._icon_img
        if self._info_text_img is not None:
            for bun in self._info_text_img.all_bundles():
                yield bun


class StatusEffectImage(InteractableImage):

    def __init__(self, status_effect, rect):
        self.effect = status_effect
        self.rect = rect

        self._icon_img = None

        self.sc = rect[2] // 16

    def contains_point(self, x, y):
        return (self.rect[0] <= x < self.rect[0] + self.rect[2] and
                self.rect[1] <= y < self.rect[1] + self.rect[3])

    def on_click(self, x, y, button=1):
        """returns: True if click was absorbed, False otherwise"""
        return False

    def get_tooltip_target_at(self, x, y):
        return self.effect

    def is_dirty(self):
        return True

    def update_images(self):
        color = self.effect.get_color()
        color = gs.get_instance().get_pulsing_color(color)

        if self._icon_img is None:
            self._icon_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=self.sc, depth=FG_DEPTH)
        self._icon_img = self._icon_img.update(new_model=self.effect.get_icon(), new_color=color,
                                               new_x=self.rect[0], new_y=self.rect[1])

    def all_bundles(self):
        if self._icon_img is not None:
            yield self._icon_img


class HotbarSidePanelButton(InteractableImage):

    def __init__(self, rect):
        self.rect = rect
        self._icon_img = None

        self.active_color = colors.DARK_GRAY
        self.inactive_color = colors.LIGHT_GRAY

    def contains_point(self, x, y):
        if self.rect is None:
            return False
        else:
            return (self.rect[0] <= x < self.rect[0] + self.rect[2] and
                    self.rect[1] <= y < self.rect[1] + self.rect[3])

    def get_preferred_size(self):
        return (15, 15)

    def get_icon_sprite(self):
        return None

    def get_color(self):
        return self.inactive_color

    def update_images(self):
        if self.rect is None:
            return

        if self._icon_img is None:
            self._icon_img = ImageBundle.new_bundle(layer_id=spriteref.UI_0_LAYER)

        sc = self.rect[2] // self.get_preferred_size()[0]

        self._icon_img = self._icon_img.update(new_model=self.get_icon_sprite(),
                                               new_depth=FG_DEPTH,
                                               new_x=self.rect[0],
                                               new_y=self.rect[1],
                                               new_color=self.get_color(),
                                               new_scale=sc)

    def all_bundles(self):
        if self._icon_img is not None:
            yield self._icon_img


class HotbarInventoryButton(HotbarSidePanelButton):

    def get_icon_sprite(self):
        return spriteref.UI.inventory_button

    def get_color(self):
        if gs.get_instance().get_active_sidepanel() == SidePanelTypes.INVENTORY:
            return self.active_color
        else:
            return self.inactive_color

    def on_click(self, x, y, button=1):
        if button == 1:
            gs.get_instance().toggle_sidepanel(SidePanelTypes.INVENTORY)
        return True

    def get_tooltip_target_at(self, x, y):
        inv_keys = gs.get_instance().settings().inventory_key()
        if len(inv_keys) == 0:
            text = "Equipment"
        else:
            text = "Equipment [{}]".format(Utils.stringify_key(inv_keys[0]))

        res = TextBuilder()
        res.add(text)
        return res


class HotbarMapButton(HotbarSidePanelButton):

    def get_icon_sprite(self):
        return spriteref.UI.map_button

    def get_color(self):
        if gs.get_instance().get_active_sidepanel() == SidePanelTypes.MAP:
            return self.active_color
        else:
            return self.inactive_color

    def on_click(self, x, y, button=1):
        if button == 1:
            gs.get_instance().toggle_sidepanel(SidePanelTypes.MAP)
        return True

    def get_tooltip_target_at(self, x, y):
        map_keys = gs.get_instance().settings().map_key()
        if len(map_keys) == 0:
            text = "Map"
        else:
            text = "Map [{}]".format(Utils.stringify_key(map_keys[0]))

        res = TextBuilder()
        res.add(text)
        return res


class HotbarHelpButton(HotbarSidePanelButton):

    def get_icon_sprite(self):
        return spriteref.UI.help_button

    def on_click(self, x, y, button=1):
        return True

    def get_tooltip_target_at(self, x, y):
        text = "Help [h]"

        res = TextBuilder()
        res.add_line(text)
        res.add("(coming soon!)", color=colors.LIGHT_GRAY)
        return res


class HotbarMoveButton(InteractableImage):

    def __init__(self, rect):
        self.rect = rect

        self.disabled_color = colors.DARK_GRAY
        self.ready_color = colors.LIGHT_GRAY

        self._icon_img = None

        self.last_clicked_at = -500
        self.render_pushed_time = 15

    def contains_point(self, x, y):
        if self.rect is not None:
            return (self.rect[0] <= x < self.rect[0] + self.rect[2] and
                    self.rect[1] <= y < self.rect[1] + self.rect[3])
        else:
            return False

    def get_preferred_size(self):
        return (15, 15)

    def is_dirty(self):
        return True

    def get_color(self):
        clicked_recently = self.last_clicked_at >= gs.get_instance().tick_counter - self.render_pushed_time
        if self.is_active() and not clicked_recently:
            return self.ready_color
        else:
            return self.disabled_color

    def update_images(self):
        icon_sprite = self.get_icon_sprite()
        if self.rect is not None and icon_sprite is not None:
            if self._icon_img is None:
                self._icon_img = ImageBundle.new_bundle(layer_id=spriteref.UI_0_LAYER)

            color = self.get_color()

            sc = self.rect[2] // self.get_preferred_size()[0]

            self._icon_img = self._icon_img.update(new_model=icon_sprite,
                                                   new_depth=FG_DEPTH,
                                                   new_x=self.rect[0],
                                                   new_y=self.rect[1],
                                                   new_color=color,
                                                   new_scale=sc)
        elif self._icon_img is not None:
                RenderEngine.get_instance().remove(self._icon_img)
                self._icon_img = None

    def get_icon_sprite(self):
        return None

    def get_tooltip_text(self):
        return ""

    def on_click(self, x, y, button=1):
        if button == 1 and self.is_active():
            self.last_clicked_at = gs.get_instance().tick_counter

            sound = self.get_click_sound_effect()
            if sound is not None:
                sound_effects.play_sound(sound)

        return True

    def get_click_sound_effect(self):
        return soundref.action_activate

    def is_active(self):
        if gs.get_instance().world_updates_paused():
            return False

        ps = gs.get_instance().player_state()
        if ps is not None:
            if ps.is_flinched() or ps.is_grasped():
                return False

        return True

    def get_tooltip_target_at(self, x, y):
        tt_text = self.get_tooltip_text()
        if tt_text is not None and len(tt_text) > 0:
            res = TextBuilder()
            res.add(tt_text)
            return res
        return None

    def all_bundles(self):
        if self._icon_img is not None:
            yield self._icon_img

    def send_move_action(self, direction):
        w = gs.get_instance().get_world()
        if w is None:
            return

        player = w.get_player()
        if player is None:
            return

        pc = gs.get_instance().player_controller()
        if pc is None:
            return  # shouldn't be possible but ehjlkhl

        pos = w.to_grid_coords(*player.center())
        new_pos = Utils.add(pos, direction)

        acts = gameengine.get_keyboard_action_requests(w, player, new_pos)
        pc.add_requests(acts)


class HotbarMoveLeftButton(HotbarMoveButton):

    def __init__(self):
        HotbarMoveButton.__init__(self, None)

    def get_icon_sprite(self):
        return spriteref.UI.left_button

    def on_click(self, x, y, button=1):
        super().on_click(x, y, button=1)
        if button == 1:
            super().send_move_action((-1, 0))
        return True


class HotbarMoveRightButton(HotbarMoveButton):

    def __init__(self):
        HotbarMoveButton.__init__(self, None)

    def get_icon_sprite(self):
        return spriteref.UI.right_button

    def on_click(self, x, y, button=1):
        super().on_click(x, y, button=1)
        if button == 1:
            super().send_move_action((1, 0))
        return True


class HotbarMoveUpButton(HotbarMoveButton):

    def __init__(self):
        HotbarMoveButton.__init__(self, None)

    def get_icon_sprite(self):
        return spriteref.UI.up_button

    def on_click(self, x, y, button=1):
        super().on_click(x, y, button=1)
        if button == 1:
            super().send_move_action((0, -1))
        return True


class HotbarMoveDownButton(HotbarMoveButton):

    def __init__(self):
        HotbarMoveButton.__init__(self, None)

    def get_icon_sprite(self):
        return spriteref.UI.down_button

    def on_click(self, x, y, button=1):
        super().on_click(x, y, button=1)
        if button == 1:
            super().send_move_action((0, 1))
        return True


class HotbarSkipTurnButton(HotbarMoveButton):

    def __init__(self):
        HotbarMoveButton.__init__(self, None)

    def get_icon_sprite(self):
        return spriteref.UI.skip_button

    def get_click_sound_effect(self):
        return None  # skipping has its own sound

    def on_click(self, x, y, button=1):
        super().on_click(x, y, button=1)
        if button == 1:
            w, p = gs.get_instance().get_world_and_player()
            if w is None or p is None:
                return True

            pc = gs.get_instance().player_controller()
            if pc is None:
                return True  # shouldn't be possible but ehjlkhl

            pos = w.to_grid_coords(*p.center())

            pc.add_requests([gameengine.SkipTurnAction(p, pos)])
            return True

    def get_preferred_size(self):
        return (30, 15)

    def is_active(self):
        return not gs.get_instance().world_updates_paused()

    def get_tooltip_text(self):
        skip_keys = gs.get_instance().settings().skip_turn_key()
        if len(skip_keys) > 0:
            return "Skip Turn [{}]".format(Utils.stringify_key(skip_keys[0]))
        else:
            return "Skip Turn"


class HealthBarPanel(InteractableImage):

    SIZE = (400, 53)

    def __init__(self, scale):
        self._top_img = None
        self._bar_img = None
        self._floating_bars = []  # list of [img, duration]

        self.sc = scale

        self._rect = [0, 0, 0, 0]
        self._bar_rect = [0, 0, 0, 0]

        self._float_dur = 30
        self._float_height = 15 * scale

        self._action_imgs = [None] * 6  # list of MappedActionImages

        self._status_imgs = []  # list of StatusEffectImages

        self._sidepanel_buttons = [None] * 8
        self._sidepanel_buttons[0] = HotbarInventoryButton(None)
        self._sidepanel_buttons[1] = HotbarMapButton(None)
        # self._sidepanel_buttons[2] = HotbarHelpButton(None)  # not ready, need to cut

        self._move_buttons = [None] * 8
        self._move_buttons[0] = HotbarSkipTurnButton()
        self._move_buttons[2] = HotbarMoveUpButton()
        self._move_buttons[4] = HotbarMoveLeftButton()
        self._move_buttons[5] = HotbarMoveRightButton()
        self._move_buttons[6] = HotbarMoveDownButton()

    def contains_point(self, x, y):
        if super().contains_point(x, y):
            return True
        else:
            if Utils.rect_contains(self._rect, (x, y)) or Utils.rect_contains(self._bar_rect, (x, y)):
                return True

            for status_img in self._status_imgs:
                if status_img.contains_point(x, y):
                    return True

            return False

    def get_tooltip_target_at(self, x, y):
        if Utils.rect_contains(self._bar_rect, (x, y)):
            ps = gs.get_instance().player_state()
            target = TextBuilder()
            target.add_line("HP: {}/{}".format(ps.hp(), ps.max_hp()), color=colors.WHITE)
            return target
        else:
            return super().get_tooltip_target_at(x, y)

    def _update_sidepanel_buttons(self):
        x_start = self._rect[0] + 7 * self.sc
        y_start = self._rect[1] + 16 * self.sc

        for i in range(0, len(self._sidepanel_buttons)):
            if self._sidepanel_buttons[i] is not None:
                self._sidepanel_buttons[i].rect = [x_start + 15 * self.sc * (i % 4),
                                                   y_start + 15 * self.sc * (i // 4),
                                                   15 * self.sc, 15 * self.sc]

                if self._sidepanel_buttons[i].is_dirty():
                    self._sidepanel_buttons[i].update_images()

    def _update_move_buttons(self):
        x_start = self._rect[0] + self._rect[2] - 67 * self.sc
        y_start = self._rect[1] + 16 * self.sc

        for i in range(0, len(self._move_buttons)):
            if self._move_buttons[i] is not None:
                w, h = self._move_buttons[i].get_preferred_size()
                self._move_buttons[i].rect = [x_start + 15 * self.sc * (i % 4),
                                              y_start + 15 * self.sc * (i // 4),
                                              w * self.sc, h * self.sc]

                if self._move_buttons[i].is_dirty():
                    self._move_buttons[i].update_images()

    def _update_action_icons(self):
        x_starts = [self._rect[0] + 87 * self.sc + i * 40 * self.sc for i in range(0, 3)] + \
                   [self._rect[0] + 205 * self.sc + i * 40 * self.sc for i in range(0, 3)]
        y_start = self._rect[1] + 19 * self.sc
        for i in range(0, 6):
            action_prov = gs.get_instance().get_mapped_action(i)
            rect = [x_starts[i], y_start, 28 * self.sc, 28 * self.sc]

            if self._action_imgs[i] is None:
                self._action_imgs[i] = MappedActionImage(action_prov, rect)
            else:
                self._action_imgs[i].action_prov = action_prov
                self._action_imgs[i].rect = rect

            if self._action_imgs[i].is_dirty():
                self._action_imgs[i].update_images()

    def _update_status_effect_icons(self):
        x_start = self._rect[0] + self._rect[2] - 71 * self.sc
        x_starts = [x_start + i * 18 * self.sc for i in range(0, 4)]
        y_start = self._rect[1] + self._rect[3] - 61 * self.sc

        effects = gs.get_instance().player_state().all_status_effects()

        while len(effects) < len(self._status_imgs):
            to_del = self._status_imgs.pop()
            for bun in to_del.all_bundles():
                RenderEngine.get_instance().remove(bun)

        for i in range(0, len(effects)):
            r = [x_starts[i % 4], y_start - 18 * self.sc * (i // 4), 16 * self.sc, 16 * self.sc]
            if i >= len(self._status_imgs):
                self._status_imgs.append(StatusEffectImage(effects[i], r))
            else:
                cur_img = self._status_imgs[i]
                cur_img.effect = effects[i]
                cur_img.rect = r
                cur_img.update_images()

    def update_images(self):
        render_eng = RenderEngine.get_instance()
        if len(self._floating_bars) > 0:
            new_bars = []
            for fb in self._floating_bars:
                if fb[1] >= self._float_dur:
                    render_eng.remove(fb[0])
                else:
                    new_bars.append([fb[0], fb[1] + 1])
            self._floating_bars = new_bars

        p_state = gs.get_instance().player_state()
        cur_hp = p_state.hp()
        max_hp = p_state.max_hp()

        # TODO this effect is actually quite cool, consider re-enabling it
        new_damage = 0

        if self._top_img is None:
            self._top_img = ImageBundle(spriteref.UI.status_bar_base, 0, 0,
                                        layer=spriteref.UI_0_LAYER, scale=self.sc, depth=BG_DEPTH)
        if self._bar_img is None:
            self._bar_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=self.sc, depth=BG_DEPTH + 1)

        x = RenderEngine.get_instance().get_game_size()[0] // 2 - self._top_img.width() // 2
        y = RenderEngine.get_instance().get_game_size()[1] - self._top_img.height()

        self._rect = [x, y, self._top_img.width(), self._top_img.height()]

        hp_pcnt_full = Utils.bound(cur_hp / max_hp, 0.0, 1.0)
        bar_w = spriteref.UI.health_bar_full.width() * self.sc
        bar_x = RenderEngine.get_instance().get_game_size()[0] // 2 - bar_w // 2

        self._bar_rect = [bar_x, y, bar_w, 16 * self.sc]

        if new_damage > 0:
            pcnt_full = Utils.bound(new_damage / max_hp, 0.0, 1.0)
            dmg_x = int(bar_x + hp_pcnt_full * bar_w)
            dmg_sprite = spriteref.UI.get_health_bar(pcnt_full)
            dmg_img = ImageBundle(dmg_sprite, dmg_x, 0, layer=spriteref.UI_0_LAYER, scale=self.sc, depth=0)
            self._floating_bars.append([dmg_img, 0])

        bar_color = (1.0, 0.25, 0.25)

        for i in range(0, len(self._floating_bars)):
            img, cur_dur = self._floating_bars[i]
            prog = Utils.bound(cur_dur / self._float_dur, 0.0, 1.0)
            h_offs = int(self._float_height * prog)
            g = bar_color[1] * (1 - prog)
            b = bar_color[2] * (1 - prog)

            self._floating_bars[i][0] = img.update(new_y=(y - h_offs), new_color=(1.0, g, b))

        self._top_img = self._top_img.update(new_x=x, new_y=y)
        bar_sprite = spriteref.UI.get_health_bar(hp_pcnt_full)

        glow_factor = (1 - hp_pcnt_full) * 0.2 * math.cos(((gs.get_instance().anim_tick % 6) / 6) * 2 * (3.1415))
        color = (bar_color[0], bar_color[1] + glow_factor, bar_color[2] + glow_factor)

        self._bar_img = self._bar_img.update(new_model=bar_sprite, new_x=bar_x, new_y=y, new_color=color)

        self._update_action_icons()
        self._update_status_effect_icons()
        self._update_sidepanel_buttons()
        self._update_move_buttons()

    def all_child_imgs(self):
        for i in self._action_imgs:
            if i is not None:
                yield i
        for i in self._status_imgs:
            yield i
        for i in self._sidepanel_buttons:
            if i is not None:
                yield i
        for i in self._move_buttons:
            if i is not None:
                yield i

    def is_dirty(self):
        return True

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        if self._bar_img is not None:
            yield self._bar_img
        if self._top_img is not None:
            yield self._top_img
        for floating_bar in self._floating_bars:
            yield floating_bar[0]
        for sidepanel_button in self._sidepanel_buttons:
            if sidepanel_button is not None:
                for bun in sidepanel_button.all_bundles():
                    yield bun
        for move_button in self._move_buttons:
            if move_button is not None:
                for bun in move_button.all_bundles():
                    yield bun


class TextBuilder:
    def __init__(self, text=""):
        self._text = text
        self._custom_colors = {}

    def add(self, text, color=None):
        if color is not None:
            for i in range(0, len(text)):
                self._custom_colors[len(self._text) + i] = color
        self._text += text

        return self

    def add_line(self, text, color=None):
        self.add(text + "\n", color=color)

    def text(self):
        return self._text

    def custom_colors(self):
        return self._custom_colors

    def __eq__(self, other):
        if isinstance(other, TextBuilder):
            return self.text() == other.text() and self.custom_colors() == other.custom_colors()
        else:
            return False

    def __hash__(self):
        return hash((self.text(), self.custom_colors()))


class TextImage:

    INVISIBLE_CHAR = "`"

    def __init__(self, x, y, text, layer, color=(1, 1, 1), scale=0.5, depth=0,
                 x_kerning=1, y_kerning=0, x_leading_kerning=0, custom_colors=None, font_lookup=None):

        self.font_lookup = spriteref.default_font_lookup if font_lookup is None else font_lookup

        self.x = x
        self.y = y
        self.text = text
        self.layer = layer
        self.color = color
        self.depth = depth
        self.custom_colors = {} if custom_colors is None else custom_colors  # int index -> (int, int, int) color
        self.scale = scale
        self._letter_images = []
        self._letter_image_indexes = []

        self.y_kerning = y_kerning
        self.x_kerning = x_kerning

        self.x_leading_kerning = x_leading_kerning

        self._build_images()

        self.actual_size = self._recalc_size()

    def _recalc_size(self):
        x_range = [None, None]
        y_range = [None, None]
        for img in self.all_bundles():
            x_range[0] = img.x() if x_range[0] is None else min(x_range[0], img.x())
            x_range[1] = img.x() + img.width() if x_range[1] is None else max(x_range[1], img.x() + img.width())
            y_range[0] = img.y() if y_range[0] is None else min(y_range[0], img.y())
            y_range[1] = img.y() + img.height() if y_range[1] is None else max(y_range[1], img.y() + img.height())

        if x_range[0] is None:
            return (0, 0)

        if x_range[1] - x_range[0] > 0:
            x_range[1] += self.x_leading_kerning * self.scale

        return (x_range[1] - x_range[0], y_range[1] - y_range[0])

    @staticmethod
    def calc_width(text, scale, font_lookup=None, x_kerning=1, x_leading_kerning=0):
        if font_lookup is None:
            font_lookup = spriteref.default_font_lookup

        max_line_w = 0
        cur_line_w = x_leading_kerning * scale
        char_w = (font_lookup.get_char("a").width() + x_kerning) * scale
        for c in text:
            if c == "\n":
                cur_line_w = x_leading_kerning * scale
            else:
                cur_line_w += char_w
                max_line_w = max(max_line_w, cur_line_w - x_kerning * scale)  # ignore trailing kerning
        return max_line_w

    @staticmethod
    def calc_line_height(scale, y_kerning=0, font_lookup=None):
        if font_lookup is None:
            font_lookup = spriteref.default_font_lookup

        return (font_lookup.get_char("a").height() + y_kerning) * scale

    def get_text(self):
        return self.text

    def size(self):
        return self.actual_size

    def w(self):
        return self.actual_size[0]

    def h(self):
        return self.actual_size[1]

    def line_height(self):
        return (self.font_lookup.get_char("a").height() + self.y_kerning) * self.scale

    def _build_images(self):
        ypos = self.y_kerning * self.scale
        xpos = self.x_leading_kerning * self.scale

        a_sprite = self.font_lookup.get_char("a")
        idx = 0

        chars = [c for c in self.text]

        for i in range(0, len(chars)):
            c = chars[i]
            if (c == " " or c == TextImage.INVISIBLE_CHAR) and (i != 0 and i != len(chars)-1):
                xpos += (self.x_kerning + a_sprite.width()) * self.scale
            elif c == "\n":
                xpos = self.x_leading_kerning * self.scale
                ypos += (self.y_kerning + a_sprite.height()) * self.scale
            else:
                sprite = self.font_lookup.get_char(c)

                if idx in self.custom_colors:
                    color = self.custom_colors[idx]
                else:
                    color = self.color

                img = ImageBundle(sprite, self.x + xpos, self.y + ypos, layer=self.layer,
                                  scale=self.scale, color=color, depth=self.depth)

                self._letter_images.append(img)
                self._letter_image_indexes.append(idx)
                xpos += (self.x_kerning + sprite.width()) * self.scale

            idx += 1

    def _unbuild_images(self):
        render_eng = RenderEngine.get_instance()
        for bun in self._letter_images:
            if bun is not None:
                render_eng.remove(bun)
        self._letter_images.clear()
        self._letter_image_indexes.clear()

    def update(self, new_text=None, new_x=None, new_y=None, new_scale=None,
               new_depth=None, new_color=None, new_custom_colors=None):
        dx = 0 if new_x is None else new_x - self.x
        dy = 0 if new_y is None else new_y - self.y
        self.custom_colors = new_custom_colors if new_custom_colors is not None else self.custom_colors
        self.color = new_color if new_color is not None else self.color

        text_changed = new_text is not None and new_text != self.text
        scale_changed = new_scale is not None and new_scale != self.scale

        if text_changed or scale_changed:
            self._unbuild_images()
            self.text = new_text if new_text is not None else self.text
            self.scale = new_scale if new_scale is not None else self.scale
            self._build_images()

        new_imgs = []
        for letter, idx in zip(self._letter_images, self._letter_image_indexes):
            letter_new_x = letter.x() + dx
            letter_new_y = letter.y() + dy
            if idx in self.custom_colors:
                color = self.custom_colors[idx]
            else:
                color = self.color
            new_imgs.append(letter.update(new_x=letter_new_x, new_y=letter_new_y,
                                          new_depth=new_depth, new_color=color))

        self._letter_images = new_imgs
        self.x = new_x if new_x is not None else self.x
        self.y = new_y if new_y is not None else self.y
        self.actual_size = self._recalc_size()

        return self

    def all_bundles(self):
        for b in self._letter_images:
            if b is not None:
                yield b

    @staticmethod
    def wrap_words_to_fit(text, scale, width, x_kerning=0):
        split_on_newlines = text.split("\n")
        if len(split_on_newlines) > 1:
            """if it's got newlines, split it, call this method again, and re-combine"""
            wrapped_substrings = []
            for line in split_on_newlines:
                wrapped_substrings.append(TextImage.wrap_words_to_fit(line, scale, width, x_kerning=x_kerning))

            return "\n".join(wrapped_substrings)

        text = text.replace("\n", " ")  # shouldn't be any at this point, but just to be safe~
        words = text.split(" ")
        lines = []
        cur_line = []

        while len(words) > 0:
            if len(cur_line) == 0:
                cur_line.append(words[0])
                words = words[1:]

            if len(words) == 0:
                lines.append(" ".join(cur_line))
                cur_line.clear()

            elif TextImage.calc_width(" ".join(cur_line + [words[0]]), scale, x_kerning=x_kerning) > width:
                lines.append(" ".join(cur_line))
                cur_line.clear()

            elif len(words) > 0:
                cur_line.append(words[0])
                words = words[1:]
                if len(words) == 0:
                    lines.append(" ".join(cur_line))

        return "\n".join(lines)


class OutlinedTextImage(TextImage):
    """beware - these are 5 (or 9) times more expensive to render than regular text."""

    def __init__(self, x, y, text, layer, color=(1, 1, 1), outline_color=(0, 0, 0), outline_thickness=1,
                 outline_depth=None, scale=1, depth=0, x_kerning=1, y_kerning=0,
                 custom_colors=None, font_lookup=None, outline_diagonals=False):

        self.outline_text_imgs = []
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        self.outline_depth = outline_depth if outline_depth is not None else depth + 1
        self.outline_diagonals = outline_diagonals

        TextImage.__init__(self, x, y, text, layer, color=color, scale=scale, depth=depth,
                           x_kerning=x_kerning, y_kerning=y_kerning, custom_colors=custom_colors,
                           font_lookup=font_lookup)

    def _get_offsets(self):
        t = self.outline_thickness
        offsets = [(-t, 0), (t, 0), (0, -t), (0, t)]

        if self.outline_diagonals:
            offsets.extend([(t, t), (t, -t), (-t, t), (-t, -t)])

        return offsets

    def _build_images(self):
        super()._build_images()

        for offs in self._get_offsets():
            outline_img = TextImage(self.x + offs[0], self.y + offs[1], self.text, self.layer,
                                    color=self.outline_color,
                                    scale=self.scale,
                                    depth=self.outline_depth,
                                    x_kerning=self.x_kerning,
                                    y_kerning=self.y_kerning,
                                    font_lookup=self.font_lookup)

            self.outline_text_imgs.append(outline_img)

    def _unbuild_images(self):
        super()._unbuild_images()
        for outline_img in self.outline_text_imgs:
            outline_img._unbuild_images()

        self.outline_text_imgs.clear()

    def update(self, new_text=None, new_x=None, new_y=None, new_scale=None, new_depth=None, new_color=None,
               new_outline_color=None, new_outline_thickness=None, new_outline_depth=None, new_custom_colors=None):

        super().update(new_text=new_text, new_x=new_x, new_y=new_y, new_scale=new_scale, new_depth=new_depth,
                       new_color=new_color, new_custom_colors=new_custom_colors)

        self.outline_depth = self.outline_depth if new_outline_depth is None else new_outline_depth
        self.outline_color = self.outline_color if new_outline_color is None else new_outline_color
        self.outline_thickness = self.outline_thickness if new_outline_thickness is None else new_outline_thickness

        offs = self._get_offsets()
        for i in range(0, len(self.outline_text_imgs)):
            self.outline_text_imgs[i] = self.outline_text_imgs[i].update(new_x=new_x + offs[i][0],
                                                                         new_y=new_y + offs[i][1],
                                                                         new_text=new_text,
                                                                         new_color=self.outline_color,
                                                                         new_scale=new_scale,
                                                                         new_depth=self.outline_depth)
        return self

    def all_bundles(self):
        for outline_img in self.outline_text_imgs:
            for bun in outline_img.all_bundles():
                yield bun
        for bun in super().all_bundles():
            yield bun


class ItemImage:

    def __init__(self, x, y, item, layer, scale, depth):
        self.x = x
        self.y = y
        self.item = item
        self.scale = scale
        self.depth = depth
        self._bundles = []
        self.layer = layer

        self._build_images()

    def _build_images(self):
        if isinstance(self.item, item_module.StatCubesItem):
            for cube in self.item.cubes:
                # pretty special-casey but.. it's fine
                art = 0 if cube not in self.item.cube_art else self.item.cube_art[cube]
                sprite = spriteref.Items.piece_bigs[art]
                xpos = self.x + sprite.width()*self.scale*cube[0]
                ypos = self.y + sprite.height()*self.scale*cube[1]
                img = ImageBundle(sprite, xpos, ypos, layer=self.layer, scale=self.scale, color=self.item.color, depth=self.depth)
                self._bundles.append(img)
        elif isinstance(self.item, item_module.SpriteItem):
            sprite = self.item.big_sprite()
            img = ImageBundle(sprite, self.x, self.y, layer=self.layer, rotation=self.item.sprite_rotation(), scale=self.scale, depth=self.depth, color=self.item.color)
            self._bundles.append(img)

    def all_bundles(self):
        for b in self._bundles:
            yield b

    @staticmethod
    def calc_size(item, scale):
        if isinstance(item, item_module.StatCubesItem):
            sprite = spriteref.Items.piece_bigs[0]
            return (scale*sprite.width()*item.w(), scale*sprite.height()*item.h())
        elif isinstance(item, item_module.SpriteItem):
            sprite_rot = item.sprite_rotation()
            sprite = item.big_sprite()
            if sprite_rot % 2 == 0:
                return (scale * sprite.width(), scale * sprite.height())
            else:
                return (scale * sprite.height(), scale * sprite.width())


# TODO - this probably doesn't work anymore, delete?
class CinematicPanel:

    IMAGE_SCALE = 6
    TEXT_SCALE = 2

    def __init__(self):
        self.current_image_img = None
        self.current_text = ""
        self.text_img = None
        self.border = 32

    def update(self, new_sprite, new_text):
        scale = CinematicPanel.IMAGE_SCALE
        if self.current_image_img is None:
            self.current_image_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=scale)

        image_w = new_sprite.width() * scale
        new_x = RenderEngine.get_instance().get_game_size()[0] // 2 - image_w // 2
        new_y = 0 + self.border
        self.current_image_img = self.current_image_img.update(new_model=new_sprite, new_x=new_x, new_y=new_y)

        if new_text != self.current_text:
            if self.text_img is not None:
                render_eng = RenderEngine.get_instance()
                for bun in self.text_img.all_bundles():
                    render_eng.remove(bun)
                self.text_img = None

        if self.text_img is None and new_text != "":
            text_scale = CinematicPanel.TEXT_SCALE
            text_w = RenderEngine.get_instance().get_game_size()[0] - self.border*2
            text_x = self.border
            text_h = RenderEngine.get_instance().get_game_size()[1] // 5 - self.border
            text_y = RenderEngine.get_instance().get_game_size()[1] - text_h - self.border
            wrapped_text = TextImage.wrap_words_to_fit(new_text, text_scale, text_w)
            self.text_img = TextImage(text_x, text_y, wrapped_text, spriteref.UI_0_LAYER, scale=text_scale, y_kerning=2)
            self.current_text = new_text

    def all_bundles(self):
        if self.current_image_img is not None:
            yield self.current_image_img
        if self.text_img is not None:
            for bun in self.text_img.all_bundles():
                yield bun
