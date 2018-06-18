from src.items.itemrendering import ItemInfoPane
from src.items.itemrendering import ItemImage
from src.renderengine.img import ImageBundle
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.entities import ItemEntity

class InventoryState:
    def __init__(self):
        self.rows = 7

class InventoryPanel:
    def __init__(self, state):
        self.state = state
        self.top_img = None
        self.mid_imgs = []
        self.bot_img = None
        
        self._build_images()
        
    def _build_images(self):
        sc = 2
        self.top_img = ImageBundle(spriteref.inv_panel_top, 0, 0, scale=sc)
        for i in range(0, self.state.rows - 1):
            y = (128 + i*16)*sc
            self.mid_imgs.append(ImageBundle(spriteref.inv_panel_mid, 0, y, scale=sc))
        y = (128 + self.state.rows*16 - 16)*sc
        self.bot_img = ImageBundle(spriteref.inv_panel_bot, 0, y, scale=sc) 
        
    def all_bundles(self):
        yield self.top_img
        for img in self.mid_imgs:
            yield img
        yield self.bot_img

class UiState:

    def __init__(self):
        self.item_panel = None
        self.inventory_panel = None
        
        self.item_on_cursor = None
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
            
        if input_state.mouse_in_window() and self.item_on_cursor is None:
            # TODO if pos in inventory  
            screen_pos = input_state.mouse_pos()
            world_pos = gs.screen_to_world_coords(screen_pos)
            item_entity = self._get_item_entity_at_world_coords(world, world_pos)
            if item_entity is not None:
                closest = item_entity.get_item()
                if self.item_panel is not None and self.item_panel.item is not closest:
                    self._destroy_panel(self.item_panel, gs.UI_TOOLTIP_LAYER, render_eng)
                    self.item_panel = None
                    
                if self.item_panel is None:
                    self.item_panel = ItemInfoPane(closest)
                    for bun in self.item_panel.all_bundles():
                        render_eng.update(bun, layer_id = gs.UI_TOOLTIP_LAYER)
                    
                render_eng.set_layer_offset(gs.UI_TOOLTIP_LAYER, -screen_pos[0], -screen_pos[1])
                should_destroy = False
                    
        
        if should_destroy and self.item_panel is not None:
            self._destroy_panel(self.item_panel, gs.UI_TOOLTIP_LAYER, render_eng)
            self.item_panel = None
            
    def _update_inventory_panel(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.INTERACT):
            if self.inventory_panel == None: 
                self.inventory_panel = InventoryPanel(InventoryState())
                
                for bun in self.inventory_panel.all_bundles():
                    render_eng.update(bun, layer_id=gs.UI_0_LAYER)
            else:
                self._destroy_panel(self.inventory_panel, gs.UI_0_LAYER, render_eng)
                self.inventory_panel = None
    
                
    def _update_item_on_cursor(self, world, gs, input_state, render_eng):
        destroy_image = False
        create_image = False
        
        if not input_state.mouse_in_window():
            destroy_image = True
        elif self.item_on_cursor is not None and self.item_on_cursor_image is None:
            # mouse left window and came back
            create_image = True
            
        elif input_state.mouse_was_pressed():
            print("mouse clicked")
            screen_pos = input_state.mouse_pos()
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
                    item_entity = ItemEntity(self.item_on_cursor, *p_center)
                    world.add(item_entity)
                    destroy_image = True
                    self.item_on_cursor = None
                    
                                     
        if destroy_image:
            self._destroy_panel(self.item_on_cursor_image, gs.UI_TOOLTIP_LAYER, render_eng)
            self.item_on_cursor_image = None
        
        elif create_image:
            self.item_on_cursor_image = ItemImage(0, 0, self.item_on_cursor, 2)
            for bun in self.item_on_cursor_image.all_bundles():
                render_eng.update(bun, gs.UI_TOOLTIP_LAYER)
            
        if self.item_on_cursor_image is not None:
            screen_pos = input_state.mouse_pos()
            if screen_pos is not None:
                render_eng.set_layer_offset(gs.UI_TOOLTIP_LAYER, -screen_pos[0], -screen_pos[1])
                    
            
        
    
    def update(self, world, gs, input_state, render_eng):
        self._update_item_on_cursor(world, gs, input_state, render_eng)
        self._update_item_panel(world, gs, input_state, render_eng)
        self._update_inventory_panel(world, gs, input_state, render_eng)
