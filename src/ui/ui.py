import math

import src.game.stats
from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.items.item as item_module
from src.utils.util import Utils
from src.game.stats import PlayerStatType, StatType


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
        cellsize = spriteref.item_piece_bigs[0].size()
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

    def __init__(self, gs):
        self.player_state = gs.player_state()
        self.state = self.player_state.inventory()
        self.layer = spriteref.UI_0_LAYER
        self.kill_count = gs.kill_count
        self.dungeon_level = gs.dungeon_level

        self.top_img = None
        self.mid_imgs = []
        self.bot_img = None
        self.title_text = None

        sc = 2
        
        self.total_rect = [0, 0, spriteref.inv_panel_top.width()*sc, 
                (128 + 16*self.state.rows)*sc]
        self.equip_grid_rect = [8*sc, 24*sc, 80*sc, 80*sc]
        self.inv_grid_rect = [8*sc, 112*sc, 144*sc, 16*self.state.rows*sc]
        self.info_rect = [96*sc, 24*sc, 56*sc, 32*sc]
        self.stats_rect = [96*sc, 64*sc, 56*sc, 40*sc]
        
        self.info_text = None
        self.att_text = None
        self.def_text = None
        self.vit_text = None
        self.hp_text = None
        self.dps_text = None 
        
        self.equip_img = None
        self.inv_img = None
        
        self._build_images(sc, gs)

    def gs_info_is_outdated(self, gs):
        return (self.kill_count != gs.kill_count or
                self.dungeon_level != gs.dungeon_level)
        
    def _build_images(self, sc, gs):
        self.top_img = ImageBundle(spriteref.inv_panel_top, 0, 0, layer=self.layer, scale=sc)
        for i in range(0, self.state.rows - 1):
            y = (128 + i*16)*sc
            self.mid_imgs.append(ImageBundle(spriteref.inv_panel_mid, 0, y, layer=self.layer, scale=sc))
        y = (128 + self.state.rows*16 - 16)*sc
        self.bot_img = ImageBundle(spriteref.inv_panel_bot, 0, y, layer=self.layer, scale=sc)
        
        self.title_text = TextImage(8*sc, 8*sc, "Inventory", self.layer, scale=int(sc*3/2))
        
        name_str = self.player_state.name()
        lvl_str = self.player_state.level()
        info_txt = "{}\n\nLVL: {}\nROOM:{}\nKILL:{}".format(name_str, lvl_str, self.dungeon_level, self.kill_count)
        i_xy = [self.info_rect[0], self.info_rect[1]]
        self.info_text = TextImage(*i_xy, info_txt, self.layer, scale=sc)
        
        s_xy = [self.stats_rect[0], self.stats_rect[1]]
        att_str = "ATT:{}".format(self.player_state.stat_value(StatType.ATT))
        self.att_text = TextImage(*s_xy, att_str, self.layer, scale=sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.ATT])
        s_xy[1] += self.att_text.line_height()
        
        def_str = "DEF:{}".format(self.player_state.stat_value(StatType.DEF))
        self.def_text = TextImage(*s_xy, def_str, self.layer, scale=sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.DEF])
        s_xy[1] += self.def_text.line_height()
        
        vit_str = "VIT:{}".format(self.player_state.stat_value(StatType.VIT))
        self.vit_text = TextImage(*s_xy, vit_str, self.layer, scale=sc,
                                  color=item_module.STAT_COLORS[src.game.stats.StatType.VIT])
        s_xy[1] += 2 * self.def_text.line_height()
        
        hp_str = "HP: {}".format(self.player_state.stat_value(PlayerStatType.HP))
        self.hp_text = TextImage(*s_xy, hp_str, self.layer, scale=sc,
                color=item_module.STAT_COLORS[None])
        s_xy[1] += self.hp_text.line_height()
        
        dps_str = "DPS:{}".format(round(self.player_state.stat_value(PlayerStatType.DPS)))
        self.dps_text = TextImage(*s_xy, dps_str, self.layer, scale=sc,
                color=item_module.STAT_COLORS[None])
        
        e_xy = (self.equip_grid_rect[0], self.equip_grid_rect[1])
        self.equip_img = ItemGridImage(*e_xy, self.state.equip_grid, self.layer, sc)
        
        inv_xy = (self.inv_grid_rect[0], self.inv_grid_rect[1])
        self.inv_img = ItemGridImage(*inv_xy, self.state.inv_grid, self.layer, sc)
        
    def all_bundles(self):
        yield self.top_img
        for img in self.mid_imgs:
            yield img
        yield self.bot_img
        for bun in self.title_text.all_bundles():
            yield bun
        for bun in self.info_text.all_bundles():
            yield bun
        for bun in self.att_text.all_bundles():
            yield bun
        for bun in self.def_text.all_bundles():
            yield bun
        for bun in self.vit_text.all_bundles():
            yield bun
        for bun in self.hp_text.all_bundles():
            yield bun
        for bun in self.dps_text.all_bundles():
            yield bun
        for bun in self.equip_img.all_bundles():
            yield bun 
        for bun in self.inv_img.all_bundles():
            yield bun


