import traceback

import pygame

import src.game.spriteref as spriteref
from src.utils.util import Utils

print("INFO: launching Cubelike...")
print("INFO: running pygame version: " + pygame.version.ver)

import src.game.debug as debug
if debug.is_dev():
    print("generating readme...")
    import src.game.readme_writer as readme_writer
    readme_writer.write_readme(Utils.resource_path("readme_template.txt"),
                               Utils.resource_path("README.md"),
                               Utils.resource_path("gifs"))

print("initializing sounds...")
pygame.mixer.pre_init(44100, -16, 1, 2048)

SCREEN_SIZE = (800, 600)


def run():
    pygame.mixer.init()
    pygame.init()

    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE

    pygame.display.set_caption("Slap Monster, Get Treasure")

    pygame.display.set_mode(SCREEN_SIZE, mods)

    from src.renderengine.engine import RenderEngine
    render_eng = RenderEngine.create_instance()
    render_eng.init(*SCREEN_SIZE)

    raw_sheet = pygame.image.load(Utils.resource_path("assets/image.png"))
    cine_img = pygame.image.load(Utils.resource_path("assets/cinematics.png"))
    ui_img = pygame.image.load(Utils.resource_path("assets/ui.png"))
    items_img = pygame.image.load(Utils.resource_path("assets/items.png"))
    boss_img = pygame.image.load(Utils.resource_path("assets/bosses.png"))
    font_img = pygame.image.load(Utils.resource_path("assets/font.png"))

    img_surface = spriteref.build_spritesheet(raw_sheet, cine_img, ui_img, items_img, boss_img, font_img)

    import src.game.cinematics as cinematics
    cinematics.init_cinematics()

    window_icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    window_icon.blit(img_surface, (0, 0), spriteref.chest_closed.rect())
    pygame.display.set_icon(window_icon)

    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)

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
            SORTS, COLOR)
    render_eng.add_layer(
            spriteref.UI_TOOLTIP_LAYER,
            "ui_tooltips", 25,
            False, COLOR)

    from src.game.inputs import InputState
    InputState.create_instance()

    import src.game.globalstate as gs
    import src.ui.menus as menus
    gs.create_new(menus.StartMenu())

    import src.worldgen.zones as zones
    zones.init_zones()

    import src.game.settings as settings
    import src.game.events as events
    import src.game.sound_effects as sound_effects
    from src.world.worldview import WorldView
        
    world = None
    world_view = None
        
    clock = pygame.time.Clock()
    running = True

    while running:
        gs.get_instance().update(world)

        for event in gs.get_instance().event_queue().all_events():
            if event.get_type() == events.EventType.NEW_ZONE:
                print("INFO: new zone {}".format(event.get_next_zone()))
                render_eng.clear_all_sprites()

                active_menu = gs.get_instance().menu_manager().get_active_menu()
                if active_menu is not None:
                    active_menu.cleanup()

                if event.get_transfer_type() == events.NewZoneEvent.RETURNING:
                    spawn_at = event.get_current_zone()
                else:
                    spawn_at = None

                world = zones.build_world(event.get_next_zone(), spawn_at_door_with_zone_id=spawn_at)
                world_view = WorldView(world)

                # kind of a hack to prevent the world from flashing for a frame before the cinematic starts
                if len(gs.get_instance().get_cinematics_queue()) > 0:
                    gs.get_instance().menu_manager().update(world)

            elif event.get_type() == events.EventType.GAME_EXIT:
                print("INFO: quitting game")
                running = False
                continue
            elif event.get_type() == events.EventType.NEW_GAME:
                print("INFO: starting fresh game")
                render_eng.clear_all_sprites()

                if event.get_instant_start():
                    menu = menus.InGameUiState()
                else:
                    menu = menus.StartMenu()

                gs.get_instance().save_settings_to_disk()
                gs.create_new(menu)
                world = None
                world_view = None
            elif event.get_type() == events.EventType.PLAYER_DIED:
                gs.get_instance().menu_manager().set_active_menu(menus.DeathMenu())

        input_state = InputState.get_instance()
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
                input_state.set_mouse_pos(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                input_state.set_mouse_down(False, button=event.button)
                input_state.set_mouse_pos(event.pos)

            if not pygame.mouse.get_focused():
                input_state.set_mouse_pos(None)

        input_state.update(gs.get_instance().tick_counter)
        sound_effects.update()

        world_active = gs.get_instance().menu_manager().should_draw_world()

        if world_active and world is None:
            # building the initial world for the game
            render_eng.clear_all_sprites()
            initial_zone_id = gs.get_instance().initial_zone_id
            loading_save = initial_zone_id != zones.first_zone_id()
            world = zones.build_world(gs.get_instance().initial_zone_id, spawn_at_save_station=loading_save)
            world_view = WorldView(world)

            if len(gs.get_instance().get_cinematics_queue()) > 0:
                gs.get_instance().menu_manager().update(world)
                world_active = False

        if debug.is_debug() and input_state.was_pressed(pygame.K_F1):
            # used to help find performance bottlenecks
            import src.utils.profiling as profiling
            profiling.get_instance().toggle()

        if input_state.was_pressed(pygame.K_F4):
            size = gs.get_instance().screen_size
            if gs.get_instance().is_fullscreen:
                pygame.display.set_mode(size, pygame.OPENGL)
            else:
                pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.OPENGL)
            gs.get_instance().is_fullscreen = not gs.get_instance().is_fullscreen

        if debug.is_debug() and world_active and input_state.was_pressed(pygame.K_F6):
            print("INFO: opened debug menu")
            gs.get_instance().menu_manager().set_active_menu(menus.DebugMenu())

        if input_state.was_pressed(pygame.K_o):
            manager = gs.get_instance().menu_manager()
            if not manager.get_active_menu().absorbs_key_inputs():
                cur_value = gs.get_instance().settings().get(settings.MUSIC_VOLUME)
                if cur_value > 0:
                    gs.get_instance().settings().set(settings.MUSIC_VOLUME, 0)
                else:
                    gs.get_instance().settings().set(settings.MUSIC_VOLUME, 100)

        if debug.is_debug() and input_state.was_pressed(pygame.K_x):
            manager = gs.get_instance().menu_manager()
            if manager.get_active_menu().get_type() == menus.MenuManager.IN_GAME_MENU:
                gs.get_instance().menu_manager().set_active_menu(menus.DeathMenu())

        if world_active:
            render_eng.set_clear_color(*world.get_bg_color())

            world.update_all()
            world_view.update_all()

            gs.get_instance().dialog_manager().update(world)

            shake = gs.get_instance().get_screenshake()
            camera = gs.get_instance().get_actual_camera_xy()
            for layer_id in spriteref.WORLD_LAYERS:
                render_eng.set_layer_offset(layer_id, *Utils.add(camera, shake))

        elif world is not None:
            world_view.cleanup_active_bundles()

        gs.get_instance().menu_manager().update(world)

        render_eng.render_layers()

        pygame.display.flip()

        if debug.is_dev() and input_state.is_held(pygame.K_TAB):
            # if holding tab in dev activate slo-mo
            clock.tick(1)
        else:
            clock.tick(60)

        if gs.get_instance().tick_counter % 60 == 0:
            if clock.get_fps() < 59:
                print("fps: {} ({} sprites)".format(round(clock.get_fps()*10) / 10.0, render_eng.count_sprites()))

    try:
        print("INFO: saving settings before exit")
        gs.get_instance().save_settings_to_disk()
    except:
        print("ERROR: failed to save settings")
        traceback.print_exc()

    pygame.quit()

                
if __name__ == "__main__":
    run()
