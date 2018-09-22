import random

from src.game import spriteref as spriteref, inputs as inputs
from src.items import item as item_module
from src.ui.tooltips import TooltipFactory
from src.ui.ui import HealthBarPanel, InventoryPanel, CinematicPanel, TextImage, ItemImage, DialogPanel
from src.utils.util import Utils
from src.world.entities import ItemEntity, PickupEntity


class MenuManager:

    DEATH_MENU = 0
    IN_GAME_MENU = 1
    START_MENU = 2
    CINEMATIC_MENU = 3

    def __init__(self, menu_id):
        self._active_menu = self._get_menu(menu_id)
        self._next_active_menu_id = menu_id

    def update(self, world, gs, input_state, render_eng):
        if self._next_active_menu_id is not None:
            for bun in self._active_menu.all_bundles():
                render_eng.remove(bun)

            self._active_menu.cleanup()

            self._active_menu = self._get_menu(self._next_active_menu_id)
            self._next_active_menu_id = None
            if not self.should_draw_world():
                render_eng.set_clear_color(*self._active_menu.get_clear_color())

        menu = self.get_active_menu()
        menu.update(world, gs, input_state, render_eng)

    def _get_menu(self, menu_id):
        if menu_id == MenuManager.DEATH_MENU:
            return DeathMenu()
        elif menu_id == MenuManager.IN_GAME_MENU:
            return InGameUiState()
        elif menu_id == MenuManager.START_MENU:
            return StartMenu()
        elif menu_id == MenuManager.CINEMATIC_MENU:
            return CinematicMenu()
        raise ValueError("Unknown menu id: " + str(menu_id))

    def should_draw_world(self):
        return self._active_menu.keep_drawing_world_underneath()

    def get_active_menu(self):
        return self._active_menu

    def set_active_menu(self, menu_id):
        if menu_id is None:
            raise ValueError("Can't set null menu")
        self._next_active_menu_id = menu_id


class Menu:

    def __init__(self, menu_type):
        self._menu_type = menu_type
        self._active_tooltip = None

    def get_clear_color(self):
        return (0.5, 0.5, 0.5)

    def get_type(self):
        return self._menu_type

    def update(self, world, gs, input_state, render_eng):
        pass

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


