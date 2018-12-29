import random

import pygame

from src.game import spriteref as spriteref
from src.items import item as item_module
from src.ui.tooltips import TooltipFactory
from src.ui.ui import HealthBarPanel, InventoryPanel, CinematicPanel, TextImage, ItemImage, DialogPanel
from src.utils.util import Utils
import src.game.events as events
import src.game.music as music
import src.game.settings as settings
import src.game.globalstate as gs


class MenuManager:

    DEATH_MENU = 0
    DEATH_OPTION_MENU = 0.5
    IN_GAME_MENU = 1
    START_MENU = 2
    CINEMATIC_MENU = 3
    PAUSE_MENU = 4
    CONTROLS_MENU = 5
    KEYBINDING_MENU = 7

    def __init__(self, menu):
        self._active_menu = StartMenu()
        self._next_active_menu = menu

    def update(self, world, input_state, render_eng):
        if self._next_active_menu is not None:
            for bun in self._active_menu.all_bundles():
                render_eng.remove(bun)

            self._active_menu.cleanup()

            self._active_menu = self._next_active_menu

            new_song = self._active_menu.get_song()
            if new_song is not None:
                music.play_song(new_song)

            self._next_active_menu = None

            if not self.should_draw_world():
                render_eng.set_clear_color(*self._active_menu.get_clear_color())
                for layer in spriteref.WORLD_LAYERS:
                    render_eng.hide_layer(layer)
            else:
                for layer in spriteref.WORLD_LAYERS:
                    render_eng.show_layer(layer)

        else:
            if world is None and self.should_draw_world():
                current_id = self.get_active_menu().get_type()
                raise ValueError("world is None for menu that needs a world: {}".format(current_id))
            else:
                self.get_active_menu().update(world, input_state, render_eng)

    def should_draw_world(self):
        return self._active_menu.keep_drawing_world_underneath()

    def pause_world_updates(self):
        return self.get_active_menu_id() != MenuManager.IN_GAME_MENU

    def get_active_menu(self):
        return self._active_menu

    def get_active_menu_id(self):
        if self._active_menu is not None:
            return self._active_menu.get_type()
        else:
            return None

    def set_active_menu(self, menu_or_id):
        """
        :param menu_or_id: either a Menu or a (number) menu id.
        """
        if menu_or_id is None:
            raise ValueError("Can't set null menu")

        self._next_active_menu = menu_or_id

    def get_world_menu_if_active(self):
        active = self.get_active_menu()
        if active is not None and active.get_type() == MenuManager.IN_GAME_MENU:
            return active
        else:
            return None


class Menu:

    def __init__(self, menu_type):
        self._menu_type = menu_type
        self._active_tooltip = None

    def get_clear_color(self):
        return (0.5, 0.5, 0.5)

    def get_type(self):
        return self._menu_type

    def update(self, world, input_state, render_eng):
        pass

    def get_song(self):
        return None

    def all_bundles(self):
        tooltip = self.get_active_tooltip()
        if tooltip is not None:
            for bun in tooltip.all_bundles():
                yield bun
        else:
            return []

    def cleanup(self):
        pass

    def keep_drawing_world_underneath(self):
        return False

    def get_active_tooltip(self):
        return self._active_tooltip

    def set_active_tooltip(self, tooltip, render_eng):
        if self._active_tooltip is not None:
            self._destroy_panel(self._active_tooltip, render_eng)
        self._active_tooltip = tooltip

    def _destroy_panel(self, panel, render_eng):
        if panel is not None:
            bundles = panel.all_bundles()
            render_eng.clear_bundles(bundles)


