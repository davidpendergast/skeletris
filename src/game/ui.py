import random

import src.game.stats
from src.items.itemrendering import ItemInfoPane
from src.items.itemrendering import ItemImage
from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.entities import ItemEntity
from src.items.itemrendering import TextImage
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

    def __init__(self, player_state):
        self.player_state = player_state
        self.state = self.player_state.inventory()
        self.layer = spriteref.UI_0_LAYER

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
        
        self._build_images(sc)
        
    def _build_images(self, sc):
        self.top_img = ImageBundle(spriteref.inv_panel_top, 0, 0, layer=self.layer, scale=sc)
        for i in range(0, self.state.rows - 1):
            y = (128 + i*16)*sc
            self.mid_imgs.append(ImageBundle(spriteref.inv_panel_mid, 0, y, layer=self.layer, scale=sc))
        y = (128 + self.state.rows*16 - 16)*sc
        self.bot_img = ImageBundle(spriteref.inv_panel_bot, 0, y, layer=self.layer, scale=sc)
        
        self.title_text = TextImage(8*sc, 8*sc, "Inventory", self.layer, scale=int(sc*3/2))
        
        name_str = self.player_state.name()
        lvl_str = self.player_state.level()
        info_txt = "{}\n\nLVL: {}\nROOM:8\nKILL:405".format(name_str, lvl_str)
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
        self._float_dur = 30
        self._float_height = 30
        self._bar_color = (1.0, 0.5, 0.5)

    def update_images(self, gs, cur_hp, max_hp, new_damage, new_healing):
        if self._top_img is None:
            self._top_img = ImageBundle(spriteref.health_bar_top, 0, 0,
                                        layer=spriteref.UI_0_LAYER, scale=2)
        if self._bar_img is None:
            self._bar_img = ImageBundle.new_bundle(layer_id=spriteref.UI_0_LAYER, scale=2)
            self._bar_img = self._bar_img.update(new_color=self._bar_color)

        hp_pcnt_full = Utils.bound(cur_hp / max_hp, 0.0, 1.0)
        x = gs.screen_size[0] // 2 - self._top_img.width() // 2
        w = self._top_img.width()
        y = gs.screen_size[1] - self._top_img.height()

        if new_damage > 0:
            pcnt_full = Utils.bound(new_damage / max_hp, 0.0, 1.0)
            dmg_x = int(x + hp_pcnt_full * w)
            dmg_sprite = spriteref.get_health_bar(pcnt_full)
            dmg_img = ImageBundle(dmg_sprite, dmg_x, 0, layer=spriteref.UI_0_LAYER, scale=2)
            self._floating_bars.append([dmg_img, 0])

        for i in range(0, len(self._floating_bars)):
            img, cur_dur = self._floating_bars[i]
            prog = Utils.bound(cur_dur / self._float_dur, 0.0, 1.0)
            h_offs = int(self._float_height * prog)
            g = self._bar_color[1] * (1 - prog)
            b = self._bar_color[2] * (1 - prog)

            self._floating_bars[i][0] = img.update(new_y=(y - h_offs), new_color=(1.0, g, b))

        self._top_img = self._top_img.update(new_x=x, new_y=y)
        bar_sprite = spriteref.get_health_bar(hp_pcnt_full)

        self._bar_img = self._bar_img.update(new_model=bar_sprite, new_x=x, new_y=y)

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

        self.update_images(gs, p_state.hp(), p_state.max_hp(), new_dmg, new_healing)

        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        if self._bar_img is not None:
            yield self._bar_img
        if self._top_img is not None:
            yield self._top_img
        for floating_bar in self._floating_bars:
            yield floating_bar[0]


