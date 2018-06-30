import pygame

import src.game.spriteref as spriteref
from src.game.globalstate import GlobalState
from src.game.inputs import InputState
from src.game.ui import UiState
from src.game.inventory import PlayerState, InventoryState
from src.game.enemies import EnemyFactory

from src.world.worldstate import World
from src.world.entities import Player, ChestEntity, DoorEntity
from src.renderengine.engine import RenderEngine

from src.worldgen.worldgen import WorldFactory

import src.utils.profiling as profiling


print("launching Cubelike...")
print("running pygame version: " + pygame.version.ver)


SCREEN_SIZE = (800, 600)


def build_me_a_world():
    w = WorldFactory.gen_world_from_rooms(num_rooms=25).build_world()
    # w = WorldFactory.gen_test_world(5).build_world()

    w.hide_all_floors()

    p = w.get_player()
    print("p = ", p)
    if p is not None:
        grid_xy = w.to_grid_coords(*p.center())
        print("setting hidden to false at {}".format(grid_xy))
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)

    return w
   
    
def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    
    pygame.display.set_caption("Cubelike")
    
    screen = pygame.display.set_mode(SCREEN_SIZE, mods)
    
    input_state = InputState()
    gs = GlobalState()
    gs.set_player_state(PlayerState("ghast", InventoryState()))
    ui_state = UiState()
    
    render_eng = RenderEngine()
    render_eng.init(*SCREEN_SIZE)
    
    COLOR = True
    SORTS = True
    render_eng.add_layer(
            spriteref.FLOOR_LAYER,
            "floors", 0, 
            False, False)
    render_eng.add_layer(
            spriteref.SHADOW_LAYER,
            "shadow_layer", 5, 
            False, False)
    render_eng.add_layer(
            spriteref.WALL_LAYER,
            "walls", 10, 
            False, False)
    render_eng.add_layer(
            spriteref.ENTITY_LAYER,
            "entities", 15, 
            SORTS, COLOR)
    render_eng.add_layer(
            spriteref.UI_0_LAYER,
            "ui_0", 20, 
            False, COLOR)
    render_eng.add_layer(
            spriteref.UI_TOOLTIP_LAYER,
            "ui_tooltips", 25,
            False, COLOR)
    
    raw_sheet = pygame.image.load("assets/image.png")
    img_surface = spriteref.build_spritesheet(raw_sheet)
    
    window_icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    window_icon.blit(img_surface, (0, 0), spriteref.chest_closed.rect())
    pygame.display.set_icon(window_icon)
    
    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)
        
    world = None
        
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
                
        if world is None or gs._needs_next_level or input_state.was_pressed(pygame.K_RETURN):
            render_eng.clear_all_sprites()
            world = build_me_a_world()
            gs._needs_next_level = False

        if input_state.was_pressed(pygame.K_F1):
            # used to help find performance bottlenecks
            profiling.get_instance().toggle()
        
        player = world.get_player()
        gs.player_state().update(player, world, gs, input_state)
        
        world.update_all(gs, input_state, render_eng)
        
        ui_state.update(world, gs, input_state, render_eng)
        
        camera = gs.get_world_camera()
        for layer_id in spriteref.WORLD_LAYERS:
            render_eng.set_layer_offset(layer_id, *camera)
        
        render_eng.render_layers()
        pygame.display.flip()
        clock.tick(60)
        if gs.tick_counter % 60 == 0:
            if clock.get_fps() < 59:
                print("fps: {} ({} sprites)".format(round(clock.get_fps()*10) / 10.0, render_eng.count_sprites()))

                
if __name__ == "__main__":
    run()