class OptionsMenu(Menu):

    def __init__(self, menu_id, title, options, title_size=5):
        Menu.__init__(self, menu_id)
        self.title_text = title
        self.title_size = title_size
        self.options_text = options

        self.spacing = 16
        self.title_spacing = self.spacing * 4

        self._title_img = None
        self._title_rect = None    # tuple(x, y, w, h)
        self._option_rects = None  # list of tuple(x, y, w, h)
        self._option_imgs = None   # list of ImgBundle
        self._selection = 0

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def get_title_color(self):
        return (1, 1, 1)

    def get_option_color(self, idx):
        if idx == self._selection:
            return (1, 0, 0)
        else:
            return (1, 1, 1)

    def get_option_text(self, idx):
        return self.options_text[idx]

    def get_num_options(self):
        return len(self.options_text)

    def build_title_img(self):
        if self.title_text is not None:
            if self._title_img is None:
                self._title_img = TextImage(0, 0, self.title_text, layer=spriteref.UI_0_LAYER,
                                            color=self.get_title_color(), scale=self.title_size)

    def build_option_imgs(self):
        if self._option_imgs is None:
            self._option_imgs = [None] * self.get_num_options()

        for i in range(0, self.get_num_options()):
            if self._option_imgs[i] is None:
                self._option_imgs[i] = TextImage(0, 0, self.get_option_text(i), layer=spriteref.UI_0_LAYER,
                                                 color=self.get_option_color(i), scale=3)

    def _layout_rects(self):
        if self._title_rect is None:
            self._title_rect = (0, 0, 0, 0)
        if self._option_rects is None:
            self._option_rects = [(0, 0, 0, 0)] * self.get_num_options()

        total_height = 0
        if self._title_img is not None:
            total_height += self._title_img.size()[1] + self.title_spacing
        for opt in self._option_imgs:
            if opt is not None:
                total_height += opt.size()[1] + self.spacing
        total_height -= self.spacing

        y_pos = gs.get_instance().screen_size[1] // 2 - total_height // 2
        if self._title_img is not None:
            title_x = gs.get_instance().screen_size[0] // 2 - self._title_img.size()[0] // 2
            self._title_rect = (title_x, y_pos, self._title_img.size()[0], self._title_img.size()[1])
            y_pos += self._title_img.size()[1] + self.title_spacing

        for i in range(0, self.get_num_options()):
            if self._option_imgs[i] is not None:
                opt_x = gs.get_instance().screen_size[0] // 2 - self._option_imgs[i].size()[0] // 2
                self._option_rects[i] = (opt_x, y_pos, self._option_imgs[i].size()[0], self._option_imgs[i].size()[1])
                y_pos += self._option_imgs[i].size()[1] + self.spacing

    def _update_imgs(self):
        if self._title_img is not None:
            x = self._title_rect[0]
            y = self._title_rect[1]
            self._title_img = self._title_img.update(new_x=x, new_y=y, new_color=self.get_title_color())

        for i in range(0, self.get_num_options()):
            color = self.get_option_color(i)
            x = self._option_rects[i][0]
            y = self._option_rects[i][1]
            self._option_imgs[i] = self._option_imgs[i].update(new_x=x, new_y=y, new_color=color)

    def handle_inputs(self, world, input_state, render_eng):
        if input_state.was_pressed(gs.get_instance().settings().exit_key()):
            self.esc_pressed()
        else:
            if input_state.was_pressed(gs.get_instance().settings().up_key()):
                self._selection = (self._selection - 1) % self.get_num_options()
            if input_state.was_pressed(gs.get_instance().settings().down_key()):
                self._selection = (self._selection + 1) % self.get_num_options()
            if input_state.was_pressed(gs.get_instance().settings().enter_key()):
                self.option_activated(self._selection)

            if self._option_rects is None:
                return

            if input_state.mouse_in_window():
                pos = input_state.mouse_pos()
                if input_state.mouse_moved():
                    for i in range(0, self.get_num_options()):
                        if self._option_rects[i] is not None and Utils.rect_contains(self._option_rects[i], pos):
                            self._selection = i

                if input_state.mouse_was_pressed():
                    clicked_option = None

                    selected_rect = self._option_rects[self._selection]
                    if selected_rect is not None:
                        # give click priority to the thing that's selected
                        bigger_rect = Utils.rect_expand(selected_rect, 15, 15, 15, 15)
                        if Utils.rect_contains(bigger_rect, pos):
                            self.option_activated(self._selection)
                            clicked_option = self._selection

                    if clicked_option is None:
                        # if the mouse hasn't moved yet on this menu, gotta catch those clicks too
                        for i in range(0, self.get_num_options()):
                            if self._option_rects[i] is not None and Utils.rect_contains(self._option_rects[i], pos):
                                clicked_option = i
                                break

                    if clicked_option is not None:
                        self.option_activated(clicked_option)

    def update(self, world, input_state, render_eng):
        self.build_title_img()
        self.build_option_imgs()
        self._layout_rects()
        self._update_imgs()

        self.handle_inputs(world, input_state, render_eng)

        for bun in self.all_bundles():
            render_eng.update(bun)

    def option_activated(self, idx):
        pass

    def esc_pressed(self):
        pass

    def keep_drawing_world_underneath(self):
        return False

    def all_bundles(self):
        if self._title_img is not None:
            for bun in self._title_img.all_bundles():
                yield bun
        if self._option_imgs is not None:
            for opt in self._option_imgs:
                if opt is not None:
                    for bun in opt.all_bundles():
                        yield bun