class MenuManager:

    DEATH_MENU = 0
    IN_GAME_MENU = 1
    START_MENU = 2

    def __init__(self, menu_id):
        self._active_menu = self._get_menu(menu_id)
        self._next_active_menu_id = menu_id

    def update(self, world, gs, input_state, render_eng):
        if self._next_active_menu_id is not None:
            for bun in self._active_menu.all_bundles():
                render_eng.remove(bun)

            self._active_menu.cleanup()

            self._active_menu = self._get_menu(self._next_active_menu_id)
            self._next_active_menu_id = None
            render_eng.set_clear_color(*self._active_menu.get_clear_color())

        menu = self.get_active_menu()
        menu.update(world, gs, input_state, render_eng)

    def _get_menu(self, menu_id):
        if menu_id == MenuManager.DEATH_MENU:
            return DeathMenu()
        elif menu_id == MenuManager.IN_GAME_MENU:
            return InGameUiState()
        raise ValueError("Unknown menu id: " + str(menu_id))

    def should_draw_world(self):
        return self._active_menu.keep_drawing_world_underneath()

    def get_active_menu(self):
        return self._active_menu

    def set_active_menu(self, menu_id):
        if menu_id is None:
            raise ValueError("Can't set null menu")
        self._next_active_menu_id = menu_id


class Menu:

    def __init__(self, menu_type):
        self._menu_type = menu_type

    def get_clear_color(self):
        return (0.5, 0.5, 0.5)

    def get_type(self):
        return self._menu_type

    def update(self, world, gs, input_state, render_eng):
        state = gs.get_in_game_ui_state()
        state.update(world, gs, input_state, render_eng)

    def all_bundles(self):
        return []

    def cleanup(self):
        pass

    def keep_drawing_world_underneath(self):
        return False

            
