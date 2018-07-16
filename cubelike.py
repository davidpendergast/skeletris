import pygame

import src.game.spriteref as spriteref
from src.utils.util import Utils
from src.game.globalstate import GlobalState
import src.game.inputs as inputs
from src.ui.menus import MenuManager
from src.game.inventory import InventoryState
from src.game.actorstate import PlayerState
from src.renderengine.engine import RenderEngine

from src.worldgen.worldgen import WorldFactory

import src.utils.profiling as profiling


print("launching Cubelike...")
print("running pygame version: " + pygame.version.ver)


SCREEN_SIZE = (800, 600)


def build_me_a_world(level):
    w = WorldFactory.gen_world_from_rooms(level, num_rooms=25).build_world()
    # w = WorldFactory.gen_test_world(5).build_world()

    w.hide_all_floors()

    p = w.get_player()
    if p is not None:
        grid_xy = w.to_grid_coords(*p.center())
        w.set_hidden(*grid_xy, False, and_fill_adj_floors=True)

    return w


def new_gs(menu_id):
    gs = GlobalState(menu_id=menu_id)
    gs.set_player_state(PlayerState("ghast", InventoryState()))
    return gs


def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    
    pygame.display.set_caption("Cubelike")
    
    pygame.display.set_mode(SCREEN_SIZE, mods)
    
    input_state = inputs.InputState()
    gs = None
    
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
            False, COLOR)
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

    img_path = Utils.resource_path("assets/image.png")
    raw_sheet = pygame.image.load(img_path)
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

        if gs is None or gs._needs_new_game:
            print("Starting new game")
            menu_id = MenuManager.START_MENU if gs is None else MenuManager.IN_GAME_MENU
            gs = new_gs(menu_id)
            world = None

        gs.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
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

        world_active = gs.get_menu_manager().should_draw_world()

        if world_active and (world is None or gs._needs_next_level):
            render_eng.clear_all_sprites()
            world = build_me_a_world(gs.dungeon_level)
            gs._needs_next_level = False

        if input_state.was_pressed(pygame.K_RETURN):
            gs.next_level()

        if input_state.was_pressed(pygame.K_ESCAPE) or gs.needs_exit:
            running = False
            continue

        if input_state.was_pressed(pygame.K_F1):
            # used to help find performance bottlenecks
            profiling.get_instance().toggle()

        if input_state.was_pressed(pygame.K_F4):
            size = gs.screen_size
            if gs.is_fullscreen:
                pygame.display.set_mode(size, pygame.OPENGL)
            else:
                pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.OPENGL)
            gs.is_fullscreen = not gs.is_fullscreen

        if input_state.was_pressed(inputs.KILL):
            manager = gs.get_menu_manager()
            if manager.get_active_menu().get_type() == MenuManager.IN_GAME_MENU:
                gs.get_menu_manager().set_active_menu(MenuManager.DEATH_MENU)

        if world_active:
            player = world.get_player()
            gs.player_state().update(player, world, gs, input_state)

            world.update_all(gs, input_state, render_eng)

            camera = gs.get_world_camera()
            for layer_id in spriteref.WORLD_LAYERS:
                render_eng.set_layer_offset(layer_id, *camera)

        elif world is not None:
            world.cleanup_active_bundles(render_eng)

        gs.get_menu_manager().update(world, gs, input_state, render_eng)

        render_eng.render_layers()

        pygame.display.flip()
        clock.tick(60)
        if gs.tick_counter % 60 == 0:
            if clock.get_fps() < 59:
                print("fps: {} ({} sprites)".format(round(clock.get_fps()*10) / 10.0, render_eng.count_sprites()))

    pygame.quit()

                
if __name__ == "__main__":
    run()
