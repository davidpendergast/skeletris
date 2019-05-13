import math

import src.game.stats
from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.items.item as item_module
from src.utils.util import Utils
from src.game.stats import StatType
import src.game.globalstate as gs
import src.utils.colors as colors
from src.renderengine.engine import RenderEngine


class ItemGridImage:

    def __init__(self, x, y, grid, layer, scale):
        self.x = x
        self.y = y
        self.grid = grid
        self.layer = layer
        self.scale = scale
        
        self.item_images = []
        
        self._build_images()
        
    def _build_images(self):
        cellsize = spriteref.Items.piece_bigs[0].size()
        for item in self.grid.all_items():
            pos = self.grid.get_pos(item)
            x_pos = self.x + pos[0] * cellsize[0] * self.scale
            y_pos = self.y + pos[1] * cellsize[1] * self.scale
            self.item_images.append(ItemImage(x_pos, y_pos, item, self.layer, self.scale))
        
    def all_bundles(self):
        for item_img in self.item_images:
            for bun in item_img.all_bundles():
                yield bun   
        

class InventoryPanel:

    def __init__(self):
        self.player_state = gs.get_instance().player_state()
        self.state = self.player_state.inventory()
        self.layer = spriteref.UI_0_LAYER

        self.top_img = None
        self.mid_imgs = []
        self.bot_img = None

        self.title_colors = colors.LIGHT_GRAY
        self.eq_title_text = None
        self.inv_title_text = None

        sc = 2
        text_sc = 1
        
        self.total_rect = [0, 0,
                           spriteref.UI.inv_panel_top.width() * sc,
                           (128 + 16 * self.state.rows) * sc]

        self.equip_grid_rect = [8*sc, 16*sc, 80*sc, 80*sc]
        self.inv_grid_rect = [8*sc, 112*sc, 144*sc, 16*self.state.rows*sc]
        self.stats_rect = [96*sc, 16*sc, 56*sc, 80*sc]

        self.eq_title_rect = [8*sc, 0*sc + 4, 80*sc, 16*sc - 4]
        self.inv_title_rect = [8*sc, 96*sc + 4, 80*sc, 16*sc - 4]

        self.lvl_text = None
        self.att_text = None
        self.def_text = None
        self.vit_text = None
        self.hp_text = None
        self.spd_text = None
        
        self.equip_img = None
        self.inv_img = None
        
        self._build_images(sc, text_sc)

    def _build_title_img(self, text, rect, scale):
        res = TextImage(rect[0], 0, text, self.layer, scale=scale, color=self.title_colors)
        new_y = rect[1] + (rect[3] - res.line_height()) // 2
        return res.update(new_y=new_y)
        
    def _build_images(self, sc, text_sc):
        self.top_img = ImageBundle(spriteref.UI.inv_panel_top, 0, 0, layer=self.layer, scale=sc)
        for i in range(0, self.state.rows - 1):
            y = (128 + i*16)*sc
            self.mid_imgs.append(ImageBundle(spriteref.UI.inv_panel_mid, 0, y, layer=self.layer, scale=sc))
        y = (128 + self.state.rows*16 - 16)*sc
        self.bot_img = ImageBundle(spriteref.UI.inv_panel_bot, 0, y, layer=self.layer, scale=sc)
        
        self.inv_title_text = self._build_title_img("Inventory", self.inv_title_rect, text_sc)
        self.eq_title_text = self._build_title_img("Equipment", self.eq_title_rect, text_sc)

        # self.lvl_text = TextImage(0, 0, "lvl", self.layer, scale=text_sc)
        # self.att_text = TextImage(0, 0, "att", self.layer, scale=text_sc, color=item_module.STAT_COLORS[src.game.stats.StatType.ATT])
        # self.def_text = TextImage(0, 0, "def", self.layer, scale=text_sc, color=item_module.STAT_COLORS[src.game.stats.StatType.DEF])
        # self.vit_text = TextImage(0, 0, "vit", self.layer, scale=text_sc, color=item_module.STAT_COLORS[src.game.stats.StatType.VIT])
        # self.spd_text = TextImage(0, 0, "spd", self.layer, scale=text_sc, color=item_module.STAT_COLORS[src.game.stats.StatType.SPEED])
        # self.hp_text = TextImage(0, 0, "hp", self.layer, scale=text_sc, color=item_module.STAT_COLORS[None])

        self.update_stats_imgs()

        e_xy = (self.equip_grid_rect[0], self.equip_grid_rect[1])
        self.equip_img = ItemGridImage(*e_xy, self.state.equip_grid, self.layer, sc)

        inv_xy = (self.inv_grid_rect[0], self.inv_grid_rect[1])
        self.inv_img = ItemGridImage(*inv_xy, self.state.inv_grid, self.layer, sc)

    def update_stats_imgs(self):
        text_sc = 1
        s_xy = [self.stats_rect[0], self.stats_rect[1]]

        lvl_txt = "LVL:{}".format(gs.get_instance().get_zone_level())
        self.lvl_text = TextImage(*s_xy, lvl_txt, self.layer, scale=text_sc)
        s_xy[1] += self.lvl_text.line_height()

        att_value = (self.player_state.stat_value(StatType.ATT) +
                     self.player_state.stat_value(StatType.UNARMED_ATT))
        att_str = "ATT:{}".format(att_value)
        self.att_text = TextImage(*s_xy, att_str, self.layer, scale=text_sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.ATT])
        s_xy[1] += self.att_text.line_height()

        def_str = "DEF:{}".format(self.player_state.stat_value(StatType.DEF))
        self.def_text = TextImage(*s_xy, def_str, self.layer, scale=text_sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.DEF])
        s_xy[1] += self.def_text.line_height()

        vit_str = "VIT:{}".format(self.player_state.stat_value(StatType.VIT))
        self.vit_text = TextImage(*s_xy, vit_str, self.layer, scale=text_sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.VIT])
        s_xy[1] += self.vit_text.line_height()

        spd_str = "SPD:{}".format(self.player_state.stat_value(StatType.SPEED))
        self.spd_text = TextImage(*s_xy, spd_str, self.layer, scale=text_sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.SPEED])
        s_xy[1] += self.spd_text.line_height()

        hp_str = "HP: {}/{}".format(self.player_state.hp(), self.player_state.max_hp())
        self.hp_text = TextImage(*s_xy, hp_str, self.layer, scale=text_sc,
                                 color=item_module.STAT_COLORS[None])
        s_xy[1] += self.hp_text.line_height()

    def all_bundles(self):
        yield self.top_img
        for img in self.mid_imgs:
            yield img
        yield self.bot_img
        for bun in self.inv_title_text.all_bundles():
            yield bun
        for bun in self.eq_title_text.all_bundles():
            yield bun
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
        for bun in self.equip_img.all_bundles():
            yield bun 
        for bun in self.inv_img.all_bundles():
            yield bun