class HealthBarPanel:

    def __init__(self):
        self._top_img = None
        self._bar_img = None
        self._floating_bars = []  # list of [img, duration]
        self._cooldown_imgs = [None] * 6
        self._potion_text = None
        self._num_potions = -1
        self._float_dur = 30
        self._float_height = 30

    def update_images(self, gs, cur_hp, max_hp, new_damage, new_healing, cooldowns):
        if self._top_img is None:
            self._top_img = ImageBundle(spriteref.status_bar_base, 0, 0,
                                        layer=spriteref.UI_0_LAYER, scale=2)
        if self._bar_img is None:
            self._bar_img = ImageBundle.new_bundle(layer_id=spriteref.UI_0_LAYER, scale=2)

        x = gs.screen_size[0] // 2 - self._top_img.width() // 2
        y = gs.screen_size[1] - self._top_img.height()

        hp_pcnt_full = Utils.bound(cur_hp / max_hp, 0.0, 1.0)
        bar_w = spriteref.health_bar_full.width() * 2
        bar_x = gs.screen_size[0] // 2 - bar_w // 2

        if new_damage > 0:
            pcnt_full = Utils.bound(new_damage / max_hp, 0.0, 1.0)
            dmg_x = int(bar_x + hp_pcnt_full * bar_w)
            dmg_sprite = spriteref.get_health_bar(pcnt_full)
            dmg_img = ImageBundle(dmg_sprite, dmg_x, 0, layer=spriteref.UI_0_LAYER, scale=2)
            self._floating_bars.append([dmg_img, 0])

        bar_color = gs.player_state().get_hp_color()

        for i in range(0, len(self._floating_bars)):
            img, cur_dur = self._floating_bars[i]
            prog = Utils.bound(cur_dur / self._float_dur, 0.0, 1.0)
            h_offs = int(self._float_height * prog)
            g = bar_color[1] * (1 - prog)
            b = bar_color[2] * (1 - prog)

            self._floating_bars[i][0] = img.update(new_y=(y - h_offs), new_color=(1.0, g, b))

        self._top_img = self._top_img.update(new_x=x, new_y=y)
        bar_sprite = spriteref.get_health_bar(hp_pcnt_full)

        glow_factor = (1 - hp_pcnt_full) * 0.2 * math.cos(((gs.anim_tick % 6) / 6) * 2 * (3.1415))
        color = (bar_color[0], bar_color[1] + glow_factor, bar_color[2] + glow_factor)

        self._bar_img = self._bar_img.update(new_model=bar_sprite, new_x=bar_x, new_y=y, new_color=color)

        for i in range(0, len(cooldowns)):
            if cooldowns[i] < 1.0:
                if self._cooldown_imgs[i] is None:
                    self._cooldown_imgs[i] = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2)
                cd_x = x + 87 * 2 + 40 * 2 * i
                cd_y = y + 19 * 2
                cd_img = spriteref.get_cooldown_img(cooldowns[i])
                self._cooldown_imgs[i] = self._cooldown_imgs[i].update(new_model=cd_img, new_x=cd_x, new_y=cd_y)

        if self._potion_text is None:
            pot_img = TextImage(0, 0, str(self._num_potions), spriteref.UI_0_LAYER)
            pot_x = x + 155*2 - pot_img.size()[0] - 4
            pot_y = y + 47*2 - pot_img.size()[1] - 4
            pot_color = (1, 1, 1) if self._num_potions > 0 else (1, 0.5, 0.5)
            self._potion_text = pot_img.update(new_x=pot_x, new_y=pot_y, new_color=pot_color)

    def update(self, world, gs, input_state, render_eng):
        p_state = gs.player_state()
        new_dmg, new_healing = p_state.damage_and_healing_last_tick()

        if len(self._floating_bars) > 0:
            new_bars = []
            for fb in self._floating_bars:
                if fb[1] >= self._float_dur:
                    render_eng.remove(fb[0])
                else:
                    new_bars.append([fb[0], fb[1] + 1])
            self._floating_bars = new_bars

        cooldowns = [p_state.get_cooldown_progress(i) for i in range(0, 6)]
        for i in range(0, 6):
            if cooldowns[i] == 1.0 and self._cooldown_imgs[i] is not None:
                render_eng.remove(self._cooldown_imgs[i])
                self._cooldown_imgs[i] = None

        n_potions = p_state.num_potions()

        if n_potions != self._num_potions:
            self._num_potions = n_potions
            if self._potion_text is not None:
                for bun in self._potion_text.all_bundles():
                    render_eng.remove(bun)
                self._potion_text = None

        self.update_images(gs, p_state.hp(), p_state.max_hp(), new_dmg, new_healing, cooldowns)

        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        if self._bar_img is not None:
            yield self._bar_img
        if self._top_img is not None:
            yield self._top_img
        for floating_bar in self._floating_bars:
            yield floating_bar[0]
        if self._potion_text is not None:
            for bun in self._potion_text.all_bundles():
                yield bun
        for cd_img in self._cooldown_imgs:
            if cd_img is not None:
                yield cd_img


