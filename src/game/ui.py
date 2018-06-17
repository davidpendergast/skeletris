from src.items.itemrendering import ItemInfoPane


class UiState:

    def __init__(self):
        self.item_panel = None
        
    def _destroy_panel(self, gs, render_eng):
        if self.item_panel is not None:
            bundles = self.item_panel.all_bundles()
            render_eng.clear_bundles(bundles, gs.UI_TOOLTIP_LAYER)
            self.item_panel = None
        
    def _update_item_panel(self, world, gs, input_state, render_eng):
        should_destroy = True
        if input_state.mouse_in_window():
            # TODO if pos in inventory  
            screen_pos = input_state.mouse_pos()
            world_pos = gs.screen_to_world_coords(screen_pos)
            hover_rad = 24
            hover_over = world.entities_in_circle(world_pos, hover_rad)
            hover_items = list(filter(lambda x: x.is_item(), hover_over))
            if len(hover_items) > 0:
                closest = hover_items[0].get_item()
                if self.item_panel is not None and self.item_panel.item is not closest:
                    self._destroy_panel(gs, render_eng)
                    
                if self.item_panel is None:
                    self.item_panel = ItemInfoPane(closest)
                    for bun in self.item_panel.all_bundles():
                        render_eng.update(bun, layer_id = gs.UI_TOOLTIP_LAYER)
                    
                render_eng.set_layer_offset(gs.UI_TOOLTIP_LAYER, -screen_pos[0], -screen_pos[1])
                should_destroy = False
                    
        
        if should_destroy and self.item_panel is not None:
            self._destroy_panel(gs, render_eng)
        
    
    def update(self, world, gs, input_state, render_eng):
        self._update_item_panel(world, gs, input_state, render_eng)