class StartMenu(OptionsMenu):

    START_OPT = 0
    OPTIONS_OPT = 1
    EXIT_OPT = 2

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.START_MENU, "cubelike", ["start", "controls", "exit"], title_size=10)

    def get_song(self):
        return music.Songs.MENU_THEME

    def option_activated(self, idx):
        if idx == StartMenu.START_OPT:
            gs.get_instance().event_queue().add(events.NewGameEvent(instant_start=True))
        elif idx == StartMenu.EXIT_OPT:
            gs.get_instance().event_queue().add(events.GameExitEvent())
        elif idx == StartMenu.OPTIONS_OPT:
            gs.get_instance().menu_manager().set_active_menu(ControlsMenu(MenuManager.START_MENU))


class PauseMenu(OptionsMenu):

    CONTINUE_IDX = 0
    HELP_IDX = 1
    EXIT_IDX = 2

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.PAUSE_MENU, "paused", ["back", "controls", "quit"])

    def option_activated(self, idx):
        if idx == PauseMenu.EXIT_IDX:
            gs.get_instance().menu_manager().set_active_menu(StartMenu())
        elif idx == PauseMenu.HELP_IDX:
            gs.get_instance().menu_manager().set_active_menu(ControlsMenu(MenuManager.IN_GAME_MENU))
        elif idx == PauseMenu.CONTINUE_IDX:
            gs.get_instance().menu_manager().set_active_menu(InGameUiState())

    def esc_pressed(self):
        gs.get_instance().menu_manager().set_active_menu(InGameUiState())


class ControlsMenu(OptionsMenu):

    OPTS = [
        ("move up", settings.KEY_UP),
        ("move left", settings.KEY_LEFT),
        ("move down", settings.KEY_DOWN),
        ("move right", settings.KEY_RIGHT),
        ("interact", settings.KEY_INTERACT),
        ("attack", settings.KEY_ATTACK),
        ("use potion", settings.KEY_POTION),
        ("inventory", settings.KEY_INVENTORY),
        ("rotate item", settings.KEY_ROTATE_CW)
    ]
    BACK_OPT_IDX = len(OPTS)

    def __init__(self, prev_id):
        OptionsMenu.__init__(self, MenuManager.CONTROLS_MENU, "controls", ["~unused~"])
        self.prev_id = prev_id

    def _layout_rects(self):
        OptionsMenu._layout_rects(self)

    def get_option_text(self, idx):
        if idx == ControlsMenu.BACK_OPT_IDX:
            return "back"
        else:
            opt = ControlsMenu.OPTS[idx]

            cur_value = gs.get_instance().settings().get(opt[1])
            if isinstance(cur_value, list):
                cur_value = cur_value[0]

            return opt[0] + " [{}]".format(Utils.stringify_key(cur_value))

    def get_num_options(self):
        return len(ControlsMenu.OPTS) + 1  # extra one is the "back" option

    def option_activated(self, idx):
        if idx == ControlsMenu.BACK_OPT_IDX:
            if self.prev_id == MenuManager.START_MENU:
                gs.get_instance().menu_manager().set_active_menu(StartMenu())
            else:
                gs.get_instance().menu_manager().set_active_menu(PauseMenu())
        else:
            opt = ControlsMenu.OPTS[idx]
            gs.get_instance().menu_manager().set_active_menu(KeybindingEditMenu(opt[1], opt[0], lambda: ControlsMenu(self.prev_id)))

    def esc_pressed(self):
        if self.prev_id == MenuManager.START_MENU:
            gs.get_instance().menu_manager().set_active_menu(StartMenu())
        else:
            gs.get_instance().menu_manager().set_active_menu(PauseMenu())