class InGameUiState(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.IN_GAME_MENU)
        self.item_panel = None
        self.inventory_panel = None
        self.health_bar_panel = None
        
        self.item_on_cursor = None
        self.item_on_cursor_offs = [0, 0]
        self.item_on_cursor_image = None

    def keep_drawing_world_underneath(self):
        return True
        
    def _destroy_panel(self, panel, render_eng):
        if panel is not None:
            bundles = panel.all_bundles()
            render_eng.clear_bundles(bundles)
            
    def _get_item_entity_at_world_coords(self, world, world_pos):
        hover_rad = 24
        hover_over = world.entities_in_circle(world_pos, hover_rad)
        hover_items = list(filter(lambda x: x.is_item(), hover_over))
        if len(hover_items) > 0:
            return hover_items[0]
        else:
            return None
        
    def _update_item_panel(self, world, gs, input_state, render_eng):
        should_destroy = True
        item_to_display = None
        screen_pos = input_state.mouse_pos()

        if input_state.mouse_in_window() and self.item_on_cursor is None:

            if self.in_inventory_panel(screen_pos):
                grid_n_cell = self.get_clicked_inventory_grid_and_cell(screen_pos)
                if grid_n_cell is not None:
                    grid, cell = grid_n_cell
                    item_to_display = grid.item_at_position(cell)
            else:   
                world_pos = gs.screen_to_world_coords(screen_pos)
                item_entity = self._get_item_entity_at_world_coords(world, world_pos)
                if item_entity is not None:
                    item_to_display = item_entity.get_item()
                    
        if item_to_display is not None:
            if self.item_panel is not None and self.item_panel.item is not item_to_display:
                self._destroy_panel(self.item_panel, render_eng)
                self.item_panel = None
                
            if self.item_panel is None:
                self.item_panel = ItemInfoPane(item_to_display)
                for bun in self.item_panel.all_bundles():
                    render_eng.update(bun)

            offs = (-screen_pos[0], -screen_pos[1])
            render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, *offs)
            should_destroy = False            
        
        if should_destroy and self.item_panel is not None:
            self._destroy_panel(self.item_panel, render_eng)
            self.item_panel = None
            
    def _update_inventory_panel(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.INVENTORY):
            if self.inventory_panel is None: 
                self.rebuild_inventory(gs, render_eng)
            else:
                self._destroy_panel(self.inventory_panel, render_eng)
                self.inventory_panel = None

    def _update_health_bar_panel(self, world, gs, input_state, render_eng):
        if self.health_bar_panel is None:
            self.health_bar_panel = HealthBarPanel()
        self.health_bar_panel.update(world, gs, input_state, render_eng)
    
    def in_inventory_panel(self, screen_pos):
        if self.inventory_panel is None:
            return False
        else:
            return Utils.rect_contains(self.inventory_panel.total_rect, screen_pos)
            
    def get_clicked_inventory_grid_and_cell(self, screen_pos):
        pos_in_panel = (screen_pos[0] - self.inventory_panel.total_rect[0],
                screen_pos[1] - self.inventory_panel.total_rect[1])
        
        eq_rect = self.inventory_panel.equip_grid_rect
        if Utils.rect_contains(eq_rect, pos_in_panel):
            grid = self.inventory_panel.state.equip_grid
            x = int((pos_in_panel[0] - eq_rect[0])/eq_rect[2]*grid.size[0])
            y = int((pos_in_panel[1] - eq_rect[1])/eq_rect[3]*grid.size[1])
            return (grid, (x, y))
        
        inv_rect = self.inventory_panel.inv_grid_rect
        if Utils.rect_contains(inv_rect, pos_in_panel):
            grid = self.inventory_panel.state.inv_grid
            x = int((pos_in_panel[0] - inv_rect[0])/inv_rect[2]*grid.size[0])
            y = int((pos_in_panel[1] - inv_rect[1])/inv_rect[3]*grid.size[1])
            return (grid, (x, y))
        
        return None
                
    def _update_item_on_cursor(self, world, gs, input_state, render_eng):
        destroy_image = False
        create_image = False
        rebuild_inventory = False
        
        if not input_state.mouse_in_window():
            destroy_image = True
        elif self.item_on_cursor is not None and self.item_on_cursor_image is None:
            # mouse left window and came back
            create_image = True
            
        elif input_state.mouse_was_pressed():
            screen_pos = input_state.mouse_pos()
            
            if self.in_inventory_panel(screen_pos):
                if self.item_on_cursor is not None:
                    # when holding an item, gotta offset the click to the top left corner
                    grid_click_pos = Utils.add(screen_pos, self.item_on_cursor_offs)
                    grid_click_pos = Utils.add(grid_click_pos, (16, 16)) # plus some fudge XXX
                else:
                    grid_click_pos = screen_pos    
                    
                clicked_grid_n_cell = self.get_clicked_inventory_grid_and_cell(grid_click_pos)
                if clicked_grid_n_cell is not None:
                    grid = clicked_grid_n_cell[0]
                    cell = clicked_grid_n_cell[1]
                    if self.item_on_cursor is not None:
                        if grid.can_place(self.item_on_cursor, cell):
                            grid.place(self.item_on_cursor, cell)
                            self.item_on_cursor = None
                            destroy_image = True
                            rebuild_inventory = True
                        else:
                            replaced_with = grid.try_to_replace(self.item_on_cursor, cell)
                            if replaced_with is not None:
                                self.item_on_cursor = replaced_with
                                destroy_image = True
                                create_image = True
                                rebuild_inventory = True
                    else:
                        clicked_item = grid.item_at_position(cell)
                        if clicked_item is not None:
                            grid.remove(clicked_item)
                            self.item_on_cursor = clicked_item
                            create_image = True
                            rebuild_inventory = True
                    
            else:  # we clicked in world
                world_pos = gs.screen_to_world_coords(screen_pos)
                if self.item_on_cursor is None:
                    clicked_item = self._get_item_entity_at_world_coords(world, world_pos)
                    if clicked_item is not None:
                        world.remove(clicked_item)
                        self.item_on_cursor = clicked_item.get_item()
                        create_image = True
                else:
                    p = world.get_player()
                    if p is not None:
                        p_center = p.center()  # drop position
                        drop_dir = Utils.sub(world_pos, p_center)
                        vel = ItemEntity.rand_vel(direction=drop_dir)
                        item_entity = ItemEntity(self.item_on_cursor, *p_center, vel=vel)
                        world.add(item_entity)
                        destroy_image = True
                        self.item_on_cursor = None
        
        if input_state.was_pressed(inputs.INTERACT) and self.item_on_cursor is not None:
            self.item_on_cursor = item_module.ItemFactory.rotate_item(self.item_on_cursor) 
            create_image = True
            destroy_image = True
                                     
        if destroy_image:
            self._destroy_panel(self.item_on_cursor_image, render_eng)
            self.item_on_cursor_image = None
        
        if create_image:
            size = ItemImage.calc_size(self.item_on_cursor, 2)
            self.item_on_cursor_image = ItemImage(0, 0, self.item_on_cursor, spriteref.UI_TOOLTIP_LAYER, 2)
            self.item_on_cursor_offs = (-size[0] // 2, -size[1] // 2)
            for bun in self.item_on_cursor_image.all_bundles():
                render_eng.update(bun)
                
        if rebuild_inventory:
            self.rebuild_inventory(gs, render_eng)
                  
        if self.item_on_cursor_image is not None:
            screen_pos = input_state.mouse_pos()
            if screen_pos is not None:
                x_offs = -screen_pos[0] - self.item_on_cursor_offs[0]
                y_offs = -screen_pos[1] - self.item_on_cursor_offs[1]
                render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, x_offs, y_offs)
     
    def rebuild_inventory(self, gs, render_eng):                
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                render_eng.remove(bun)
                
        self.inventory_panel = InventoryPanel(gs.player_state())
        for bun in self.inventory_panel.all_bundles():
            render_eng.update(bun)

    def update(self, world, gs, input_state, render_eng):
        # TODO - need to better organize this mess
        self._update_item_on_cursor(world, gs, input_state, render_eng)
        self._update_item_panel(world, gs, input_state, render_eng)
        self._update_inventory_panel(world, gs, input_state, render_eng)
        self._update_health_bar_panel(world, gs, input_state, render_eng)

        p_state = gs.player_state()
        if p_state.hp() <= 0:
            gs.get_menu_manager().set_active_menu(MenuManager.DEATH_MENU)

    def cleanup(self):
        self.item_on_cursor = None
        self.inventory_panel = None
        self.item_on_cursor_image = None
        self.item_on_cursor = None  # XXX this will DESTROY the item on cursor

    def all_bundles(self):
        if self.health_bar_panel is not None:
            for bun in self.health_bar_panel.all_bundles():
                yield bun
        if self.item_panel is not None:
            for bun in self.item_panel.all_bundles():
                yield bun
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                yield bun
        if self.item_on_cursor_image is not None:
            for bun in self.item_on_cursor_image.all_bundles():
                yield bun


