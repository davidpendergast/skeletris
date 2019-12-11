import pygame

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.debug as debug

DEFAULT_SCREEN_SIZE = (800, 600)


def init(name_of_game):
    print("INFO: pygame version: " + pygame.version.ver)
    print("INFO: initializing sounds...")
    pygame.mixer.pre_init(44100, -16, 1, 2048)

    pygame.mixer.init()
    pygame.init()

    # fyi this needs to happen before any calls to set_mode
    info = pygame.display.Info()
    monitor_size = (info.current_w, info.current_h)  # what happens if you have two monitors...?

    window_icon = pygame.image.load(Utils.resource_path("assets/icon.png"))
    pygame.display.set_icon(window_icon)

    from src.game.windowstate import WindowState
    WindowState.create_instance(fullscreen=False, resizeable=True,
                                screen_size=DEFAULT_SCREEN_SIZE, window_size=DEFAULT_SCREEN_SIZE,
                                fullscreen_size=monitor_size)
    WindowState.get_instance().set_caption(name_of_game)
    WindowState.get_instance().show_window(None)

    from src.renderengine.engine import RenderEngine
    render_eng = RenderEngine.create_instance()
    render_eng.init(*DEFAULT_SCREEN_SIZE)

    raw_sheet = pygame.image.load(Utils.resource_path("assets/image.png"))
    cine_img = pygame.image.load(Utils.resource_path("assets/cinematics.png"))
    ui_img = pygame.image.load(Utils.resource_path("assets/ui.png"))
    items_img = pygame.image.load(Utils.resource_path("assets/items.png"))
    boss_img = pygame.image.load(Utils.resource_path("assets/bosses.png"))
    font_img = pygame.image.load(Utils.resource_path("assets/font.png"))
    animation_img = pygame.image.load(Utils.resource_path("assets/animations.png"))
    title_scene_img = pygame.image.load(Utils.resource_path("assets/title_scene.png"))


    img_surface = spriteref.build_spritesheet(raw_sheet, cine_img, ui_img, items_img, boss_img, font_img,
                                              animation_img, title_scene_img)

    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)

    COLOR = True
    SORTS = True
    render_eng.add_layer(
        spriteref.FLOOR_LAYER,
        "floors", 0,
        False, COLOR)
    render_eng.add_layer(
        spriteref.SHADOW_LAYER,
        "shadow_layer", 5,
        False, COLOR)
    render_eng.add_layer(
        spriteref.WALL_LAYER,
        "walls", 10,
        False, COLOR)
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
    gs.create_new(menus.TitleMenu())

    import src.worldgen.zones as zones
    zones.init_zones()