class KeybindingEditMenu(OptionsMenu):

    def __init__(self, setting, setting_name, return_menu_builder):
        """
        return_menu_builder: lambda () -> Menu
        """
        OptionsMenu.__init__(self, MenuManager.KEYBINDING_MENU, "edit " + setting_name,
                             ["press new key"])

        self._setting = setting
        self._return_menu_builder = return_menu_builder

    def option_activated(self, idx):
        pass

    def get_option_color(self, idx):
        return (1, 1, 1)

    def esc_pressed(self):
        gs.get_instance().menu_manager().set_active_menu(self._return_menu_builder())

    def handle_inputs(self, world, input_state, render_eng):
        if input_state.was_pressed(gs.get_instance().settings().exit_key()):
            self.esc_pressed()
        else:
            pressed = input_state.all_pressed_keys()
            pressed = [x for x in pressed if self._is_valid_binding(x)]
            if len(pressed) > 0:
                key = random.choice(pressed)  # TODO - better way to handle this?
                gs.get_instance().settings().set(self._setting, [key])
                gs.get_instance().save_settings_to_disk()
                gs.get_instance().menu_manager().set_active_menu(self._return_menu_builder())

    def _is_valid_binding(self, key):
        if key in (pygame.K_RETURN, pygame.K_ESCAPE, "MOUSE_BUTTON_1"):
            return False

        return True


class CinematicMenu(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.CINEMATIC_MENU)
        self.active_scene = None

        self.letter_reveal_speed = 3
        self.active_tick_count = 0  # how many ticks the current cinematic has been showing

        self.cinematic_panel = None

    def get_song(self):
        # each scene will specify its song
        return music.Songs.CONTINUE_CURRENT

    def update(self, world, input_state, render_eng):
        if self.active_scene is None:
            cine_queue = gs.get_instance().get_cinematics_queue()
            if len(cine_queue) == 0:
                gs.get_instance().menu_manager().set_active_menu(InGameUiState())
                return
            else:
                self.active_scene = cine_queue.pop(0)
                self.active_tick_count = 0
                music.play_song(self.active_scene.music_id)

        if self.active_scene is not None:
            if self.cinematic_panel is None:
                self.cinematic_panel = CinematicPanel()

            img_idx = (gs.get_instance().anim_tick // 2) % len(self.active_scene.images)
            current_image = self.active_scene.images[img_idx]
            num_chars_to_display = 1 + self.active_tick_count // self.letter_reveal_speed
            text_finished_scrolling = len(self.active_scene.text) <= num_chars_to_display
            full_text = self.active_scene.text

            if text_finished_scrolling:
                current_text = full_text
            else:
                vis_text = full_text[0:num_chars_to_display]
                invis_text = full_text[num_chars_to_display:]
                invis_text = Utils.replace_all_except(invis_text, TextImage.INVISIBLE_CHAR, except_for=(" ", "\n"))

                current_text = vis_text + invis_text

            self.cinematic_panel.update(render_eng, current_image, current_text)

            if self.active_tick_count > 10 and input_state.was_pressed(gs.get_instance().settings().interact_key()):
                if text_finished_scrolling:
                    self.active_scene = None
                else:
                    self.active_tick_count = len(full_text) * self.letter_reveal_speed

            self.active_tick_count += 1

        for bun in self.all_bundles():
            render_eng.update(bun)

    def get_clear_color(self):
        return (0.0, 0.0, 0.0)

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.cinematic_panel is not None:
            for bun in self.cinematic_panel.all_bundles():
                yield bun


class DeathMenu(OptionsMenu):
    """Displays some flavor text, then becomes a death option menu"""

    ALL_FLAVOR = [
        "you'll do better next time!",
        "epic run!",
        "ouch!"
    ]

    def get_clear_color(self):
        return (0, 0, 0)

    def _get_flavor_text(self):
        idx = int(random.random() * len(DeathMenu.ALL_FLAVOR))
        return DeathMenu.ALL_FLAVOR[idx]

    def get_flavor_progress(self):
        return Utils.bound(self._flavor_tick / self._flavor_full_brightness_duration, 0.0, 1.0)

    def get_title_color(self):
        # fade in
        return Utils.linear_interp(self.get_clear_color(), (1, 1, 1), self.get_flavor_progress())

    def get_option_color(self, idx):
        return self.get_clear_color()

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.DEATH_MENU, self._get_flavor_text(), ["~hidden~"], title_size=3)
        self._flavor_full_brightness_duration = 100
        self._total_duration = 120
        self._flavor_tick = 0

    def update(self, world, input_state, render_eng):
        OptionsMenu.update(self, world, input_state, render_eng)

        self._flavor_tick += 1
        if self._flavor_tick >= self._total_duration:
            gs.get_instance().menu_manager().set_active_menu(DeathOptionMenu())

    def get_song(self):
        return None

    def option_activated(self, idx):
        pass