class DeathMenu(Menu):
    RETRY_OPT = 0
    EXIT_OPT = 1

    def __init__(self):
        Menu.__init__(self, MenuManager.DEATH_MENU)
        self._you_died_img = None
        self._flavor_img = None

        self._num_options = 2
        self._option_imgs = [None] * self._num_options
        self._selection = 0

        self._title_pos = (0, 0)
        self._flavor_pos = (0, 0)
        self._option_rects = [(0, 0, 0, 0)] * self._num_options

        self._showing_flavor = True
        self._flavor_duration = 100
        self._flavor_tick = 0
        self._flavor_text = self._get_flavor_text()

        self._build_imgs()

    def get_flavor_progress(self):
        return Utils.bound(self._flavor_tick / self._flavor_duration, 0.0, 1.0)

    def get_clear_color(self):
        return (0.0, 0.0, 0.0)

    ALL_FLAVOR = [
        "from death... comes life?",
        "you'll do better next time!"
    ]

    def _get_flavor_text(self):
        idx = int(random.random() * len(DeathMenu.ALL_FLAVOR))
        return DeathMenu.ALL_FLAVOR[idx]

    def _build_imgs(self):
        if self._you_died_img is None:
            self._you_died_img = TextImage(0, 0, "game over", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=6)
        if self._flavor_img is None:
            self._flavor_img = TextImage(0, 0, self._flavor_text, layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=2)
        if self._option_imgs[0] is None:
            self._option_imgs[0] = TextImage(0, 0, "retry", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)
        if self._option_imgs[1] is None:
            self._option_imgs[1] = TextImage(0, 0, "quit", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)

    def _update_imgs(self):
        if self.get_flavor_progress() < 0.15:
            c = self.get_flavor_progress() / 0.15
            color = (c, c, c)  # fade in
        else:
            color = (1, 1, 1)
        self._flavor_img.update(new_x=self._flavor_pos[0], new_y=self._flavor_pos[1], new_color=color)

        self._you_died_img.update(new_x=self._title_pos[0], new_y=self._title_pos[1])
        for i in range(0, self._num_options):
            color = (1, 0, 0) if self._selection == i else (1, 1, 1)
            x = self._option_rects[i][0]
            y = self._option_rects[i][1]
            self._option_imgs[i].update(new_x=x, new_y=y, new_color=color)

    def update(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.UP):
            self._selection = (self._selection - 1) % self._num_options
        if input_state.was_pressed(inputs.DOWN):
            self._selection = (self._selection + 1) % self._num_options
        if input_state.was_pressed(inputs.ENTER):
            self._handle_enter_press(gs)

        if input_state.mouse_in_window():
            pos = input_state.mouse_pos()
            if input_state.mouse_moved():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._selection = i

            if input_state.mouse_was_pressed():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._handle_enter_press(gs)
                        break

        screensize = gs.screen_size
        flv_size = self._flavor_img.size()
        self._flavor_pos = (screensize[0] // 2 - flv_size[0] // 2,
                            screensize[1] // 2 - flv_size[1] // 2)

        gap = 32
        total_height = self._you_died_img.size()[1]
        for img in self._option_imgs:
            total_height += img.size()[1] + gap

        total_width = self._you_died_img.size()[0]

        x_pos = screensize[0] // 2 - total_width // 2
        y_pos = screensize[1] // 2 - total_height // 2

        self._title_pos = (x_pos, y_pos)
        y_pos += self._you_died_img.size()[1] + gap

        for i in range(0, self._num_options):
            opt_size = self._option_imgs[i].size()
            x_pos = screensize[0] // 2 - opt_size[0] // 2
            self._option_rects[i] = (x_pos, y_pos, opt_size[0], opt_size[1])

            y_pos += opt_size[1] + gap

        self._update_imgs()

        if self._showing_flavor and self.get_flavor_progress() == 1.0:
            self._showing_flavor = False
            for bun in self._flavor_img.all_bundles():
                render_eng.remove(bun)
        elif self._showing_flavor:
            self._flavor_tick += 1

        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        if self._showing_flavor:
            if self._flavor_img is not None:
                for bun in self._flavor_img.all_bundles():
                    yield bun
        else:
            if self._you_died_img is not None:
                for bun in self._you_died_img.all_bundles():
                    yield bun
            for opt_img in self._option_imgs:
                if opt_img is not None:
                    for bun in opt_img.all_bundles():
                        yield bun

    def _handle_enter_press(self, gs):
        if self.get_flavor_progress() < 1:
            self._flavor_tick = self._flavor_duration
        else:
            sel = self._selection
            print("sel = {}".format(sel))
            if sel == DeathMenu.RETRY_OPT:
                gs.new_game()
            elif sel == DeathMenu.EXIT_OPT:
                gs.new_game()

