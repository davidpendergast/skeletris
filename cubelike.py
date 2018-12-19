import pygame

import src.game.spriteref as spriteref
from src.utils.util import Utils
from src.game.globalstate import GlobalState, SaveData
import src.game.inputs as inputs
from src.ui.menus import MenuManager
from src.game.inventory import InventoryState
from src.game.actorstate import PlayerState
from src.renderengine.engine import RenderEngine
import src.game.debug as debug
import src.game.cinematics as cinematics
import src.worldgen.zones as zones
import src.game.settings as settings
import src.game.readme_writer as readme_writer
import src.utils.profiling as profiling
import src.game.events as events


print("launching Cubelike...")
print("running pygame version: " + pygame.version.ver)

if debug.IS_DEV:
    print("generating readme...")
    readme_writer.write_readme(Utils.resource_path("readme_template.txt"),
                               Utils.resource_path("README.md"),
                               Utils.resource_path("gifs"))

print("initializing sounds...")
pygame.mixer.init()

SCREEN_SIZE = (800, 600)


def build_me_a_world(gs, zone_id=zones.TestZone.ZONE_ID):
    return zones.build_world(zone_id, gs)


def new_gs(menu_id):
    data_file = "save_data.json"
    if SaveData.exists_on_disk(data_file):
        save_data = SaveData.load_from_disk(data_file)
    else:
        save_data = SaveData.create_new_save_file(data_file)
    gs = GlobalState(save_data, menu_id=menu_id)
    gs.set_player_state(PlayerState("ghast", InventoryState()))
    return gs


def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    
    pygame.display.set_caption("Cubelike")
    
    pygame.display.set_mode(SCREEN_SIZE, mods)
    
    input_state = inputs.InputState()
    gs = new_gs(MenuManager.START_MENU)

    if debug.IS_DEV:
        gs.settings().set(settings.MUSIC_VOLUME, 0)
    
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

    raw_sheet = pygame.image.load(Utils.resource_path("assets/image.png"))
    cine_img = pygame.image.load(Utils.resource_path("assets/cinematics.png"))
    ui_img = pygame.image.load(Utils.resource_path("assets/ui.png"))
    tree_img = pygame.image.load(Utils.resource_path("assets/trees.png"))
    boss_img = pygame.image.load(Utils.resource_path("assets/bosses.png"))

    img_surface = spriteref.build_spritesheet(raw_sheet, cine_img, ui_img, tree_img, boss_img)
    cinematics.init_cinematics()
    
    window_icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    window_icon.blit(img_surface, (0, 0), spriteref.chest_closed.rect())
    pygame.display.set_icon(window_icon)
    
    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)

    zones.init_zones()
        
    world = None
        
    clock = pygame.time.Clock()
    running = True

    while running:
        gs.update(world, input_state, render_eng)

        for event in gs.event_queue().all_events():
            if event.get_type() == events.EventType.NEW_ZONE:
                render_eng.clear_all_sprites()
                world = build_me_a_world(gs, zone_id=event.get_next_zone())
            elif event.get_type() == events.EventType.GAME_EXIT:
                print("INFO: quitting game")
                running = False
                continue
            elif event.get_type() == events.EventType.NEW_GAME:
                print("INFO: starting fresh game")
                render_eng.clear_all_sprites()
                if event.get_instant_start():
                    menu_id = MenuManager.IN_GAME_MENU
                else:
                    menu_id = MenuManager.START_MENU
                gs = new_gs(menu_id)
                world = None
            elif event.get_type() == events.EventType.PLAYER_DIED:
                gs.menu_manager().set_active_menu(MenuManager.DEATH_MENU)

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
                input_state.set_mouse_down(True, button=event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                input_state.set_mouse_down(False, button=event.button)

            if not pygame.mouse.get_focused():
                input_state.set_mouse_pos(None)

        input_state.update(gs)

        world_active = gs.menu_manager().should_draw_world()

        if world_active and world is None:
            # building the initial world
            render_eng.clear_all_sprites()
            world = build_me_a_world(gs)

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

        if input_state.was_pressed(pygame.K_o):
            cur_value = gs.settings().get(settings.MUSIC_VOLUME)
            if cur_value > 0:
                gs.settings().set(settings.MUSIC_VOLUME, 0)
            else:
                gs.settings().set(settings.MUSIC_VOLUME, 100)

        if input_state.was_pressed(pygame.K_x) and debug.DEBUG:
            manager = gs.menu_manager()
            if manager.get_active_menu().get_type() == MenuManager.IN_GAME_MENU:
                gs.menu_manager().set_active_menu(MenuManager.DEATH_MENU)

        if debug.DEBUG and input_state.was_pressed(pygame.K_F7):
            gs.save_data().save_to_disk()

        if world_active:
            render_eng.set_clear_color(*world.get_bg_color())
            player = world.get_player()
            gs.player_state().update(player, world, gs, input_state)

            world.update_all(gs, input_state, render_eng)

            gs.dialog_manager().update(world, gs, input_state)

            shake = gs.get_screenshake()
            camera = gs.get_world_camera()
            for layer_id in spriteref.WORLD_LAYERS:
                render_eng.set_layer_offset(layer_id, *Utils.add(camera, shake))

        elif world is not None:
            world.cleanup_active_bundles(render_eng)

        gs.menu_manager().update(world, gs, input_state, render_eng)

        render_eng.render_layers()

        pygame.display.flip()

        if debug.IS_DEV and input_state.is_held(pygame.K_TAB):
            # if holding tab in dev activate slo-mo
            clock.tick(1)
        else:
            clock.tick(60)

        if gs.tick_counter % 60 == 0:
            if clock.get_fps() < 59:
                print("fps: {} ({} sprites)".format(round(clock.get_fps()*10) / 10.0, render_eng.count_sprites()))

    pygame.quit()

                
if __name__ == "__main__":
    run()