class TextImage:

    X_KERNING = 1
    Y_KERNING = 1

    def __init__(self, x, y, text, layer, try_split=True, color=(1, 1, 1), scale=2, center_w=None):
        self.x = x
        self.center_w = center_w
        self.y = y
        self.text = text.lower()
        self.layer = layer
        self.color = color
        self.scale = scale
        self._letter_images = []

        self._text_chunks = spriteref.split_text(self.text) if try_split else list(self.text)

        #if try_split and max(map(lambda _x: len(_x), self._text_chunks)) == 1:
        #    print("couldn't split: {}".format(self.text))

        self._build_images()

        self.actual_size = self._recalc_size()

    def _recalc_size(self):
        x_range = [None, None]
        y_range = [None, None]
        for img in self.all_bundles():
            x_range[0] = img.x() if x_range[0] is None else min(x_range[0], img.x())
            x_range[1] = img.x() + img.width() if x_range[1] is None else max(x_range[0], img.x() + img.width())
            y_range[0] = img.y() if y_range[0] is None else min(y_range[0], img.y())
            y_range[1] = img.y() + img.height() if y_range[1] is None else max(y_range[1], img.y() + img.height())
        return (x_range[1] - x_range[0], y_range[1] - y_range[0])

    def _calc_width(self):
        max_line_w = 0
        cur_line_w = 0
        char_w = (spriteref.alphabet["a"].width() + TextImage.X_KERNING) * self.scale
        for c in self.text:
            if c == "\n":
                cur_line_w = 0
            else:
                cur_line_w += char_w
                max_line_w = max(max_line_w, cur_line_w)
        return max_line_w

    def size(self):
        return self.actual_size

    def line_height(self):
        return (spriteref.alphabet["a"].height() + TextImage.Y_KERNING) * self.scale

    def _build_images(self):
        ypos = TextImage.Y_KERNING

        if self.center_w is not None:
            true_width = self._calc_width()
            x_shift = self.x + self.center_w // 2 - true_width // 2
        else:
            x_shift = TextImage.X_KERNING

        xpos = x_shift

        a_sprite = spriteref.alphabet["a"]
        for chunk in self._text_chunks:
            if chunk == " ":
                xpos += (TextImage.X_KERNING + a_sprite.width()) * self.scale
            elif chunk == "\n":
                xpos = x_shift
                ypos += (TextImage.Y_KERNING + a_sprite.height()) * self.scale
            else:
                if len(chunk) == 1:
                    sprite = spriteref.alphabet[chunk]
                else:
                    sprite = spriteref.cached_text_imgs[chunk]

                img = ImageBundle(sprite, self.x + xpos, self.y + ypos, layer=self.layer,
                        scale=self.scale, color=self.color)
                self._letter_images.append(img)
                xpos += (TextImage.X_KERNING + sprite.width()) * self.scale

    def update(self, new_x=None, new_y=None, new_depth=None, new_color=None):
        dx = 0 if new_x is None else new_x - self.x
        dy = 0 if new_y is None else new_y - self.y
        new_imgs = []
        for letter in self._letter_images:
            letter_new_x = letter.x() + dx
            letter_new_y = letter.y() + dy
            new_imgs.append(letter.update(new_x=letter_new_x, new_y=letter_new_y,
                                          new_depth=new_depth, new_color=new_color))

        self._letter_images = new_imgs
        self.x = new_x if new_x is not None else self.x
        self.y = new_y if new_y is not None else self.y
        self.color = new_color if new_color is not None else self.color
        self.actual_size = self._recalc_size()

        return self

    def all_bundles(self):
        for b in self._letter_images:
            if b is not None:
                yield b


class ItemImage:

    def __init__(self, x, y, item, layer, scale):
        self.x = x
        self.y = y
        self.item = item
        self.scale = scale
        self._cube_images = []
        self.layer = layer

        self._build_images()

    def _build_images(self):
        for cube in self.item.cubes:
            art = 0 if cube not in self.item.cube_art else self.item.cube_art[cube]
            sprite = spriteref.item_piece_bigs[art]
            xpos = self.x + sprite.width()*self.scale*cube[0]
            ypos = self.y + sprite.height()*self.scale*cube[1]
            img = ImageBundle(sprite, xpos, ypos, layer=self.layer, scale=self.scale, color=self.item.color)
            self._cube_images.append(img)

    def all_bundles(self):
        for b in self._cube_images:
            yield b

    @staticmethod
    def calc_size(item, scale):
        sprite = spriteref.item_piece_bigs[0]
        return (scale*sprite.width()*item.w(), scale*sprite.height()*item.h())