class DeathOptionMenu(OptionsMenu):

    RETRY_OPT = 0
    EXIT_OPT = 1

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.DEATH_OPTION_MENU, "game over", ["retry", "quit"])

    def get_song(self):
        return None

    def option_activated(self, idx):
        if idx == DeathOptionMenu.RETRY_OPT:
            gs.get_instance().event_queue().add(events.NewGameEvent(instant_start=True))
        elif idx == DeathOptionMenu.EXIT_OPT:
            gs.get_instance().event_queue().add(events.NewGameEvent(instant_start=False))


class InGameUiState(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.IN_GAME_MENU)
        self.inventory_panel = None
        self.health_bar_panel = None
        self.dialog_panel = None
        self.world_ui_panel = None          # for things like locked door UIs
        self.top_right_info_panel = None

        self.item_on_cursor_offs = [0, 0]
        self.item_on_cursor_image = None

    def get_song(self):
        # zones specify their songs
        return music.Songs.CONTINUE_CURRENT

    def keep_drawing_world_underneath(self):
        return True

    def _get_entity_at_world_coords(self, world, world_pos, cond=None):
        hover_rad = 32
        hover_over = world.entities_in_circle(world_pos, hover_rad)
        if cond is not None:
            hover_over = list(filter(cond, hover_over))
        if len(hover_over) > 0:
            return hover_over[0]
        else:
            return None

    def _get_top_right_info_obj(self, world):
        return gs.get_instance().player_state().held_item

    def _update_top_right_info_panel(self, world, input_state, render_eng):
        obj_to_display = self._get_top_right_info_obj(world)

        if self.top_right_info_panel is not None:
            if obj_to_display is None or self.top_right_info_panel.get_target() is not obj_to_display:
                for bun in self.top_right_info_panel.all_bundles():
                    render_eng.remove(bun)
                self.top_right_info_panel = None

        if self.top_right_info_panel is None and obj_to_display is not None:
            new_panel = TooltipFactory.build_tooltip(obj_to_display, layer=spriteref.UI_0_LAYER)
            w = new_panel.get_rect()[2]
            xy = (gs.get_instance().screen_size[0] - w - 16, 16)

            # XXX building it twice because we don't know how wide it will be beforehand...
            new_panel = TooltipFactory.build_tooltip(obj_to_display, xy=xy, layer=spriteref.UI_0_LAYER)
            self.top_right_info_panel = new_panel
            for bun in self.top_right_info_panel.all_bundles():
                render_eng.update(bun)

    def _update_tooltip(self, world, input_state, render_eng):
        needs_update = False
        obj_to_display = None
        screen_pos = input_state.mouse_pos()

        if input_state.mouse_in_window() and gs.get_instance().player_state().held_item is None:
            if self.in_inventory_panel(screen_pos):
                grid_n_cell = self.get_clicked_inventory_grid_and_cell(screen_pos)
                if grid_n_cell is not None:
                    grid, cell = grid_n_cell
                    obj_to_display = grid.item_at_position(cell)
            else:
                world_pos = gs.get_instance().screen_to_world_coords(screen_pos)
                item_entity = self._get_entity_at_world_coords(world, world_pos, lambda x: x.is_item())
                if item_entity is not None:
                    obj_to_display = item_entity.get_item()
                else:
                    enemy_entity = self._get_entity_at_world_coords(world, world_pos, lambda x: x.is_enemy())
                    if enemy_entity is not None:
                        obj_to_display = enemy_entity.state

        if obj_to_display is not None:
            current_tooltip = self.get_active_tooltip()
            if current_tooltip is None or current_tooltip.get_target() is not obj_to_display:
                new_tooltip = TooltipFactory.build_tooltip(obj_to_display)
                self.set_active_tooltip(new_tooltip, render_eng)
                needs_update = True

            offs = (-screen_pos[0], -screen_pos[1])
            render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, *offs)

        current_tooltip = self.get_active_tooltip()

        if needs_update and current_tooltip is not None:
            for bun in current_tooltip.all_bundles():
                render_eng.update(bun)

        if gs.get_instance().player_state().is_dead() or obj_to_display is None:
            self.set_active_tooltip(None, render_eng)

    def _update_dialog_panel(self, world, input_state, render_eng):
        should_destroy = (self.dialog_panel is not None and (not gs.get_instance().dialog_manager().is_active() or
                          self.dialog_panel.get_dialog() is not gs.get_instance().dialog_manager().get_dialog()))

        if should_destroy:
            self._destroy_panel(self.dialog_panel, render_eng)
            self.dialog_panel = None

        if gs.get_instance().dialog_manager().is_active():
            if self.dialog_panel is None:
                dialog = gs.get_instance().dialog_manager().get_dialog()
                self.dialog_panel = DialogPanel(dialog)

        if self.dialog_panel is not None:
            self.dialog_panel.update(render_eng)

    def _update_inventory_panel(self, world, input_state, render_eng):
        if gs.get_instance().player_state().is_dead():
            if self.inventory_panel is not None:
                self._destroy_panel(self.inventory_panel, render_eng)
                self.inventory_panel = None

        elif input_state.was_pressed(gs.get_instance().settings().inventory_key()):
            if self.inventory_panel is None:
                self.rebuild_inventory(render_eng)
            else:
                self._destroy_panel(self.inventory_panel, render_eng)
                self.inventory_panel = None

        elif self.inventory_panel is not None and self.inventory_panel.gs_info_is_outdated():
            self.rebuild_inventory(render_eng)

    def _update_health_bar_panel(self, world, input_state, render_eng):
        if self.health_bar_panel is None:
            self.health_bar_panel = HealthBarPanel()
        self.health_bar_panel.update(world, input_state, render_eng)

    def _update_world_ui_panel(self, world, input_state, render_eng):
        if self.world_ui_panel is not None:
            inv_rect = self.get_inventory_rect()
            if inv_rect is None:
                center = (gs.get_instance().screen_size[0] // 2, gs.get_instance().screen_size[1] // 2)
            else:
                center = (inv_rect[2] + (gs.get_instance().screen_size[0] - inv_rect[2]) // 2, gs.get_instance().screen_size[1] // 2)
            size = self.world_ui_panel.size()
            self.world_ui_panel.set_xy(center[0] - size[0] // 2, center[1] - size[1] // 2)

            self.world_ui_panel.update(world, input_state, render_eng)
            if self.world_ui_panel.should_destroy(world, input_state, render_eng):
                self.world_ui_panel.prepare_to_destroy(world, input_state, render_eng)
                for bun in self.world_ui_panel.all_bundles():
                    render_eng.remove(bun)

    def showing_popup_panel(self):
        return self.world_ui_panel is not None

    def add_popup_panel(self, panel):
        """panel: PopupPanel"""
        self.world_ui_panel = panel

    def in_inventory_panel(self, screen_pos):
        rect = self.get_inventory_rect()
        if rect is None:
            return False
        else:
            return Utils.rect_contains(rect, screen_pos)

    def get_inventory_rect(self):
        if self.inventory_panel is None:
            return None
        else:
            return self.inventory_panel.total_rect

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

    def _update_item_on_cursor(self, world, input_state, render_eng):
        destroy_image = False
        create_image = False
        rebuild_inventory = False

        ps = gs.get_instance().player_state()

        if not input_state.mouse_in_window():
            destroy_image = True

        elif ps.held_item is not None and self.item_on_cursor_image is None:
            create_image = True

        elif ps.held_item is None and self.item_on_cursor_image is not None:
            destroy_image = True

        elif input_state.mouse_was_pressed():
            screen_pos = input_state.mouse_pos()

            if self.in_inventory_panel(screen_pos):
                if ps.held_item is not None:
                    # when holding an item, gotta offset the click to the top left corner
                    grid_click_pos = Utils.add(screen_pos, self.item_on_cursor_offs)
                    grid_click_pos = Utils.add(grid_click_pos, (16, 16))  # plus some fudge XXX
                else:
                    grid_click_pos = screen_pos

                clicked_grid_n_cell = self.get_clicked_inventory_grid_and_cell(grid_click_pos)
                if clicked_grid_n_cell is not None:
                    grid = clicked_grid_n_cell[0]
                    cell = clicked_grid_n_cell[1]
                    if ps.held_item is not None:
                        if grid.can_place(ps.held_item, cell):
                            grid.place(ps.held_item, cell)
                            ps.held_item = None
                            destroy_image = True
                            rebuild_inventory = True
                        else:
                            replaced_with = grid.try_to_replace(ps.held_item, cell)
                            if replaced_with is not None:
                                ps.held_item = replaced_with

                                destroy_image = True
                                create_image = True
                                rebuild_inventory = True
                    else:
                        clicked_item = grid.item_at_position(cell)
                        if clicked_item is not None:
                            grid.remove(clicked_item)
                            gs.get_instance().player_state().held_item = clicked_item
                            create_image = True
                            rebuild_inventory = True

            else:  # we clicked in world
                world_pos = gs.get_instance().screen_to_world_coords(screen_pos)
                if ps.held_item is None:
                    clicked_item = self._get_entity_at_world_coords(world, world_pos, lambda x: x.is_item())
                    if clicked_item is not None:
                        world.remove(clicked_item)
                        ps.held_item = clicked_item.get_item()
                        create_image = True
                else:
                    p = world.get_player()
                    if p is not None:
                        p_center = p.center()  # drop position
                        drop_dir = Utils.sub(world_pos, p_center)
                        gs.get_instance().player_state().drop_held_item(p, world, direction=drop_dir)
                        destroy_image = True

        if input_state.was_pressed(gs.get_instance().settings().rotate_cw_key()) and ps.held_item is not None:
            ps.held_item = item_module.ItemFactory.rotate_item(ps.held_item)
            create_image = True
            destroy_image = True

        if destroy_image:
            self._destroy_panel(self.item_on_cursor_image, render_eng)
            self.item_on_cursor_image = None

        if create_image:
            size = ItemImage.calc_size(ps.held_item, 2)
            self.item_on_cursor_image = ItemImage(0, 0, ps.held_item, spriteref.UI_TOOLTIP_LAYER, 2)
            self.item_on_cursor_offs = (-size[0] // 2, -size[1] // 2)
            for bun in self.item_on_cursor_image.all_bundles():
                render_eng.update(bun)

        if rebuild_inventory:
            self.rebuild_inventory(render_eng)

        if self.item_on_cursor_image is not None:
            screen_pos = input_state.mouse_pos()
            if screen_pos is not None:
                x_offs = -screen_pos[0] - self.item_on_cursor_offs[0]
                y_offs = -screen_pos[1] - self.item_on_cursor_offs[1]
                render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, x_offs, y_offs)

    def rebuild_inventory(self, render_eng):
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                render_eng.remove(bun)

        self.inventory_panel = InventoryPanel()
        for bun in self.inventory_panel.all_bundles():
            render_eng.update(bun)

    def update(self, world, input_state, render_eng):
        self._update_item_on_cursor(world, input_state, render_eng)
        self._update_tooltip(world, input_state, render_eng)
        self._update_top_right_info_panel(world, input_state, render_eng)
        self._update_inventory_panel(world, input_state, render_eng)
        self._update_health_bar_panel(world, input_state, render_eng)
        self._update_dialog_panel(world, input_state, render_eng)
        self._update_world_ui_panel(world, input_state, render_eng)

        if len(gs.get_instance().get_cinematics_queue()) > 0:
            gs.get_instance().menu_manager().set_active_menu(CinematicMenu())

        elif input_state.was_pressed(gs.get_instance().settings().exit_key()):
            gs.get_instance().menu_manager().set_active_menu(PauseMenu())

    def cleanup(self):
        Menu.cleanup(self)
        self.inventory_panel = None
        self.item_on_cursor_image = None
        self.world_ui_panel = None
        self.top_right_info_panel = None

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                yield bun
        if self.health_bar_panel is not None:
            for bun in self.health_bar_panel.all_bundles():
                yield bun
        if self.top_right_info_panel is not None:
            for bun in self.top_right_info_panel.all_bundles():
                yield bun
        if self.world_ui_panel is not None:
            for bun in self.world_ui_panel.all_bundles():
                yield bun
        if self.item_on_cursor_image is not None:
            for bun in self.item_on_cursor_image.all_bundles():
                yield bun
        if self.dialog_panel is not None:
            for bun in self.dialog_panel.all_bundles():
                yield bun