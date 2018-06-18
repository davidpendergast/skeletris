import pygame

import src.game.spriteref as spriteref
from src.game.globalstate import GlobalState
from src.game.inputs import InputState
from src.game.ui import UiState

from src.world.worldstate import World
from src.world.entities import Player, Enemy, ChestEntity
import src.renderengine.img as img
from src.renderengine.engine import RenderEngine

from src.items.item import ItemFactory
from src.items.itemrendering import TextImage, ItemImage, ItemInfoPane

print("launching Cubelike...")
print("running pygame version: " + pygame.version.ver)


SCREEN_SIZE = (800, 600)

def build_me_a_world(width, height, render_eng, gs):
    import random
    w = World(width, height)
    for x in range(0, width):
        for y in range(0, height):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                w.set_geo(x, y, World.WALL)    
            elif x < 3 and y < 3:
                w.set_geo(x, y, World.FLOOR)
            else:
                if random.random() < 0.33:
                    w.set_geo(x, y, World.WALL)
                else:
                    w.set_geo(x, y, World.FLOOR)
                    if random.random() < 0.05:
                        i = int(random.random() * len(spriteref.enemies_all))
                        e = Enemy(0, 0, spriteref.enemies_all[i])
                        w.add(e, gridcell=(x, y))
                    elif random.random() < 0.05:
                        w.add(ChestEntity(0, 0), gridcell=(x, y))
    
    render_eng.clear_all_sprites()
                        
    for bun in w.get_all_bundles(World.WALL):
        render_eng.update(bun, layer_id=gs.WALL_LAYER)
        
    for bun in w.get_all_bundles(World.FLOOR):
        render_eng.update(bun, layer_id=gs.FLOOR_LAYER)
        
    player = Player(80, 80)
    w.add(player)
    
    #item = ItemFactory.gen_item()
    #item_panel = ItemInfoPane(item)
    #for b in item_panel.all_bundles():
    #    render_eng.update(b, layer_id=gs.UI_0_LAYER)
    
    return w
   
    
def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode(SCREEN_SIZE, mods)
    
    input_state = InputState()
    gs = GlobalState()
    ui_state = UiState()
    
    render_eng = RenderEngine()
    render_eng.init(*SCREEN_SIZE)
    
    COLOR = True
    SORTS = True
    render_eng.add_layer(
            gs.FLOOR_LAYER, 
            "floors", 0, 
            False, False)
    render_eng.add_layer(
            gs.SHADOW_LAYER, 
            "shadow_layer", 5, 
            False, False)
    render_eng.add_layer(
            gs.WALL_LAYER, 
            "walls", 10, 
            False, False)
    render_eng.add_layer(
            gs.ENTITY_LAYER, 
            "entities", 15, 
            SORTS, COLOR)
    render_eng.add_layer(
            gs.UI_0_LAYER, 
            "ui_0", 20, 
            False, COLOR)
    render_eng.add_layer(
            gs.UI_TOOLTIP_LAYER, 
            "ui_tooltips", 25, 
            False, COLOR)
    
    raw_sheet = pygame.image.load("assets/image.png")
    img_surface = spriteref.build_spritesheet(raw_sheet)
    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)
        
    world = build_me_a_world(1, 1, render_eng, gs)
        
    clock = pygame.time.Clock()    
    
    running = True
    
    while running:
        gs.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
            elif event.type == pygame.KEYDOWN:
                input_state.set_key(event.key, True)
            elif event.type == pygame.KEYUP:
                input_state.set_key(event.key, False)
            elif event.type == pygame.MOUSEMOTION:
                input_state.set_mouse_pos(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                input_state.set_mouse_down(True)
            elif event.type == pygame.MOUSEBUTTONUP:
                input_state.set_mouse_down(False)

            if not pygame.mouse.get_focused():
                input_state.set_mouse_pos(None)
        input_state.update(gs)
                
        if input_state.was_pressed(pygame.K_RETURN):
            world = build_me_a_world(7, 7, render_eng, gs)
        
        world.update_all(gs, input_state, render_eng)
        
        ui_state.update(world, gs, input_state, render_eng)
        
        camera = gs.get_world_camera()
        for layer_id in gs.world_layers:
            render_eng.set_layer_offset(layer_id, *camera)
        
        render_eng.render_layers()
        pygame.display.flip()
        clock.tick(60)
        if gs.tick_counter % 60 == 0:
            if clock.get_fps() < 59:
                print("fps: {}".format(clock.get_fps()))

                
if __name__ == "__main__":
    run()
        
    
