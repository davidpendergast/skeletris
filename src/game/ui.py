from src.items.itemrendering import ItemInfoPane
from src.items.itemrendering import ItemImage
from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.entities import ItemEntity
from src.items.itemrendering import TextImage
import src.items.item as item_module
from src.items.item import StatType
from src.utils.util import Utils
from src.game.inventory import InventoryState, PlayerStatType

        
        
class ItemGridImage:
    def __init__(self, x, y, scale, grid):
        self.x = x
        self.y = y
        self.grid = grid
        self.scale = scale
        
        self.item_images = []
        
        self._build_images()
        
    def _build_images(self):
        cellsize = spriteref.item_piece_bigs[0].size()
        for item in self.grid.all_items():
            pos = self.grid.get_pos(item)
            x_pos = self.x + pos[0] * cellsize[0] * self.scale
            y_pos = self.y + pos[1] * cellsize[1] * self.scale
            self.item_images.append(ItemImage(x_pos, y_pos, item, self.scale))
        
    def all_bundles(self):
        for item_img in self.item_images:
            for bun in item_img.all_bundles():
                yield bun   
        

class InventoryPanel:
    def __init__(self, player_state):
        self.player_state = player_state
        self.state = self.player_state.inventory()
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
        self.top_img = ImageBundle(spriteref.inv_panel_top, 0, 0, scale=sc)
        for i in range(0, self.state.rows - 1):
            y = (128 + i*16)*sc
            self.mid_imgs.append(ImageBundle(spriteref.inv_panel_mid, 0, y, scale=sc))
        y = (128 + self.state.rows*16 - 16)*sc
        self.bot_img = ImageBundle(spriteref.inv_panel_bot, 0, y, scale=sc) 
        
        self.title_text = TextImage(8*sc, 8*sc, "Inventory", scale=int(sc*3/2))
        
        name_str = self.player_state.name()
        lvl_str = self.player_state.level()
        info_txt = "{}\n\nLVL: {}\nROOM:8\nKILL:405".format(name_str, lvl_str)
        i_xy = [self.info_rect[0], self.info_rect[1]]
        self.info_text = TextImage(*i_xy, info_txt, scale=sc)
        
        s_xy = [self.stats_rect[0], self.stats_rect[1]]
        att_str = "ATT:{}".format(self.player_state.stat_value(StatType.ATT))
        self.att_text = TextImage(*s_xy, att_str, scale=sc, 
                color=item_module.STAT_COLORS[item_module.StatType.ATT])
        s_xy[1] += self.att_text.line_height()
        
        def_str = "DEF:{}".format(self.player_state.stat_value(StatType.DEF))
        self.def_text = TextImage(*s_xy, def_str, scale=sc, 
                color=item_module.STAT_COLORS[item_module.StatType.DEF])
        s_xy[1] += self.def_text.line_height()
        
        vit_str = "VIT:{}".format(self.player_state.stat_value(StatType.VIT))
        self.vit_text = TextImage(*s_xy, vit_str, scale=sc, 
                color=item_module.STAT_COLORS[item_module.StatType.VIT])
        s_xy[1] += 2 * self.def_text.line_height()
        
        hp_str = "HP: {}".format(self.player_state.stat_value(PlayerStatType.HP))
        self.hp_text = TextImage(*s_xy, hp_str, scale=sc, 
                color=item_module.STAT_COLORS[None])
        s_xy[1] += self.hp_text.line_height()
        
        dps_str = "DPS:{}".format(self.player_state.stat_value(PlayerStatType.DPS))
        self.dps_text = TextImage(*s_xy, dps_str, scale=sc, 
                color=item_module.STAT_COLORS[None])
        
        e_xy = (self.equip_grid_rect[0], self.equip_grid_rect[1])
        self.equip_img = ItemGridImage(*e_xy, sc, self.state.equip_grid)
        
        inv_xy = (self.inv_grid_rect[0], self.inv_grid_rect[1])
        self.inv_img = ItemGridImage(*inv_xy, sc, self.state.inv_grid)
        
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
            
            
class UiState:

    def __init__(self):
        self.item_panel = None
        self.inventory_panel = None
        
        self.item_on_cursor = None
        self.item_on_cursor_offs = [0, 0]
        self.item_on_cursor_image = None
        
    def _destroy_panel(self, panel, layer_id, render_eng):
        if panel is not None:
            bundles = panel.all_bundles()
            render_eng.clear_bundles(bundles, layer_id)
            
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
           
        if input_state.mouse_in_window() and self.item_on_cursor is None: 
            screen_pos = input_state.mouse_pos()
            
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
                self._destroy_panel(self.item_panel, gs.UI_TOOLTIP_LAYER, render_eng)
                self.item_panel = None
                
            if self.item_panel is None:
                self.item_panel = ItemInfoPane(item_to_display)
                for bun in self.item_panel.all_bundles():
                    render_eng.update(bun, layer_id = gs.UI_TOOLTIP_LAYER)
            
            offs = (-screen_pos[0], -screen_pos[1])
            render_eng.set_layer_offset(gs.UI_TOOLTIP_LAYER, *offs)
            should_destroy = False            
        
        if should_destroy and self.item_panel is not None:
            self._destroy_panel(self.item_panel, gs.UI_TOOLTIP_LAYER, render_eng)
            self.item_panel = None
            
    def _update_inventory_panel(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.INVENTORY):
            if self.inventory_panel is None: 
                self.rebuild_inventory(gs, render_eng)
            else:
                self._destroy_panel(self.inventory_panel, gs.UI_0_LAYER, render_eng)
                self.inventory_panel = None
    
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
                    
            else: # we clicked in world
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
                        p_center = p.center() # drop position
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
            self._destroy_panel(self.item_on_cursor_image, gs.UI_TOOLTIP_LAYER, render_eng)
            self.item_on_cursor_image = None
        
        if create_image:
            size = ItemImage.calc_size(self.item_on_cursor, 2)
            self.item_on_cursor_image = ItemImage(0, 0, self.item_on_cursor, 2)
            self.item_on_cursor_offs = (-size[0] // 2, -size[1] // 2)
            for bun in self.item_on_cursor_image.all_bundles():
                render_eng.update(bun, gs.UI_TOOLTIP_LAYER)
                
        if rebuild_inventory:
            self.rebuild_inventory(gs, render_eng)
                  
        if self.item_on_cursor_image is not None:
            screen_pos = input_state.mouse_pos()
            if screen_pos is not None:
                x_offs = -screen_pos[0] - self.item_on_cursor_offs[0]
                y_offs = -screen_pos[1] - self.item_on_cursor_offs[1]
                render_eng.set_layer_offset(gs.UI_TOOLTIP_LAYER, x_offs, y_offs)
     
    def rebuild_inventory(self, gs, render_eng):                
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                render_eng.remove(bun, layer_id=gs.UI_0_LAYER)
                
        self.inventory_panel = InventoryPanel(gs.player_state())
        for bun in self.inventory_panel.all_bundles():
            render_eng.update(bun, layer_id=gs.UI_0_LAYER)      
        
    
    def update(self, world, gs, input_state, render_eng):
        ## TODO - need to better organize this mess
        self._update_item_on_cursor(world, gs, input_state, render_eng)
        self._update_item_panel(world, gs, input_state, render_eng)
        self._update_inventory_panel(world, gs, input_state, render_eng)
        
        
        
        
        
        