class StartMenu(Menu):
    START_OPT = 0
    OPTIONS_OPT = 1
    EXIT_OPT = 2

    def __init__(self):
        Menu.__init__(self, MenuManager.START_MENU)
        self._title_img = None
        self._num_options = 3
        self._option_imgs = [None] * self._num_options
        self._selection = 0

        self._title_pos = (0, 0)
        self._option_rects = [(0, 0, 0, 0)] * self._num_options

        self._build_imgs()

    def get_clear_color(self):
        return (0, 0, 0)

    def _build_imgs(self):
        if self._title_img is None:
            self._title_img = TextImage(0, 0, "cubelike", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=10)
        if self._option_imgs[0] is None:
            self._option_imgs[0] = TextImage(0, 0, "start", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)
        if self._option_imgs[1] is None:
            self._option_imgs[1] = TextImage(0, 0, "options", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)
        if self._option_imgs[2] is None:
            self._option_imgs[2] = TextImage(0, 0, "exit", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)

    def _handle_enter_press(self, gs):
        if self._selection == StartMenu.START_OPT:
            gs.new_game()
        elif self._selection == StartMenu.EXIT_OPT:
            gs.needs_exit = True
        elif self._selection == StartMenu.OPTIONS_OPT:
            pass  # TODO

    def _update_imgs(self):
        self._title_img.update(new_x=self._title_pos[0], new_y=self._title_pos[1])

        for i in range(0, self._num_options):
            color = (1, 0, 0) if self._selection == i else (1, 1, 1)
            x = self._option_rects[i][0]
            y = self._option_rects[i][1]
            self._option_imgs[i].update(new_x=x, new_y=y, new_color=color)

    def update(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.UP):
            self._selection = (self._selection - 1) % self._num_options
        if input_state.was_pressed(inputs.DOWN):
            self._selection = (self._selection + 1) % self._num_options
        if input_state.was_pressed(inputs.ENTER):
            self._handle_enter_press(gs)

        if input_state.mouse_in_window():
            pos = input_state.mouse_pos()
            if input_state.mouse_moved():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._selection = i

            if input_state.mouse_was_pressed():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._handle_enter_press(gs)
                        break

        screensize = gs.screen_size
        self._title_pos = (screensize[0] // 2 - self._title_img.size()[0] // 2,
                           screensize[1] // 3 - self._title_img.size()[1] // 2)
        gap = 16
        opt_y = screensize[1] // 2
        for i in range(0, self._num_options):
            self._option_rects[i] = (screensize[0] // 2 - self._option_imgs[i].size()[0] // 2,
                                     opt_y,
                                     self._option_imgs[i].size()[0],
                                     self._option_imgs[i].size()[1])
            opt_y += self._option_imgs[i].size()[1] + gap

        self._update_imgs()
        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun

        if self._title_img is not None:
            for bun in self._title_img.all_bundles():
                yield bun
        for opt_img in self._option_imgs:
            if opt_img is not None:
                for bun in opt_img.all_bundles():
                    yield bun


class CinematicMenu(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.CINEMATIC_MENU)
        self._next_menu = MenuManager.IN_GAME_MENU
        self.active_scene = None

        self.letter_reveal_speed = 3
        self.active_tick_count = 0  # how many ticks the current cinematic has been showing

        self.cinematic_panel = None

    def update(self, world, gs, input_state, render_eng):
        if self.active_scene is None:
            cine_queue = gs.get_cinematics_queue()
            if len(cine_queue) == 0:
                gs.get_menu_manager().set_active_menu(self._next_menu)
                return
            else:
                self.active_scene = cine_queue.pop(0)
                self.active_tick_count = 0

        if self.active_scene is not None:
            if self.cinematic_panel is None:
                self.cinematic_panel = CinematicPanel()

            img_idx = (gs.anim_tick // 2) % len(self.active_scene.images)
            current_image = self.active_scene.images[img_idx]
            num_chars_to_display = 1 + self.active_tick_count // self.letter_reveal_speed
            text_finished_scrolling = len(self.active_scene.text) <= num_chars_to_display
            full_text = self.active_scene.text

            if text_finished_scrolling:
                current_text = full_text
            else:
                current_text = full_text[0:num_chars_to_display]

            self.cinematic_panel.update(gs, render_eng, current_image, current_text)

            if self.active_tick_count > 10 and input_state.was_pressed(inputs.INTERACT):
                if text_finished_scrolling:
                    self.active_scene = None
                else:
                    self.active_tick_count = len(full_text) * self.letter_reveal_speed

            self.active_tick_count += 1

        for bun in self.all_bundles():
            render_eng.update(bun)

    def get_clear_color(self):
        return (0.0, 0.0, 0.0)

    def set_next_menu(self, next_menu_id):
        self._next_menu = next_menu_id

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.cinematic_panel is not None:
            for bun in self.cinematic_panel.all_bundles():
                yield bun


class DeathMenu(Menu):
    RETRY_OPT = 0
    EXIT_OPT = 1

    def __init__(self):
        Menu.__init__(self, MenuManager.DEATH_MENU)
        self._you_died_img = None
        self._flavor_img = None

        self._num_options = 2
        self._option_imgs = [None] * self._num_options
        self._selection = 0

        self._title_pos = (0, 0)
        self._flavor_pos = (0, 0)
        self._option_rects = [(0, 0, 0, 0)] * self._num_options

        self._showing_flavor = True
        self._flavor_duration = 100
        self._flavor_tick = 0
        self._flavor_text = self._get_flavor_text()

        self._build_imgs()

    def get_flavor_progress(self):
        return Utils.bound(self._flavor_tick / self._flavor_duration, 0.0, 1.0)

    def get_clear_color(self):
        return (0.0, 0.0, 0.0)

    ALL_FLAVOR = [
        "you'll do better next time!",
        "epic run!",
        "ouch!"
    ]

    def _get_flavor_text(self):
        idx = int(random.random() * len(DeathMenu.ALL_FLAVOR))
        return DeathMenu.ALL_FLAVOR[idx]

    def _build_imgs(self):
        if self._you_died_img is None:
            self._you_died_img = TextImage(0, 0, "game over", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=6)
        if self._flavor_img is None:
            self._flavor_img = TextImage(0, 0, self._flavor_text, layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=2)
        if self._option_imgs[0] is None:
            self._option_imgs[0] = TextImage(0, 0, "retry", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)
        if self._option_imgs[1] is None:
            self._option_imgs[1] = TextImage(0, 0, "quit", layer=spriteref.UI_0_LAYER, color=(1, 1, 1), scale=3)

    def _update_imgs(self):
        if self.get_flavor_progress() < 0.15:
            c = self.get_flavor_progress() / 0.15
            color = (c, c, c)  # fade in
        else:
            color = (1, 1, 1)
        self._flavor_img.update(new_x=self._flavor_pos[0], new_y=self._flavor_pos[1], new_color=color)

        self._you_died_img.update(new_x=self._title_pos[0], new_y=self._title_pos[1])
        for i in range(0, self._num_options):
            color = (1, 0, 0) if self._selection == i else (1, 1, 1)
            x = self._option_rects[i][0]
            y = self._option_rects[i][1]
            self._option_imgs[i].update(new_x=x, new_y=y, new_color=color)

    def update(self, world, gs, input_state, render_eng):
        if input_state.was_pressed(inputs.UP):
            self._selection = (self._selection - 1) % self._num_options
        if input_state.was_pressed(inputs.DOWN):
            self._selection = (self._selection + 1) % self._num_options
        if input_state.was_pressed(inputs.ENTER):
            self._handle_enter_press(gs)

        if input_state.mouse_in_window():
            pos = input_state.mouse_pos()
            if input_state.mouse_moved():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._selection = i

            if input_state.mouse_was_pressed():
                for i in range(0, self._num_options):
                    if Utils.rect_contains(self._option_rects[i], pos):
                        self._handle_enter_press(gs)
                        break

        screensize = gs.screen_size
        flv_size = self._flavor_img.size()
        self._flavor_pos = (screensize[0] // 2 - flv_size[0] // 2,
                            screensize[1] // 2 - flv_size[1] // 2)

        gap = 32
        total_height = self._you_died_img.size()[1]
        for img in self._option_imgs:
            total_height += img.size()[1] + gap

        total_width = self._you_died_img.size()[0]

        x_pos = screensize[0] // 2 - total_width // 2
        y_pos = screensize[1] // 2 - total_height // 2

        self._title_pos = (x_pos, y_pos)
        y_pos += self._you_died_img.size()[1] + gap

        for i in range(0, self._num_options):
            opt_size = self._option_imgs[i].size()
            x_pos = screensize[0] // 2 - opt_size[0] // 2
            self._option_rects[i] = (x_pos, y_pos, opt_size[0], opt_size[1])

            y_pos += opt_size[1] + gap

        self._update_imgs()

        if self._showing_flavor and self.get_flavor_progress() == 1.0:
            self._showing_flavor = False
            for bun in self._flavor_img.all_bundles():
                render_eng.remove(bun)
        elif self._showing_flavor:
            self._flavor_tick += 1

        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self._showing_flavor:
            if self._flavor_img is not None:
                for bun in self._flavor_img.all_bundles():
                    yield bun
        else:
            if self._you_died_img is not None:
                for bun in self._you_died_img.all_bundles():
                    yield bun
            for opt_img in self._option_imgs:
                if opt_img is not None:
                    for bun in opt_img.all_bundles():
                        yield bun

    def _handle_enter_press(self, gs):
        if self.get_flavor_progress() < 1:
            self._flavor_tick = self._flavor_duration
        else:
            sel = self._selection
            if sel == DeathMenu.RETRY_OPT:
                gs.new_game()
            elif sel == DeathMenu.EXIT_OPT:
                gs.get_menu_manager().set_active_menu(MenuManager.START_MENU)


class InGameUiState(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.IN_GAME_MENU)
        self.inventory_panel = None
        self.health_bar_panel = None
        self.dialog_panel = None

        self.item_on_cursor = None
        self.item_on_cursor_offs = [0, 0]
        self.item_on_cursor_image = None

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

    def _update_tooltip(self, world, gs, input_state, render_eng):
        needs_update = False
        obj_to_display = None
        screen_pos = input_state.mouse_pos()

        if input_state.mouse_in_window() and self.item_on_cursor is None:
            if self.in_inventory_panel(screen_pos):
                grid_n_cell = self.get_clicked_inventory_grid_and_cell(screen_pos)
                if grid_n_cell is not None:
                    grid, cell = grid_n_cell
                    obj_to_display = grid.item_at_position(cell)
            else:
                world_pos = gs.screen_to_world_coords(screen_pos)
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

        if gs.player_state().is_dead() or obj_to_display is None:
            self.set_active_tooltip(None, render_eng)

    def _update_dialog_panel(self, world, gs, input_state, render_eng):
        should_destroy = (self.dialog_panel is not None and (not gs.dialog_manager().is_active() or
                          self.dialog_panel.get_dialog() is not gs.dialog_manager().get_dialog()))

        if should_destroy:
            self._destroy_panel(self.dialog_panel, render_eng)
            self.dialog_panel = None

        if gs.dialog_manager().is_active():
            if self.dialog_panel is None:
                dialog = gs.dialog_manager().get_dialog()
                self.dialog_panel = DialogPanel(dialog)

        if self.dialog_panel is not None:
            self.dialog_panel.update(gs, render_eng)

    def _update_inventory_panel(self, world, gs, input_state, render_eng):
        if gs.player_state().is_dead():
            if self.inventory_panel is not None:
                self._destroy_panel(self.inventory_panel, render_eng)
                self.inventory_panel = None

        elif input_state.was_pressed(inputs.INVENTORY):
            if self.inventory_panel is None:
                self.rebuild_inventory(gs, render_eng)
            else:
                self._destroy_panel(self.inventory_panel, render_eng)
                self.inventory_panel = None

        elif self.inventory_panel is not None and self.inventory_panel.gs_info_is_outdated(gs):
            self.rebuild_inventory(gs, render_eng)

    def _update_health_bar_panel(self, world, gs, input_state, render_eng):
        if self.health_bar_panel is None:
            self.health_bar_panel = HealthBarPanel()
        self.health_bar_panel.update(world, gs, input_state, render_eng)

    def in_inventory_panel(self, screen_pos):
        if self.inventory_panel is None:
            return False
        else:
            return Utils.rect_contains(self.inventory_panel.total_rect, screen_pos)

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

    def _update_item_on_cursor(self, world, gs, input_state, render_eng):
        destroy_image = False
        create_image = False
        rebuild_inventory = False

        if gs.player_state().is_dead():
            destroy_image = True
            if self.item_on_cursor is not None:
                center = gs.screen_size[0] // 2, gs.screen_size[1] // 2
                world_coords = gs.screen_to_world_coords(center)
                self._drop_item_on_cursor(world_coords, Utils.rand_vec(1), world)

        elif not input_state.mouse_in_window():
            destroy_image = True

        elif self.item_on_cursor is not None and self.item_on_cursor_image is None:
            # mouse left window and came back
            create_image = True

        elif input_state.mouse_was_pressed():
            screen_pos = input_state.mouse_pos()

            if self.in_inventory_panel(screen_pos):
                if self.item_on_cursor is not None:
                    # when holding an item, gotta offset the click to the top left corner
                    grid_click_pos = Utils.add(screen_pos, self.item_on_cursor_offs)
                    grid_click_pos = Utils.add(grid_click_pos, (16, 16))  # plus some fudge XXX
                else:
                    grid_click_pos = screen_pos

                clicked_grid_n_cell = self.get_clicked_inventory_grid_and_cell(grid_click_pos)
                if clicked_grid_n_cell is not None:
                    grid = clicked_grid_n_cell[0]
                    cell = clicked_grid_n_cell[1]
                    if self.item_on_cursor is not None:
                        if grid.can_place(self.item_on_cursor, cell):
                            grid.place(self.item_on_cursor, cell)
                            self.item_on_cursor = None
                            destroy_image = True
                            rebuild_inventory = True
                        else:
                            replaced_with = grid.try_to_replace(self.item_on_cursor, cell)
                            if replaced_with is not None:
                                self.item_on_cursor = replaced_with
                                destroy_image = True
                                create_image = True
                                rebuild_inventory = True
                    else:
                        clicked_item = grid.item_at_position(cell)
                        if clicked_item is not None:
                            grid.remove(clicked_item)
                            self.item_on_cursor = clicked_item
                            create_image = True
                            rebuild_inventory = True

            else:  # we clicked in world
                world_pos = gs.screen_to_world_coords(screen_pos)
                if self.item_on_cursor is None:
                    clicked_item = self._get_entity_at_world_coords(world, world_pos, lambda x: x.is_item())
                    if clicked_item is not None:
                        world.remove(clicked_item)
                        self.item_on_cursor = clicked_item.get_item()
                        create_image = True
                else:
                    p = world.get_player()
                    if p is not None:
                        p_center = p.center()  # drop position
                        drop_dir = Utils.sub(world_pos, p_center)
                        self._drop_item_on_cursor(p_center, drop_dir, world)
                        destroy_image = True

        if input_state.was_pressed(inputs.ROTATE_CW) and self.item_on_cursor is not None:
            self.item_on_cursor = item_module.ItemFactory.rotate_item(self.item_on_cursor)
            create_image = True
            destroy_image = True

        if destroy_image:
            self._destroy_panel(self.item_on_cursor_image, render_eng)
            self.item_on_cursor_image = None

        if create_image:
            size = ItemImage.calc_size(self.item_on_cursor, 2)
            self.item_on_cursor_image = ItemImage(0, 0, self.item_on_cursor, spriteref.UI_TOOLTIP_LAYER, 2)
            self.item_on_cursor_offs = (-size[0] // 2, -size[1] // 2)
            for bun in self.item_on_cursor_image.all_bundles():
                render_eng.update(bun)

        if rebuild_inventory:
            self.rebuild_inventory(gs, render_eng)

        if self.item_on_cursor_image is not None:
            screen_pos = input_state.mouse_pos()
            if screen_pos is not None:
                x_offs = -screen_pos[0] - self.item_on_cursor_offs[0]
                y_offs = -screen_pos[1] - self.item_on_cursor_offs[1]
                render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, x_offs, y_offs)

    def _drop_item_on_cursor(self, pos, drop_dir, world):
        if self.item_on_cursor is None:
            return
        vel = PickupEntity.rand_vel(direction=drop_dir)
        item_entity = ItemEntity(self.item_on_cursor, *pos, vel=vel)
        world.add(item_entity)
        self.item_on_cursor = None

    def rebuild_inventory(self, gs, render_eng):
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                render_eng.remove(bun)

        self.inventory_panel = InventoryPanel(gs)
        for bun in self.inventory_panel.all_bundles():
            render_eng.update(bun)

    def update(self, world, gs, input_state, render_eng):
        # TODO - need to better organize this mess
        self._update_item_on_cursor(world, gs, input_state, render_eng)
        self._update_tooltip(world, gs, input_state, render_eng)
        self._update_inventory_panel(world, gs, input_state, render_eng)
        self._update_health_bar_panel(world, gs, input_state, render_eng)
        self._update_dialog_panel(world, gs, input_state, render_eng)

    def cleanup(self):
        Menu.cleanup(self)
        self.inventory_panel = None
        self.item_on_cursor_image = None
        self.item_on_cursor = None  # XXX this will DESTROY the item on cursor

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.health_bar_panel is not None:
            for bun in self.health_bar_panel.all_bundles():
                yield bun
        if self.inventory_panel is not None:
            for bun in self.inventory_panel.all_bundles():
                yield bun
        if self.item_on_cursor_image is not None:
            for bun in self.item_on_cursor_image.all_bundles():
                yield bun
        if self.dialog_panel is not None:
            for bun in self.dialog_panel.all_bundles():
                yield bun