def run():
    # importing is fragile (-_-)
    import src.game.events as events
    import src.game.sound_effects as sound_effects
    import src.game.soundref as soundref
    from src.world.worldview import WorldView
    import src.game.globalstate as gs
    from src.renderengine.engine import RenderEngine
    import src.ui.menus as menus
    import src.worldgen.zones as zones
    from src.game.windowstate import WindowState
    from src.game.inputs import InputState

    world_view = None

    clock = pygame.time.Clock()
    running = True

    # XXX for some reason, when you un-fullscreen it sends a boo VIDEORESIZE event
    # at max screen size, which isn't what we want (on linux at least~)
    ignore_videoresize_events_this_frame = False

    while running:
        gs.get_instance().event_queue().flip()
        gs.get_instance().update()

        for event in gs.get_instance().event_queue().all_events():
            if event.get_type() == events.EventType.NEW_ZONE:
                RenderEngine.get_instance().clear_all_sprites()

                active_menu = gs.get_instance().menu_manager().get_active_menu()
                if active_menu is not None:
                    active_menu.cleanup()

                zone_id = event.get_next_zone()

                if event.get_show_zone_title():
                    title = zones.get_zone(zone_id).get_name()
                    title_menu = menus.TextOnlyMenu(title, menus.InGameUiState(), auto_advance_duration=60)
                    gs.get_instance().menu_manager().set_active_menu(title_menu)
                else:
                    gs.get_instance().menu_manager().set_active_menu(menus.InGameUiState())

                world = zones.build_world(zone_id)
                world_view = WorldView(world)

                gs.get_instance().set_world(world)

            elif event.get_type() == events.EventType.GAME_EXIT:
                print("INFO: quitting game")
                running = False
                continue

            elif event.get_type() == events.EventType.GAME_WIN:
                print("INFO: won game!")
                tick_count = gs.get_instance().tick_counter
                kill_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.KILL_COUNT)
                turn_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.TURN_COUNT)
                win_menu = menus.YouWinMenu(tick_count, turn_count, kill_count)
                gs.get_instance().menu_manager().set_active_menu(win_menu)

            elif event.get_type() == events.EventType.ACTOR_KILLED:
                killer_uid = event.get_killer_uid()
                if killer_uid is not None:
                    w, p = gs.get_instance().get_world_and_player()
                    if p is not None and p.get_uid() == killer_uid:
                        gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.KILL_COUNT)

            elif event.get_type() == events.EventType.ROTATED_ITEM:
                # used to auto-skip the rotate item tutorial
                gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.ROTATED_ITEM_COUNT)

            elif event.get_type() == events.EventType.NEW_GAME:
                print("INFO: starting fresh game")
                RenderEngine.get_instance().clear_all_sprites()

                if event.get_instant_start():
                    menu = menus.InGameUiState()
                else:
                    menu = menus.StartMenu()

                if debug.reset_tutorials_each_game():
                    gs.get_instance().settings().clear_finished_tutorials()

                gs.get_instance().save_settings_to_disk()
                gs.get_instance().set_world(None)  # just to make it clear...

                gs.create_new(menu)
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

            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                scr_pos = WindowState.get_instance().window_to_screen_pos(event.pos)
                game_pos = Utils.round(Utils.mult(scr_pos, 1 / RenderEngine.get_instance().get_pixel_mult()))
                input_state.set_mouse_pos(game_pos)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    input_state.set_mouse_down(True, button=event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    input_state.set_mouse_down(False, button=event.button)

            elif event.type == pygame.VIDEORESIZE and not ignore_videoresize_events_this_frame:
                # XXX ideally we'd set the window size to no smaller than the min size
                # but that seems to break resizing entirely on linux so... (._.)
                WindowState.get_instance().set_window_size(event.w, event.h, RenderEngine.get_instance(), forcefully=True)
                screen_size = (max(800, event.w), max(600, event.h))
                WindowState.get_instance().set_screen_size(*screen_size)
                RenderEngine.get_instance().resize(*screen_size)

            if not pygame.mouse.get_focused():
                input_state.set_mouse_pos(None)

        ignore_videoresize_events_this_frame = False

        input_state.update(gs.get_instance().tick_counter)
        sound_effects.update()

        world_active = gs.get_instance().menu_manager().should_draw_world()

        if world_active and gs.get_instance().get_world() is None:
            # building the initial world for the game
            RenderEngine.get_instance().clear_all_sprites()

            world = zones.build_world(gs.get_instance().initial_zone_id)

            gs.get_instance().set_world(world)
            world_view = WorldView(world)

        if debug.is_dev() and input_state.was_pressed(pygame.K_F1):
            # used to help find performance bottlenecks
            import src.utils.profiling as profiling
            profiling.get_instance().toggle()

        if input_state.was_pressed(pygame.K_F4):
            win = WindowState.get_instance()
            fullscreen = not win.get_fullscreen()
            win.set_fullscreen(fullscreen, RenderEngine.get_instance(), forcefully=True)

            ignore_videoresize_events_this_frame = True

            new_size = win.get_display_size()
            win.set_screen_size(*new_size)
            RenderEngine.get_instance().resize(*new_size)

        if debug.is_debug() and world_active and input_state.was_pressed(pygame.K_F6):
            gs.get_instance().menu_manager().set_active_menu(menus.DebugMenu())
            sound_effects.play_sound(soundref.pause_in)

        if debug.is_debug() and input_state.was_pressed(pygame.K_x):
            manager = gs.get_instance().menu_manager()
            if manager.get_active_menu().get_type() == menus.MenuManager.IN_GAME_MENU:
                gs.get_instance().menu_manager().set_active_menu(menus.DeathMenu())

        if debug.is_debug() and input_state.was_pressed(pygame.K_F10):
            gs.get_instance().event_queue().add(events.GameWinEvent())

        world = gs.get_instance().get_world()
        if world is not None:
            if world_active:
                RenderEngine.get_instance().set_clear_color(*world.get_bg_color())

                world.update_all()
                world_view.update_all()

                gs.get_instance().dialog_manager().update(world)

                shake = gs.get_instance().get_screenshake()
                camera = gs.get_instance().get_actual_camera_xy()
                for layer_id in spriteref.WORLD_LAYERS:
                    RenderEngine.get_instance().set_layer_offset(layer_id, *Utils.add(camera, shake))

            elif world_view is not None:
                world_view.cleanup_active_bundles()

        gs.get_instance().menu_manager().update()

        RenderEngine.get_instance().render_layers()

        pygame.display.flip()

        if debug.is_dev() and input_state.is_held(pygame.K_TAB):
            # activate slo-mo
            clock.tick(15)
        else:
            clock.tick(60)

        if gs.get_instance().tick_counter % 60 == 0:
            if clock.get_fps() < 55:
                print("WARN: fps drop: {} ({} sprites)".format(round(clock.get_fps() * 10) / 10.0,
                                                               RenderEngine.get_instance().count_sprites()))

    print("INFO: saving settings before exit")
    gs.get_instance().save_settings_to_disk()

    pygame.quit()
