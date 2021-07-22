import pygame
import traceback

import src.game.spriteref as spriteref
from src.utils.util import Utils
import src.game.debug as debug
import src.game.constants as constants

DEFAULT_SCREEN_SIZE = (800, 600)
MINIMUM_SCREEN_SIZE = (800, 600)


def init(name_of_game):
    print("INFO: pygame version: " + pygame.version.ver)
    print("INFO: initializing sounds...")
    pygame.mixer.pre_init(44100, -16, 1, 2048)

    try:
        pygame.mixer.init()
    except pygame.error:
        print("ERROR: failed to initialize pygame.mixer (sounds and music). Game will continue with no sound."
              " This can occur when all audio devices are disabled or unavailable.")
        traceback.print_exc()

    pygame.init()

    window_icon = pygame.image.load(Utils.resource_path("assets/icon.png"))
    pygame.display.set_icon(window_icon)

    from src.game.windowstate import WindowState
    WindowState.create_instance(window_size=DEFAULT_SCREEN_SIZE, min_size=MINIMUM_SCREEN_SIZE)
    WindowState.get_instance().set_caption(name_of_game)
    WindowState.get_instance().show()

    from src.renderengine.engine import RenderEngine
    render_eng = RenderEngine.create_instance()
    render_eng.init(*DEFAULT_SCREEN_SIZE)
    render_eng.set_min_size(*MINIMUM_SCREEN_SIZE)

    raw_sheet = pygame.image.load(Utils.resource_path("assets/image.png"))
    cine_img = pygame.image.load(Utils.resource_path("assets/cinematics.png"))
    ui_img = pygame.image.load(Utils.resource_path("assets/ui.png"))
    items_img = pygame.image.load(Utils.resource_path("assets/items.png"))
    boss_img = pygame.image.load(Utils.resource_path("assets/bosses.png"))
    cave_horror_img = pygame.image.load(Utils.resource_path("assets/cave_horror.png"))
    font_img = pygame.image.load(Utils.resource_path("assets/font.png"))
    animation_img = pygame.image.load(Utils.resource_path("assets/animations.png"))
    title_scene_img = pygame.image.load(Utils.resource_path("assets/title_scene.png"))

    img_surface = spriteref.build_spritesheet(raw_sheet, cine_img, ui_img, items_img, boss_img, cave_horror_img,
                                              font_img, animation_img, title_scene_img)

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

    px_scale = _calc_pixel_scale(DEFAULT_SCREEN_SIZE, px_scale_opt=gs.get_instance().settings().pixel_scale())
    render_eng.set_pixel_scale(px_scale)