class DialogPanel:

    BORDER_SIZE = 8, 8
    TEXT_SCALE= 1
    SIZE = (256 * 2 - 16 * 2, 48 * 2 - 16)

    def __init__(self, dialog):
        self._dialog = dialog
        self._border_imgs = []
        self._speaker_img = None
        self._text_displaying = ""
        self._option_selected = None
        self._text_img = None
        self._bg_imgs = []

    def get_dialog(self):
        return self._dialog

    def update_images(self, text, sprite, left_side):
        """
            returns: True if needs a full render engine update, else False
        """
        needs_update = False

        x = gs.get_instance().screen_size[0] // 2 - DialogPanel.SIZE[0] // 2
        y = gs.get_instance().screen_size[1] - HealthBarPanel.SIZE[1] - DialogPanel.SIZE[1]
        lay = spriteref.UI_0_LAYER

        if len(self._border_imgs) == 0:
            bw, bh = DialogPanel.BORDER_SIZE
            right_x = x + DialogPanel.SIZE[0]
            border_sprites = spriteref.UI.text_panel_edges

            for i in range(0, DialogPanel.SIZE[0] // bw):
                top_bord = ImageBundle(border_sprites[1], x + bw * i, y - bh, layer=lay, scale=2)
                self._border_imgs.append(top_bord)
            for i in range(0, DialogPanel.SIZE[1] // bh):
                l_bord = ImageBundle(border_sprites[3], x - bw, y + bh * i, layer=lay, scale=2)
                self._border_imgs.append(l_bord)
                r_bord = ImageBundle(border_sprites[5], right_x, y + bh * i,  layer=lay, scale=2)
                self._border_imgs.append(r_bord)
            self._border_imgs.append(ImageBundle(border_sprites[0], x - bw, y - bh, layer=lay, scale=2))
            self._border_imgs.append(ImageBundle(border_sprites[2], right_x, y - bh, layer=lay, scale=2))
            needs_update = True

        if len(self._bg_imgs) == 0:
            bg_sprite = spriteref.UI.text_panel_edges[4]
            bg_w, bg_h = bg_sprite.size()
            sc = min(DialogPanel.SIZE[0] // bg_w, DialogPanel.SIZE[1] // bg_h)
            bg_w *= sc
            bg_h *= sc
            for x1 in range(0, DialogPanel.SIZE[0] // bg_w):
                for y1 in range(0, DialogPanel.SIZE[1] // bg_h):
                    self._bg_imgs.append(ImageBundle(bg_sprite, x + x1 * bg_w, y + y1 * bg_h, layer=lay, scale=sc))
            needs_update = True

        text_buffer = 6, 6
        text_area = [x + text_buffer[0], y + text_buffer[1],
                     DialogPanel.SIZE[0] - text_buffer[0] * 2,
                     DialogPanel.SIZE[1] - text_buffer[1] * 2]

        if sprite is not None:
            sprite_buffer = 6, 4
            if self._speaker_img is None:
                y_pos = y + DialogPanel.SIZE[1] // 2 - sprite.height() * 2 // 2
                if left_side:
                    x_pos = x + sprite_buffer[0]
                else:
                    x_pos = x + DialogPanel.SIZE[0] - sprite.width() * 2 - sprite_buffer[0]
                self._speaker_img = ImageBundle(sprite, x_pos, y_pos, layer=lay, scale=2)
            self._speaker_img = self._speaker_img.update(new_model=sprite)

            if left_side:
                text_x = x + self._speaker_img.width() + sprite_buffer[0] + text_buffer[0]
            else:
                text_x = x + text_buffer[0]

            text_area = [text_x, y + text_buffer[0],
                         DialogPanel.SIZE[0] - self._speaker_img.width() - text_buffer[0] - sprite_buffer[0],
                         DialogPanel.SIZE[1] - text_buffer[1] * 2]
            # gets updated automatically

        if len(text) > 0 and self._text_img is None:
            wrapped_text = TextImage.wrap_words_to_fit(text, DialogPanel.TEXT_SCALE, text_area[2])
            custom_colors = {}
            if self._option_selected is not None:
                opt_text = self._dialog.get_options()[self._option_selected]

                try:
                    pos = wrapped_text.index(opt_text)
                    for i in range(pos, pos + len(opt_text)):
                        custom_colors[i] = (255, 0, 0)
                    print("custom_colors={}".format(custom_colors))
                except ValueError:
                    print("ERROR: option \"{}\" missing from dialog \"{}\"".format(opt_text, wrapped_text))

            self._text_img = TextImage(text_area[0], text_area[1], wrapped_text, layer=lay, scale=DialogPanel.TEXT_SCALE,
                                       y_kerning=3,
                                       custom_colors=custom_colors)
            needs_update = True

        return needs_update

    def update(self):
        do_text_rebuild = False

        new_text = self._dialog.get_visible_text(invisible_sub=TextImage.INVISIBLE_CHAR)
        if self._text_displaying != new_text and self._text_img is not None:
            do_text_rebuild = True

        self._text_displaying = new_text

        option_idx = None
        if len(self._dialog.get_options()) > 0 and self._dialog.is_done_scrolling():
            option_idx = self._dialog.get_selected_opt_idx()

        if option_idx != self._option_selected:
            do_text_rebuild = True
            self._option_selected = option_idx

        render_eng = RenderEngine.get_instance()

        new_sprite = self._dialog.get_visible_sprite()
        if new_sprite is None and self._speaker_img is not None:
            render_eng.remove(self._speaker_img)
            self._speaker_img = None

        if do_text_rebuild:
            for bun in self._text_img.all_bundles():
                render_eng.remove(bun)
            self._text_img = None

        full_update = self.update_images(self._text_displaying, new_sprite,
                                         self._dialog.get_sprite_side())

        if full_update:
            for bun in self.all_bundles():
                render_eng.update(bun)
        elif self._speaker_img is not None:
            render_eng.update(self._speaker_img)

    def all_bundles(self):
        for bg in self._bg_imgs:
            yield bg
        for bord in self._border_imgs:
            yield bord
        if self._speaker_img is not None:
            yield self._speaker_img
        if self._text_img is not None:
            for bun in self._text_img.all_bundles():
                yield bun


class PopupPanel:

    def __init__(self, w, h):
        self.rect = [0, 0, w, h]

    def set_xy(self, x, y):
        """Note that this gets set by MenuState every frame"""
        self.rect[0] = x
        self.rect[1] = y

    def get_rect(self):
        return self.rect

    def size(self):
        return (self.rect[2], self.rect[3])

    def update(self, world, input_state):
        pass

    def should_destroy(self, world, input_state):
        return False

    def prepare_to_destroy(self, world, input_state):
        pass

    def all_bundles(self):
        pass


class HealthBarPanel:

    SIZE = (400 * 2, 53 * 2)

    def __init__(self):
        self._top_img = None
        self._bar_img = None
        self._floating_bars = []  # list of [img, duration]

        # (base_img, cooldown_img, left text, right text)
        self._action_imgs = [(None, None, None, None)] * 6

        self._item_images = {}  # (item, grid_pos) -> img

        self._float_dur = 30
        self._float_height = 30

    def update_images(self, cur_hp, max_hp, new_damage, new_healing, action_states):
        if self._top_img is None:
            self._top_img = ImageBundle(spriteref.UI.status_bar_base, 0, 0,
                                        layer=spriteref.UI_0_LAYER, scale=2)
        if self._bar_img is None:
            self._bar_img = ImageBundle.new_bundle(layer_id=spriteref.UI_0_LAYER, scale=2)

        x = gs.get_instance().screen_size[0] // 2 - self._top_img.width() // 2
        y = gs.get_instance().screen_size[1] - self._top_img.height()

        hp_pcnt_full = Utils.bound(cur_hp / max_hp, 0.0, 1.0)
        bar_w = spriteref.UI.health_bar_full.width() * 2
        bar_x = gs.get_instance().screen_size[0] // 2 - bar_w // 2

        if new_damage > 0:
            pcnt_full = Utils.bound(new_damage / max_hp, 0.0, 1.0)
            dmg_x = int(bar_x + hp_pcnt_full * bar_w)
            dmg_sprite = spriteref.UI.get_health_bar(pcnt_full)
            dmg_img = ImageBundle(dmg_sprite, dmg_x, 0, layer=spriteref.UI_0_LAYER, scale=2)
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

        render_eng = RenderEngine.get_instance()

        x_start = [x + 87 * 2 + i*40*2 for i in range(0, 3)] + [x + 205*2 + i*40*2 for i in range(0, 3)]
        y_start = y + 19 * 2
        for i in range(0, len(action_states)):
            state = action_states[i]
            cur_img = [img for img in self._action_imgs[i]]
            if state is None:
                for img in cur_img:
                    if img is not None:
                        for bun in img.all_bundles():
                            render_eng.remove(bun)
                self._action_imgs[i] = (None, None, None, None)
            else:
                """Action Image"""
                if cur_img[0] is None:
                    cur_img[0] = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2)
                cur_img[0] = cur_img[0].update(new_model=state[0], new_x=x_start[i], new_y=y_start)

                """Bonus Images"""
                self.handle_bonus_images(i, x_start[i], y_start)

                """Cooldown Image"""
                if state[1] >= 1:
                    if cur_img[1] is not None:
                        render_eng.remove(cur_img[1])
                        cur_img[1] = None
                else:
                    if cur_img[1] is None:
                        cur_img[1] = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2)
                    cur_img[1] = cur_img[1].update(new_model=spriteref.get_cooldown_img(state[1]),
                                                   new_x=x_start[i], new_y=y_start)

                """Left Text"""
                incorrect_text = state[2] is not None and cur_img[2] is not None and state[2] != cur_img[2].text
                if state[2] is None or incorrect_text:
                    if cur_img[2] is not None:
                        for bun in cur_img[2].all_bundles():
                            render_eng.remove(bun)
                        cur_img[2] = None
                if state[2] is not None:
                    if cur_img[2] is None:
                        cur_img[2] = TextImage(0, 0, state[2], spriteref.UI_0_LAYER)
                    cur_img[2] = cur_img[2].update(new_x=x_start[i] + 1,
                                                   new_y=y_start + 28*2 - cur_img[2].size()[1] - 2)

                """Right Text"""
                incorrect_text = state[3] is not None and cur_img[3] is not None and state[3] != cur_img[3].text
                if state[3] is None or incorrect_text:
                    if cur_img[3] is not None:
                        for bun in cur_img[3].all_bundles():
                            render_eng.remove(bun)
                        cur_img[3] = None
                if state[3] is not None:
                    if cur_img[3] is None:
                        cur_img[3] = TextImage(0, 0, state[3], spriteref.UI_0_LAYER)
                    color = (1, 0.5, 0.5) if state[3] == "0" else (1.0, 1.0, 1.0)
                    cur_img[3] = cur_img[3].update(new_x=x_start[i] - 3 + 28*2 - cur_img[3].size()[0],
                                                   new_y=y_start + 28 * 2 - cur_img[2].size()[1] - 2,
                                                   new_color=color)

            self._action_imgs[i] = tuple(cur_img)

    def handle_bonus_images(self, i, x_start, y_start):
        if i == 4:
            inv = gs.get_instance().player_state().inventory()
            items = inv.all_equipped_items()
            needs_rebuilt = False
            new_item_map = {}
            for item in items:
                pos = inv.equip_grid.get_pos(item)
                if (item, pos) not in self._item_images:
                    needs_rebuilt = True
                new_item_map[(item, pos)] = None

            if len(new_item_map) != len(self._item_images):
                needs_rebuilt = True

            if needs_rebuilt:
                render_eng = RenderEngine.get_instance()
                for key in self._item_images:
                    render_eng.remove(self._item_images[key])
                self._item_images = new_item_map
                for key in self._item_images:
                    item, pos = key
                    img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2)
                    self._item_images[key] = img.update(
                        new_x=x_start + 8 + pos[0] * 8,
                        new_y=y_start + 6 + pos[1] * 8,
                        new_model=spriteref.get_item_entity_sprite(item.cubes),
                        new_color=(1, 1, 1))

    def get_action_item_state(self, idx):
        """returns: None if it's locked, else (sprite, cooldown_value, left_text, right_text)"""
        return None

    def update(self, world, input_state):
        p_state = gs.get_instance().player_state()
        new_dmg, new_healing = 0, 0

        render_eng = RenderEngine.get_instance()

        if len(self._floating_bars) > 0:
            new_bars = []
            for fb in self._floating_bars:
                if fb[1] >= self._float_dur:
                    render_eng.remove(fb[0])
                else:
                    new_bars.append([fb[0], fb[1] + 1])
            self._floating_bars = new_bars

        action_states = [self.get_action_item_state(i) for i in range(0, 6)]
        self.update_images(p_state.hp(), p_state.max_hp(), new_dmg, new_healing, action_states)

        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        if self._bar_img is not None:
            yield self._bar_img
        if self._top_img is not None:
            yield self._top_img
        for floating_bar in self._floating_bars:
            yield floating_bar[0]
        for img_tuple in self._action_imgs:
            for img in img_tuple:
                if img is not None:
                    for bun in img.all_bundles():
                        yield bun
        for key in self._item_images:
            if self._item_images[key] is not None:
                yield self._item_images[key]


class TextImage:

    INVISIBLE_CHAR = "`"

    X_KERNING = 0
    Y_KERNING = 0

    def __init__(self, x, y, text, layer, try_split=True, color=(1, 1, 1), scale=1, center_w=None, y_kerning=None,
                 custom_colors=None):
        self.x = x
        self.center_w = center_w
        self.y = y
        self.text = text
        self.layer = layer
        self.color = color
        self.custom_colors = {} if custom_colors is None else custom_colors  # int index -> (int, int, int) color
        self.scale = scale
        self._letter_images = []
        self._letter_image_indexes = []
        self.y_kerning = TextImage.Y_KERNING if y_kerning is None else y_kerning

        self._text_chunks = spriteref.split_text(self.text) if try_split else list(self.text)

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

        return (x_range[1] - x_range[0], y_range[1] - y_range[0])

    @staticmethod
    def calc_width(text, scale):
        max_line_w = 0
        cur_line_w = 0
        char_w = (spriteref.Font.get_char("a").width() + TextImage.X_KERNING) * scale
        for c in text:
            if c == "\n":
                cur_line_w = 0
            else:
                cur_line_w += char_w
                max_line_w = max(max_line_w, cur_line_w)
        return max_line_w

    def size(self):
        return self.actual_size

    def line_height(self):
        return (spriteref.Font.get_char("a").height() + self.y_kerning) * self.scale

    def _build_images(self):
        ypos = TextImage.Y_KERNING

        if self.center_w is not None:
            true_width = TextImage.calc_width(self.text, self.scale)
            x_shift = self.x + self.center_w // 2 - true_width // 2
        else:
            x_shift = TextImage.X_KERNING

        xpos = x_shift

        a_sprite = spriteref.Font.get_char("a")
        idx = 0
        for chunk in self._text_chunks:
            if chunk == " " or chunk == TextImage.INVISIBLE_CHAR:
                xpos += (TextImage.X_KERNING + a_sprite.width()) * self.scale
            elif chunk == "\n":
                xpos = x_shift
                ypos += (self.y_kerning + a_sprite.height()) * self.scale
            else:
                if len(chunk) == 1:
                    sprite = spriteref.Font.get_char(chunk)
                else:
                    sprite = spriteref.cached_text_imgs[chunk]

                if idx in self.custom_colors:
                    color = self.custom_colors[idx]
                else:
                    color = self.color

                img = ImageBundle(sprite, self.x + xpos, self.y + ypos, layer=self.layer,
                                  scale=self.scale, color=color)

                self._letter_images.append(img)
                self._letter_image_indexes.append(idx)
                xpos += (TextImage.X_KERNING + sprite.width()) * self.scale

            idx += len(chunk)

    def update(self, new_x=None, new_y=None, new_depth=None, new_color=None, new_custom_colors=None):
        dx = 0 if new_x is None else new_x - self.x
        dy = 0 if new_y is None else new_y - self.y
        self.custom_colors = new_custom_colors if new_custom_colors is not None else self.custom_colors
        self.color = new_color if new_color is not None else self.color

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
    def wrap_words_to_fit(text, scale, width):
        split_on_newlines = text.split("\n")
        if len(split_on_newlines) > 1:
            """if it's got newlines, split it, call this method again, and re-combine"""
            wrapped_substrings = [TextImage.wrap_words_to_fit(line, scale, width) for line in split_on_newlines]
            return "\n".join(wrapped_substrings)

        text = text.replace("\n", " ")  # shouldn't be any at this point, but just to be safe~
        words = text.split(" ")
        lines = []
        cur_line = []
        while len(words) > 0:
            if len(cur_line) == 0:
                cur_line.append(words[0])
                words = words[1:]
            if len(words) == 0 or TextImage.calc_width(" ".join(cur_line + [words[0]]), scale) > width:
                lines.append(" ".join(cur_line))
                cur_line.clear()
            elif len(words) > 0:
                cur_line.append(words[0])
                words = words[1:]
                if len(words) == 0:
                    lines.append(" ".join(cur_line))

        return "\n".join(lines)


class ItemImage:

    def __init__(self, x, y, item, layer, scale):
        self.x = x
        self.y = y
        self.item = item
        self.scale = scale
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
                img = ImageBundle(sprite, xpos, ypos, layer=self.layer, scale=self.scale, color=self.item.color)
                self._bundles.append(img)
        elif isinstance(self.item, item_module.SpriteItem):
            sprite = self.item.big_sprite()
            img = ImageBundle(sprite, self.x, self.y, layer=self.layer, rotation=self.item.sprite_rotation(), scale=self.scale, color=self.item.color)
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
            self.current_image_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale)

        image_w = new_sprite.width() * scale
        new_x = gs.get_instance().screen_size[0] // 2 - image_w // 2
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
            text_w = gs.get_instance().screen_size[0] - self.border*2
            text_x = self.border
            text_h = gs.get_instance().screen_size[1] // 5 - self.border
            text_y = gs.get_instance().screen_size[1] - text_h - self.border
            wrapped_text = TextImage.wrap_words_to_fit(new_text, text_scale, text_w)
            self.text_img = TextImage(text_x, text_y, wrapped_text, spriteref.UI_0_LAYER, scale=text_scale, y_kerning=2)
            self.current_text = new_text

    def all_bundles(self):
        if self.current_image_img is not None:
            yield self.current_image_img
        if self.text_img is not None:
            for bun in self.text_img.all_bundles():
                yield bun