def _calc_pixel_scale(screen_size, px_scale_opt=None, max_scale=4):
    if px_scale_opt is None:
        import src.game.globalstate as gs
        px_scale_opt = gs.get_instance().settings().pixel_scale()

    global DEFAULT_SCREEN_SIZE
    default_w = DEFAULT_SCREEN_SIZE[0]
    default_h = DEFAULT_SCREEN_SIZE[1]
    default_scale = 2

    screen_w, screen_h = screen_size

    if px_scale_opt <= 0:

        # when the screen is large enough to fit this quantity of (minimal) screens at a
        # particular scaling setting, that scale is considered good enough to switch to.
        # we choose the largest (AKA most zoomed in) "good" scale.
        step_up_x_ratio = 1.0
        step_up_y_ratio = 1.0

        best = default_scale
        for i in range(default_scale + 1, max_scale + 1):
            if (default_w / default_scale * i * step_up_x_ratio <= screen_w
                    and default_h / default_scale * i * step_up_y_ratio <= screen_h):
                best = i
            else:
                break

        return best
    else:
        return int(px_scale_opt)


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

    ignore_resize_events_next_tick = False

    while running:

        # processing "global" events
        gs.get_instance().global_event_queue().flip()
        for global_event in gs.get_instance().global_event_queue().all_events():
            if global_event.get_type() == events.GlobalEventType.GAME_EXIT:
                running = False
                continue

            elif global_event.get_type() == events.GlobalEventType.QUIT_TO_START_MENU:
                print("INFO: quitting to start menu")
                RenderEngine.get_instance().clear_all_sprites()

                gs.get_instance().save_settings_to_disk()
                gs.get_instance().save_current_game_to_disk_softly()

                gs.create_new(menus.StartMenu())
                world_view = None

            elif global_event.get_type() == events.GlobalEventType.NEW_GAME:
                print("INFO: starting game")
                RenderEngine.get_instance().clear_all_sprites()

                gs.create_new(menus.InGameUiState(), from_save_data=global_event.get_save_data())
                world_view = None

            elif global_event.get_type() == events.GlobalEventType.NEW_ZONE:
                RenderEngine.get_instance().clear_all_sprites()

                active_menu = gs.get_instance().menu_manager().get_active_menu()
                if active_menu is not None:
                    active_menu.cleanup()

                zone_id = global_event.get_next_zone()

                if global_event.get_show_zone_title():
                    title = zones.get_zone(zone_id).get_name()
                    title_menu = menus.TextOnlyMenu(title, menus.InGameUiState(), auto_advance_duration=60)
                    gs.get_instance().menu_manager().set_active_menu(title_menu)
                else:
                    gs.get_instance().menu_manager().set_active_menu(menus.InGameUiState())

                    if global_event.do_fade_in():
                        gs.get_instance().do_fade_sequence(1.0, 0.0, constants.STANDARD_FADE_DURATION)
                        gs.get_instance().pause_world_updates(constants.STANDARD_FADE_DURATION // 2)

                world = zones.build_world(zone_id)
                world_view = WorldView(world)

                gs.get_instance().set_world(world)

        # processing in-world events
        if not gs.get_instance().menu_manager().pause_world_updates():
            gs.get_instance().event_queue().flip()
            gs.get_instance().update_world_stuff()

            for zone_event in gs.get_instance().event_queue().all_events():
                if zone_event.get_type() == events.EventType.ACTOR_KILLED:
                    killer_uid = zone_event.get_killer_uid()
                    if killer_uid is not None:
                        w, p = gs.get_instance().get_world_and_player()
                        if p is not None and p.get_uid() == killer_uid:
                            gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.KILL_COUNT)

                elif zone_event.get_type() == events.EventType.ROTATED_ITEM:
                    gs.get_instance().inc_run_statistic(gs.RunStatisticTypes.ROTATED_ITEM_COUNT)

                elif zone_event.get_type() == events.EventType.GAME_WIN:
                    print("INFO: won game!")

                    import src.game.savedata as savedata
                    gs.get_instance().save_current_game_to_disk(savedata.WIN_SAVE_ID)

                    tick_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.ELAPSED_TICKS)
                    kill_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.KILL_COUNT)
                    turn_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.TURN_COUNT)
                    death_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.DEATH_COUNT)
                    cp_count = gs.get_instance().get_run_statistic(gs.RunStatisticTypes.CHECKPOINT_COUNT)

                    save_blob = gs.get_instance().get_save_data_if_present()
                    if save_blob is not None:
                        saved_version = save_blob.get(savedata.SaveDataTags.VERSION_NUM)
                    else:
                        saved_version = None

                    win_menu = menus.YouWinMenu(tick_count, turn_count, kill_count, death_count, cp_count, saved_version=saved_version)
                    gs.get_instance().menu_manager().set_active_menu(win_menu)

                elif zone_event.get_type() == events.EventType.PLAYER_DIED:
                    # save completed tutorials to disk, because these get reloaded.
                    gs.get_instance().save_settings_to_disk()

                    # saving the stats (kill_count, elapsed_time, etc.) from this run to disk
                    # (note that death_count is inc'd the moment the player dies, so we don't touch it here)
                    gs.get_instance().save_current_game_to_disk_softly()

                    # grab the save data in case we opt to retry
                    save_data = gs.get_instance().get_save_data_if_present()

                    # detach the save data from the (still-active) GS so that we stop adding elapsed time
                    gs.get_instance().detach_save_data_if_present()

                    gs.get_instance().menu_manager().set_active_menu(menus.DeathMenu(retry_save_data=save_data))

        # processing user input events
        all_resize_events = []
        toggled_fullscreen = False

        input_state = InputState.get_instance()
        for py_event in pygame.event.get():
            if py_event.type == pygame.QUIT:
                running = False
                continue
            elif py_event.type == pygame.KEYDOWN:
                input_state.set_key(py_event.key, True)
            elif py_event.type == pygame.KEYUP:
                input_state.set_key(py_event.key, False)

            elif py_event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                scr_pos = WindowState.get_instance().window_to_screen_pos(py_event.pos)
                game_pos = Utils.round(Utils.mult(scr_pos, 1 / RenderEngine.get_instance().get_pixel_scale()))
                input_state.set_mouse_pos(game_pos)

                if py_event.type == pygame.MOUSEBUTTONDOWN:
                    input_state.set_mouse_down(True, button=py_event.button)
                elif py_event.type == pygame.MOUSEBUTTONUP:
                    input_state.set_mouse_down(False, button=py_event.button)

            elif py_event.type == pygame.VIDEORESIZE:
                all_resize_events.append(py_event)

            if py_event.type == pygame.KEYDOWN and py_event.key == pygame.K_F4:
                toggled_fullscreen = True

            if not pygame.mouse.get_focused():
                input_state.set_mouse_pos(None)

        ignore_resize_events_this_tick = ignore_resize_events_next_tick
        ignore_resize_events_next_tick = False

        if toggled_fullscreen:
            # print("INFO {}: toggled fullscreen".format(gs.get_instance().tick_counter))
            win = WindowState.get_instance()
            engine = RenderEngine.get_instance()
            win.set_fullscreen(not win.is_fullscreen())

            new_size = win.get_display_size()
            new_pixel_scale = _calc_pixel_scale(new_size)
            if new_pixel_scale != RenderEngine.get_instance().get_pixel_scale():
                RenderEngine.get_instance().set_pixel_scale(new_pixel_scale)
            engine.resize(new_size[0], new_size[1], px_scale=new_pixel_scale)

            # when it goes from fullscreen to windowed mode, pygame sends a VIDEORESIZE event
            # on the next frame that claims the window has been resized to the maximum resolution.
            # this is annoying so we ignore it. we want the window to remain the same size it was
            # before the fullscreen happened.
            ignore_resize_events_next_tick = True

        if not ignore_resize_events_this_tick and len(all_resize_events) > 0:
            # print("INFO {}: got {} resize event(s)".format(gs.get_instance().tick_counter, len(all_resize_events)))
            last_resize_event = all_resize_events[-1]

            WindowState.get_instance().set_window_size(last_resize_event.w, last_resize_event.h)

            display_w, display_h = WindowState.get_instance().get_display_size()
            new_pixel_scale = _calc_pixel_scale((last_resize_event.w, last_resize_event.h))

            RenderEngine.get_instance().resize(display_w, display_h, px_scale=new_pixel_scale)

        input_state.update(gs.get_instance().tick_counter)
        sound_effects.update()

        world_active = gs.get_instance().menu_manager().should_draw_world()

        if world_active and gs.get_instance().get_world() is None:
            # building the initial world for the game
            RenderEngine.get_instance().clear_all_sprites()

            save_id = gs.get_instance().get_last_save_id()
            if save_id is not None:
                world = zones.build_world_for_save_id(save_id)
            else:
                zone_id = zones.first_zone_id()
                world = zones.build_world(zone_id)

            fade_duration = constants.STANDARD_FADE_DURATION
            gs.get_instance().do_fade_sequence(1.0, 0.0, fade_duration)
            gs.get_instance().pause_world_updates(fade_duration // 2)

            gs.get_instance().set_world(world)
            world_view = WorldView(world)

        if debug.is_dev() and input_state.was_pressed(pygame.K_F1):
            # used to help find performance bottlenecks
            import src.utils.profiling as profiling
            profiling.get_instance().toggle()

        if debug.is_dev() and world_active and input_state.was_pressed(pygame.K_F6):
            gs.get_instance().menu_manager().set_active_menu(menus.DebugMenu())
            sound_effects.play_sound(soundref.pause_in)

        if input_state.was_pressed(pygame.K_F5):
            current_scale = gs.get_instance().settings().pixel_scale()
            options = gs.get_instance().settings().pixel_scale_options()
            if current_scale in options:
                new_scale = (options.index(current_scale) + 1) % len(options)
            else:
                print("WARN: illegal pixel scale={}, reverting to default".format(current_scale))
                new_scale = options[0]
            gs.get_instance().settings().set_pixel_scale(new_scale)

            display_size = WindowState.get_instance().get_display_size()
            new_pixel_scale = _calc_pixel_scale(display_size)
            RenderEngine.get_instance().set_pixel_scale(new_pixel_scale)

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

        slo_mo_mode = debug.is_dev() and input_state.is_held(pygame.K_TAB)
        if slo_mo_mode:
            clock.tick(15)
        else:
            clock.tick(60)

        gs.get_instance().increment_tick_counts()

        if gs.get_instance().tick_counter % 60 == 0:
            if clock.get_fps() < 55 and debug.is_dev() and not slo_mo_mode:
                print("WARN: fps drop: {} ({} sprites)".format(round(clock.get_fps() * 10) / 10.0,
                                                               RenderEngine.get_instance().count_sprites()))

    print("INFO: saving game data before exit...")
    gs.get_instance().save_current_game_to_disk_softly()

    print("INFO: saving settings before exit...")
    gs.get_instance().save_settings_to_disk()

    print("INFO: quitting skeletris")
    pygame.quit()
