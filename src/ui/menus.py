import random

import pygame

import src.game.spriteref as spriteref
import src.game.soundref as soundref
from src.items import item as item_module
from src.ui.tooltips import TooltipFactory
from src.ui.ui import HealthBarPanel, InventoryPanel, MapPanel, SidePanelTypes, CinematicPanel, TextImage, ItemImage, DialogPanel
from src.renderengine.img import ImageBundle
from src.utils.util import Utils
import src.game.events as events
import src.game.music as music
import src.game.settings as settings
import src.game.globalstate as gs
import src.game.sound_effects as sound_effects
from src.renderengine.engine import RenderEngine
from src.game.inputs import InputState
import src.utils.colors as colors
import src.game.gameengine as gameengine
import src.game.version as version
import src.game.savedata as savedata
import src.game.constants as constants


class MenuManager:

    DEATH_MENU = 0
    DEATH_OPTION_MENU = 0.5
    IN_GAME_MENU = 1
    START_MENU = 2

    LOAD_MENU = 2.5
    LOAD_INFO_MENU = 2.75
    REALLY_DELETE_SAVE_FILE_MENU = 2.85

    CINEMATIC_MENU = 3  # not used anymore
    PAUSE_MENU = 4
    CONTROLS_MENU = 5
    KEYBINDING_MENU = 7

    DEBUG_MENU = 8
    DEBUG_SETTINGS_MENU = 8.25
    DEBUG_ZONE_SELECT_MENU = 8.75

    SETTINGS_MENU = 9
    TEXT_MENU = 10
    TITLE_MENU = 11
    REALLY_QUIT = 12
    YOU_WIN_MENU = 13
    CREDITS_MENU = 14

    HIGH_SCORES = 15

    def __init__(self, menu):
        self._active_menu = TitleMenu()
        self._next_active_menu = menu

    def update(self):
        render_eng = RenderEngine.get_instance()
        world = gs.get_instance().get_world()

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
                c_xy = self.get_active_menu().get_camera_center_point_on_screen()
                if c_xy is not None:
                    gs.get_instance().set_camera_center_on_screen(c_xy[0], c_xy[1])

        else:
            if world is None and self.should_draw_world():
                # expected sometimes~
                pass
            else:
                self.get_active_menu().update(world)

                c_xy = self.get_active_menu().get_camera_center_point_on_screen()
                if c_xy is not None:
                    cur_center = gs.get_instance().get_camera_center_on_screen()
                    if cur_center != c_xy:
                        if Utils.dist(c_xy, cur_center) <= 2:
                            gs.get_instance().set_camera_center_on_screen(c_xy[0], c_xy[1])
                        else:
                            new_center = Utils.round(Utils.linear_interp(cur_center, c_xy, 0.12))
                            gs.get_instance().set_camera_center_on_screen(new_center[0], new_center[1])

                input_state = InputState.get_instance()
                if input_state.mouse_in_window():
                    xy = input_state.mouse_pos()
                    cursor = self.get_active_menu().cursor_style_at(world, xy)
                else:
                    # this matters on mac because you continue controlling the cursor's image
                    # as long as the window has focus, even after the cursor has left.
                    cursor = spriteref.UI.Cursors.arrow_cursor

                if cursor is None:
                    pygame.mouse.set_cursor(*spriteref.UI.Cursors.invisible_cursor)
                else:
                    pygame.mouse.set_cursor(*cursor)

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

    def set_active_menu(self, menu):
        if menu is None:
            raise ValueError("Can't set null menu")

        self._next_active_menu = menu

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
        return (0, 0, 0)

    def get_type(self):
        return self._menu_type

    def update(self, world):
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

    def get_camera_center_point_on_screen(self):
        return None

    def get_active_tooltip(self):
        return self._active_tooltip

    def set_active_tooltip(self, tooltip):
        if self._active_tooltip is not None:
            self._destroy_panel(self._active_tooltip)
        self._active_tooltip = tooltip

    def _destroy_panel(self, panel):
        if panel is not None:
            bundles = panel.all_bundles()
            RenderEngine.get_instance().clear_bundles(bundles)

    def cursor_style_at(self, world, xy):
        return pygame.cursors.arrow


class OptionsMenu(Menu):

    def __init__(self, menu_id, title, options, title_size=2.0):
        """
        title: text or sprite
        title_size: scale of title text or sprite
        options: list of strings, or tuples of strings
        """
        Menu.__init__(self, menu_id)

        if isinstance(title, str):
            self.title_text = title
            self.title_sprite = None
        else:
            self.title_sprite = title
            self.title_text = None

        self.title_size = title_size

        self.options_text = []
        for opt in options:
            if isinstance(opt, str):
                self.options_text.append((opt,))
            elif isinstance(opt, (tuple, list)):
                self.options_text.append(tuple(opt))
            else:
                raise ValueError("illegal option type: {}".format(opt))

        self._title_img = None
        self._title_rect = None    # tuple(x, y, w, h)

        self._option_rects = {}  # (int, int) -> tuple(x, y, w, h)
        self._option_imgs = {}   # (int, int) -> ImgBundle

        for r in range(0, self.get_num_option_rows()):
            for c in range(0, self.get_row_size(r)):
                self._option_rects[(r, c)] = None
                self._option_imgs[(r, c)] = None

        self._selection = (0, 0)  # row, column
        self._hidden_c = 0  # col

        self._first_frame_active = True

    def get_clear_color(self):
        return (0, 0, 0)

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def get_title_color(self):
        return (1, 1, 1)

    def get_spacing(self):
        return 4

    def get_title_spacing(self):
        return self.get_spacing() * 3

    def get_enabled(self, idx):
        return True

    def get_option_color(self, idx):
        if self.get_enabled(idx):
            if idx == self._selection:
                return (1, 0, 0)
            else:
                return colors.WHITE
        else:
            return colors.DARK_GRAY

    def get_option_text(self, idx):
        if self.has_option_at(idx):
            return self.options_text[idx[0]][idx[1]]
        else:
            return None

    def has_option_at(self, idx):
        if 0 <= idx[0] < self.get_num_option_rows():
            return 0 <= idx[1] < self.get_row_size(idx[0])
        else:
            return False

    def get_num_option_rows(self):
        return len(self.options_text)

    def get_row_size(self, r):
        return len(self.options_text[r])

    def build_images(self):
        self.build_title_img()
        self.build_option_imgs()

    def build_title_img(self):
        if self.title_text is not None:
            if self._title_img is None:
                self._title_img = TextImage(0, 0, self.title_text, layer=spriteref.UI_0_LAYER,
                                            color=self.get_title_color(), scale=self.title_size, x_kerning=0)
        elif self.title_sprite is not None:
            if self._title_img is None:
                self._title_img = ImageBundle(self.title_sprite, 0, 0, spriteref.UI_0_LAYER,
                                              color=self.get_title_color(), scale=self.title_size)

    def build_option_imgs(self):
        for r in range(0, self.get_num_option_rows()):
            for c in range(0, self.get_row_size(r)):
                idx = (r, c)
                if self._option_imgs[idx] is None:
                    self._option_imgs[idx] = TextImage(0, 0, self.get_option_text(idx), layer=spriteref.UI_0_LAYER,
                                                       color=self.get_option_color(idx), scale=1, x_kerning=0)

    def layout_rects(self):
        if self._title_rect is None:
            self._title_rect = (0, 0, 0, 0)

        total_height = 0
        if self._title_img is not None:
            total_height += self._title_img.size()[1] + self.get_title_spacing()
        for r in range(0, self.get_num_option_rows()):
            row_h = 0
            for c in range(0, self.get_row_size(r)):
                opt_img = self._option_imgs[(r, c)]
                if opt_img is not None:
                    row_h = max(row_h, opt_img.size()[1] + self.get_spacing())
            total_height += row_h

        total_height -= self.get_spacing()

        y_pos = RenderEngine.get_instance().get_game_size()[1] // 2 - total_height // 2
        if self._title_img is not None:
            title_x = RenderEngine.get_instance().get_game_size()[0] // 2 - self._title_img.size()[0] // 2
            self._title_rect = (title_x, y_pos, self._title_img.size()[0], self._title_img.size()[1])
            y_pos += self._title_img.size()[1] + self.get_title_spacing()

        # TODO add support for grid-style layouts
        for r in range(0, self.get_num_option_rows()):
            row_width = 0
            for c in range(0, self.get_row_size(r)):
                idx = (r, c)
                if self._option_imgs[idx] is not None:
                    row_width += self._option_imgs[idx].size()[0]

            opt_x = RenderEngine.get_instance().get_game_size()[0] // 2 - row_width // 2
            row_h = 0
            for c in range(0, self.get_row_size(r)):
                idx = (r, c)
                if self._option_imgs[idx] is not None:
                    self._option_rects[idx] = (opt_x, y_pos, self._option_imgs[idx].size()[0], self._option_imgs[idx].size()[1])
                    opt_x += self._option_imgs[idx].size()[0]
                    row_h = max(row_h, self._option_imgs[idx].size()[1] + self.get_spacing())

            y_pos += row_h

    def update_imgs(self):
        if self._title_img is not None:
            x = self._title_rect[0]
            y = self._title_rect[1]
            self._title_img = self._title_img.update(new_x=x, new_y=y, new_color=self.get_title_color())

        for r in range(0, self.get_num_option_rows()):
            for c in range(0, self.get_row_size(r)):
                idx = (r, c)
                color = self.get_option_color(idx)
                if self._option_rects[idx] is not None and self._option_imgs[idx] is not None:
                    x = self._option_rects[idx][0]
                    y = self._option_rects[idx][1]
                    self._option_imgs[idx] = self._option_imgs[idx].update(new_x=x, new_y=y,
                                                                           new_text=self.get_option_text(idx), new_color=color)

    def all_idxes(self):
        for r in range(0, self.get_num_option_rows()):
            for c in range(0, self.get_row_size(r)):
                yield (r, c)

    def set_selected(self, idx, forcefully=False, _soft_c=False):
        if not self.has_option_at(idx):
            return

        if not self.get_enabled(idx) and not forcefully:
            return

        if idx != self._selection:
            sound_effects.play_sound(soundref.menu_move)
            self._selection = idx

        if not _soft_c:
            self._hidden_c = idx[1]

    def get_selected_idx(self):
        return self._selection

    def _move_selection(self, cur_selection, dx, dy):
        if dy != 0:
            best_selection = None
            best_dist = (float('inf'), float('inf'))
            for sel in self.all_idxes():
                if not self.get_enabled(sel) or sel == cur_selection:
                    continue
                r_dist = abs((cur_selection[0] + dy) - sel[0]) % self.get_num_option_rows()
                c_dist = abs(self._hidden_c - sel[1])
                if best_dist is None or r_dist < best_dist[0] or (r_dist == best_dist[0] and c_dist < best_dist[1]):
                    best_selection = sel
                    best_dist = (r_dist, c_dist)

            if best_selection is not None:
                self.set_selected(best_selection, _soft_c=True)
                return True

        elif dx != 0:
            cur_r = cur_selection[0]
            cur_c = cur_selection[1]
            for i in range(1, self.get_row_size(cur_selection[0])):
                new_sel = (cur_r, cur_c + dx * i)
                if self.has_option_at(new_sel) and self.get_enabled(new_sel):
                    self.set_selected(new_sel)
                    return True

        return False

    def handle_inputs(self, world):
        input_state = InputState.get_instance()
        if input_state.was_pressed(gs.get_instance().settings().exit_key()):
            self.esc_pressed()
        else:
            dy = 0
            up_pressed = input_state.was_pressed(gs.get_instance().settings().menu_up_key())
            up_pressed = up_pressed or input_state.was_pressed(gs.get_instance().settings().up_key())
            if up_pressed:
                dy -= 1

            down_pressed = input_state.was_pressed(gs.get_instance().settings().menu_down_key())
            down_pressed = down_pressed or input_state.was_pressed(gs.get_instance().settings().down_key())
            if down_pressed:
                dy += 1

            dx = 0
            left_pressed = input_state.was_pressed(gs.get_instance().settings().menu_left_key())
            left_pressed = left_pressed or input_state.was_pressed(gs.get_instance().settings().left_key())
            if left_pressed:
                dx -= 1

            right_pressed = input_state.was_pressed(gs.get_instance().settings().menu_right_key())
            right_pressed = right_pressed or input_state.was_pressed(gs.get_instance().settings().right_key())
            if right_pressed:
                dx += 1

            self._move_selection(self._selection, dx, dy)

            if input_state.was_pressed(gs.get_instance().settings().enter_key()):
                if self.get_enabled(self._selection):
                    self.option_activated(self._selection)
                else:
                    sound_effects.play_sound(soundref.menu_back)

            if self._option_rects is None:
                return

            if input_state.mouse_in_window():
                pos = input_state.mouse_pos()
                if input_state.mouse_moved() or self._first_frame_active:
                    for idx in self.all_idxes():
                        if self._option_rects[idx] is not None and Utils.rect_contains(self._option_rects[idx], pos):
                            self.set_selected(idx, forcefully=True)

                if input_state.mouse_was_pressed():
                    clicked_option = None

                    selected_rect = self._option_rects[self._selection]
                    if selected_rect is not None:
                        # give click priority to the thing that's selected
                        bigger_rect = Utils.rect_expand(selected_rect,
                                                        left_expand=5, right_expand=5,
                                                        up_expand=5, down_expand=5)
                        if Utils.rect_contains(bigger_rect, pos):
                            clicked_option = self._selection

                    if clicked_option is None:
                        # if the mouse hasn't moved yet on this menu, gotta catch those clicks too
                        for idx in self.all_idxes():
                            if self._option_rects[idx] is not None and Utils.rect_contains(self._option_rects[idx], pos):
                                clicked_option = idx
                                break

                    if clicked_option is not None:
                        if self.get_enabled(clicked_option):
                            self.option_activated(clicked_option)
                        else:
                            pass  # TODO sound effect

        self._first_frame_active = False

    def update(self, world):
        self.build_images()
        self.layout_rects()
        self.update_imgs()

        self.handle_inputs(world)

        render_eng = RenderEngine.get_instance()
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
            for idx in self._option_imgs:
                if self._option_imgs[idx] is not None:
                    for bun in self._option_imgs[idx].all_bundles():
                        yield bun

    def cursor_style_at(self, world, xy):
        return super().cursor_style_at(world, xy)


class OptionsMenuWithTextBlurb(OptionsMenu):

    def __init__(self, menu_id, title, options, title_size=2.0, info_text_size=1):
        OptionsMenu.__init__(self, menu_id, title, options, title_size=title_size)

        self._info_text_size = info_text_size
        self._info_text_imgs = []
        self._info_text_rects = []

    def get_blurb_text(self):
        return "Here's some info.\nOn multiple lines, no less."

    def get_blurb_text_color(self, i=-1):
        return colors.WHITE

    def get_title_spacing(self):
        if len(self._info_text_imgs) == 0:
            return super().get_title_spacing()
        else:
            # make room for the info
            total_h = 0
            for i in range(0, len(self._info_text_imgs)):
                text_img = self._info_text_imgs[i]
                total_h += text_img.h()
                total_h += self.get_spacing() if i < len(self._info_text_imgs) - 1 else super().get_title_spacing()

            return super().get_title_spacing() + total_h

    def build_images(self):
        super().build_images()
        blurbs = Utils.listify(self.get_blurb_text())
        while len(self._info_text_imgs) < len(blurbs):
            self._info_text_imgs.append(TextImage(0, 0, " ", spriteref.UI_0_LAYER, scale=self._info_text_size))

        r_engine = RenderEngine.get_instance()
        while len(self._info_text_imgs) > len(blurbs):
            to_rem = self._info_text_imgs.pop()
            for bun in to_rem.all_bundles():
                r_engine.remove(bun)

        for i in range(0, len(self._info_text_imgs)):
            text_blurb = blurbs[i]
            self._info_text_imgs[i] = self._info_text_imgs[i].update(new_text=text_blurb)

    def layout_rects(self):
        super().layout_rects()

        title_rect = (0, 0, 0, 0) if self._title_rect is None else self._title_rect
        cur_y = title_rect[1] + title_rect[3] + super().get_title_spacing()

        self._info_text_rects.clear()

        for i in range(0, len(self._info_text_imgs)):
            text_img = self._info_text_imgs[i]
            info_x = RenderEngine.get_instance().get_game_size()[0] // 2 - text_img.w() // 2
            self._info_text_rects.append((info_x, cur_y, text_img.w(), text_img.h()))

            cur_y += text_img.h()
            cur_y += self.get_spacing() if i < len(self._info_text_imgs) - 1 else super().get_title_spacing()

    def update_imgs(self):
        super().update_imgs()

        n_info_blurbs = min(len(self._info_text_imgs), len(self._info_text_rects))
        for i in range(0, n_info_blurbs):
            text_img = self._info_text_imgs[i]
            text_rect = self._info_text_rects[i]
            new_color = self.get_blurb_text_color(i=i)

            self._info_text_imgs[i] = text_img.update(new_x=text_rect[0], new_y=text_rect[1], new_color=new_color)

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for text_img in self._info_text_imgs:
            for bun in text_img.all_bundles():
                yield bun


class MenuWithVersionDisplay:

    def __init__(self):
        self._version_text = "[{}]".format(self.get_version_number_string())
        self._version_img = None
        self._version_rect = [0, 0, 0, 0]

    def get_version_number_string(self):
        return version.get_pretty_version_string()

    def build_version_images(self):
        if self._version_text is not None:
            if self._version_img is None:
                self._version_img = TextImage(0, 0, self._version_text, spriteref.UI_0_LAYER, scale=0.5, x_kerning=1)

    def layout_version_rects(self):
        if self._version_img is not None:
            scr_w, scr_h = RenderEngine.get_instance().get_game_size()
            x = scr_w - self._version_img.w() - 2
            y = scr_h - self._version_img.h() - 2
            self._version_rect = [x, y, self._version_img.w(), self._version_img.h()]

    def update_version_images(self):
        if self._version_img is not None:
            self._version_img = self._version_img.update(new_x=self._version_rect[0],
                                                         new_y=self._version_rect[1],
                                                         new_color=colors.LIGHT_GRAY)

    def all_bundles(self):
        if self._version_img is not None:
            for bun in self._version_img.all_bundles():
                yield bun


class StartMenu(OptionsMenu, MenuWithVersionDisplay):

    def __init__(self):
        has_save_data = savedata.has_files_on_disk()
        if not has_save_data:
            opts = ["start", "controls", "sound", "exit"]
            self._start_idx = (0, 0)
            self._load_idx = (-1, 0)
            self._options_idx = (1, 0)
            self._sound_idx = (2, 0)
            self._exit_idx = (3, 0)
        else:
            opts = ["start", "load game", "controls", "sound", "scores", "exit"]
            self._start_idx = (0, 0)
            self._load_idx = (1, 0)
            self._options_idx = (2, 0)
            self._sound_idx = (3, 0)
            self._high_scores_idx = (4, 0)
            self._exit_idx = (5, 0)

        OptionsMenu.__init__(self,
                             MenuManager.START_MENU,
                             spriteref.title_img,
                             opts,
                             title_size=3)

        MenuWithVersionDisplay.__init__(self)

    def build_images(self):
        super().build_images()
        MenuWithVersionDisplay.build_version_images(self)

    def layout_rects(self):
        super().layout_rects()
        MenuWithVersionDisplay.layout_version_rects(self)

    def update_imgs(self):
        super().update_imgs()
        MenuWithVersionDisplay.update_version_images(self)

    def get_song(self):
        return music.Songs.MENU_THEME

    def option_activated(self, idx):
        if idx == self._start_idx:
            gs.get_instance().add_event(events.NewGameEvent())
            sound_effects.play_sound(soundref.newgame_start)
        elif idx == self._exit_idx:
            gs.get_instance().add_event(events.GameExitEvent())
        elif idx == self._options_idx:
            gs.get_instance().menu_manager().set_active_menu(ControlsMenu(MenuManager.START_MENU))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == self._sound_idx:
            gs.get_instance().menu_manager().set_active_menu(SoundSettingsMenu(MenuManager.START_MENU))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == self._load_idx:
            gs.get_instance().menu_manager().set_active_menu(LoadMenu(reload_data=True))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == self._high_scores_idx:
            gs.get_instance().menu_manager().set_active_menu(HighScoresMenu(reload_data=True))
            sound_effects.play_sound(soundref.menu_select)

    def esc_pressed(self):
        gs.get_instance().menu_manager().set_active_menu(TitleMenu())
        sound_effects.play_sound(soundref.menu_back)

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for bun in MenuWithVersionDisplay.all_bundles(self):
            yield bun


class LoadMenu(OptionsMenu):

    FILES_PER_PAGE = 6

    def __init__(self, page=0, sel_idx=None, reload_data=True):

        self.page = page

        if reload_data:
            savedata.reload_all_save_data_from_disk()

        all_saves = savedata.get_all_in_progress_save_data(load_if_needed=False)

        start_idx = LoadMenu.FILES_PER_PAGE * page

        self.first_page = (page == 0)

        if start_idx >= len(all_saves):
            # this shouldn't happen...
            self.data_for_opts = []
            self.last_page = True
        elif start_idx + LoadMenu.FILES_PER_PAGE < len(all_saves):
            self.data_for_opts = all_saves[start_idx:start_idx + LoadMenu.FILES_PER_PAGE]
            self.last_page = False
        else:
            self.data_for_opts = all_saves[start_idx:]
            self.last_page = True

        self.opts = []
        for d in self.data_for_opts:
            self.opts.append(d.get_pretty_string(max_length=40))

        if len(all_saves) > LoadMenu.FILES_PER_PAGE:
            self.opts.append("next page")
            self.next_page_idx = (len(self.opts) - 1, 0)

            self.opts.append("prev page")
            self.prev_page_idx = (len(self.opts) - 1, 0)
        else:
            self.next_page_idx = (-1, 0)
            self.prev_page_idx = (-1, 0)

        self.opts.append("back")
        self.back_idx = (len(self.opts) - 1, 0)

        OptionsMenu.__init__(self, MenuManager.LOAD_MENU, "load game", self.opts)

        if sel_idx is not None:
            self.set_selected(sel_idx)

    def get_enabled(self, idx):
        if idx == self.prev_page_idx and self.first_page:
            return False
        elif idx == self.next_page_idx and self.last_page:
            return False
        else:
            return True

    def esc_pressed(self):
        self.option_activated(self.back_idx)

    def option_activated(self, idx):
        if idx == self.back_idx:
            gs.get_instance().menu_manager().set_active_menu(StartMenu())
            sound_effects.play_sound(soundref.menu_back)
        elif idx == self.next_page_idx:
            gs.get_instance().menu_manager().set_active_menu(LoadMenu(self.page + 1, reload_data=False))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == self.prev_page_idx:
            gs.get_instance().menu_manager().set_active_menu(LoadMenu(self.page - 1, reload_data=False))
            sound_effects.play_sound(soundref.menu_select)

        elif 0 <= idx[0] < len(self.data_for_opts):
            selected_data = self.data_for_opts[idx[0]]
            bring_me_back = lambda: LoadMenu(page=self.page, sel_idx=idx, reload_data=False)
            load_info_menu = LoadFileInfoMenu(selected_data, back_menu_builder=bring_me_back)
            gs.get_instance().menu_manager().set_active_menu(load_info_menu)
            sound_effects.play_sound(soundref.menu_select)


class LoadFileInfoMenu(OptionsMenuWithTextBlurb, MenuWithVersionDisplay):

    PLAY_IDX = (0, 0)
    DELETE_IDX = (1, 0)
    BACK_IDX = (2, 0)

    def __init__(self, save_blob, back_menu_builder=None):
        self.back_menu_builder = back_menu_builder
        self.save_blob = save_blob

        title = save_blob.get_pretty_string(max_length=40, include_elapsed_time=False, include_version_desc=False)

        OptionsMenuWithTextBlurb.__init__(self, MenuManager.LOAD_INFO_MENU, title,
                                          ["play", "delete", "back"],
                                          title_size=1.5)

        MenuWithVersionDisplay.__init__(self)

    def get_blurb_text(self):
        return [
            "{}".format(self.save_blob.get_pretty_last_modified_date()),

            "playtime: {}\n".format(self.save_blob.get_pretty_elapsed_time(show_hours_if_zero=True)) +
            "   kills: {}\n".format(self.save_blob.get(savedata.SaveDataTags.KILL_COUNT)) +
            "  deaths: {}\n".format(self.save_blob.get(savedata.SaveDataTags.DEATH_COUNT)) +
            "   turns: {}\n".format(self.save_blob.get(savedata.SaveDataTags.TURN_COUNT))
        ]

    def esc_pressed(self):
        self.option_activated(LoadFileInfoMenu.BACK_IDX)

    def option_activated(self, idx):
        if idx == LoadFileInfoMenu.PLAY_IDX:
            new_game_event = events.NewGameEvent(from_save_data=self.save_blob)
            gs.get_instance().add_event(new_game_event)
            sound_effects.play_sound(soundref.newgame_start)

        elif idx == LoadFileInfoMenu.DELETE_IDX:
            after_back = lambda: LoadFileInfoMenu(self.save_blob, back_menu_builder=self.back_menu_builder)

            def after_delete():
                if savedata.has_files_on_disk():
                    return LoadMenu(reload_data=True)
                else:
                    savedata.reload_all_save_data_from_disk()  # clear the deleted file from the cache
                    return StartMenu()

            really_del_menu = ReallyDeleteSaveFileMenu(self.save_blob, after_back, after_delete)
            gs.get_instance().menu_manager().set_active_menu(really_del_menu)
            sound_effects.play_sound(soundref.menu_select)

        elif idx == LoadFileInfoMenu.BACK_IDX:
            if self.back_menu_builder is not None:
                back_menu = self.back_menu_builder()
            else:
                back_menu = LoadMenu()
            gs.get_instance().menu_manager().set_active_menu(back_menu)
            sound_effects.play_sound(soundref.menu_back)

    def get_version_number_string(self):
        vers = self.save_blob.get(savedata.SaveDataTags.VERSION_NUM)
        return version.get_pretty_version_string(for_version=vers)

    def build_images(self):
        super().build_images()
        MenuWithVersionDisplay.build_version_images(self)

    def layout_rects(self):
        super().layout_rects()
        MenuWithVersionDisplay.layout_version_rects(self)

    def update_imgs(self):
        super().update_imgs()
        MenuWithVersionDisplay.update_version_images(self)

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for bun in MenuWithVersionDisplay.all_bundles(self):
            yield bun


class ReallyDeleteSaveFileMenu(OptionsMenu):

    DELETE_IDX = (0, 0)
    BACK_IDX = (1, 0)

    def __init__(self, save_blob, back_menu_builder, after_delete_menu_builder):
        OptionsMenu.__init__(self, MenuManager.REALLY_DELETE_SAVE_FILE_MENU,
                             "really delete?",
                             ["delete", "back"])
        self.save_blob = save_blob

        self.back_menu_builder = back_menu_builder
        self.after_delete_menu_builder = after_delete_menu_builder

    def esc_pressed(self):
        self.option_activated(ReallyDeleteSaveFileMenu.BACK_IDX)

    def option_activated(self, idx):
        if idx == ReallyDeleteSaveFileMenu.DELETE_IDX:
            print("INFO: deleting save file: {}".format(self.save_blob.filepath))
            res = savedata.delete_from_disk(self.save_blob)
            if res:
                after_delete_menu = self.after_delete_menu_builder()
                gs.get_instance().menu_manager().set_active_menu(after_delete_menu)
                sound_effects.play_sound(soundref.menu_select)
            else:
                sound_effects.play_sound(soundref.error)

        elif idx == ReallyDeleteSaveFileMenu.BACK_IDX:
            back_menu = self.back_menu_builder()
            gs.get_instance().menu_manager().set_active_menu(back_menu)
            sound_effects.play_sound(soundref.menu_back)


# TODO - make it so you can view the info of each run
class HighScoresMenu(OptionsMenuWithTextBlurb):
    _SCORES_PER_PAGE = 5

    def __init__(self, reload_data=True, page=0):
        if reload_data:
            savedata.reload_all_save_data_from_disk()

        import src.game.debug as debug
        do_filter = not debug.is_dev()

        all_scores = savedata.get_all_completed_save_data(load_if_needed=False, filter_non_standard_versions=do_filter)
        if len(all_scores) > HighScoresMenu._SCORES_PER_PAGE:
            self.page = Utils.bound(page, 0, len(all_scores) // HighScoresMenu._SCORES_PER_PAGE - 1)
            self._first_page = self.page == 0
            self._last_page = self.page == (len(all_scores) // HighScoresMenu._SCORES_PER_PAGE - 1)

            opts = []
            if not self._last_page:
                self._next_page_idx = (len(opts), 0)
                opts.append("next page")
            else:
                self._next_page_idx = (-1, 0)

            if not self._first_page:
                self._prev_page_idx = (len(opts), 0)
                opts.append("prev page")
            else:
                self._prev_page_idx = (-1, 0)

            self._back_idx = (len(opts), 0)
            opts.append("back")

            first_score_idx = self.page * HighScoresMenu._SCORES_PER_PAGE
            end_score_idx = min(first_score_idx + HighScoresMenu._SCORES_PER_PAGE, len(all_scores))
            self.scores_on_page = all_scores[first_score_idx:end_score_idx]
        else:
            opts = ["back"]
            self.page = 0
            self._first_page = True
            self._last_page = True
            self._next_page_idx = (-1, 0)
            self._prev_page_idx = (-1, 0)
            self._back_idx = (0, 0)
            self.scores_on_page = all_scores

        OptionsMenuWithTextBlurb.__init__(self, MenuManager.HIGH_SCORES, "high scores", opts)

    def get_blurb_text(self):
        if len(self.scores_on_page) == 0:
            return "no scores yet!"
        else:
            lines = []
            for i in range(0, len(self.scores_on_page)):
                save_blob = self.scores_on_page[i]
                n = self.page * HighScoresMenu._SCORES_PER_PAGE + i + 1
                if n < 10:
                    row_str = " {}. ".format(n)
                else:
                    row_str = "{}. ".format(n)

                row_str += "{}".format(save_blob.get_pretty_elapsed_time(show_hours_if_zero=True))

                row_str += " " + save_blob.get_pretty_last_modified_date()

                if not save_blob.has_standard_version():
                    vers_string = save_blob.get(savedata.SaveDataTags.VERSION_NUM)[3]
                    row_str += " ({})".format(vers_string)

                lines.append(row_str)

            return "\n".join(lines)

    def esc_pressed(self):
        self.option_activated(self._back_idx)

    def get_enabled(self, idx):
        if idx == self._prev_page_idx:
            return not self._first_page
        elif idx == self._next_page_idx:
            return not self._last_page
        else:
            return True

    def option_activated(self, idx):
        if idx == self._prev_page_idx:
            new_menu = HighScoresMenu(reload_data=False, page=self.page - 1)
            gs.get_instance().menu_manager().set_active_menu(new_menu)
            sound_effects.play_sound(soundref.menu_select)

        elif idx == self._next_page_idx:
            new_menu = HighScoresMenu(reload_data=False, page=self.page + 1)
            gs.get_instance().menu_manager().set_active_menu(new_menu)
            sound_effects.play_sound(soundref.menu_select)

        elif idx == self._back_idx:
            gs.get_instance().menu_manager().set_active_menu(StartMenu())
            sound_effects.play_sound(soundref.menu_back)


class PauseMenu(OptionsMenu, MenuWithVersionDisplay):

    CONTINUE_IDX = (0, 0)
    CONTROLS_IDX = (1, 0)
    SOUND_IDX = (2, 0)
    EXIT_IDX = (3, 0)

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.PAUSE_MENU, "paused", ["resume", "controls", "sound", "quit"])

        MenuWithVersionDisplay.__init__(self)

    def option_activated(self, idx):
        if idx == PauseMenu.EXIT_IDX:
            gs.get_instance().menu_manager().set_active_menu(ReallyQuitMenu())
            sound_effects.play_sound(soundref.menu_select)
        elif idx == PauseMenu.CONTROLS_IDX:
            gs.get_instance().menu_manager().set_active_menu(ControlsMenu(MenuManager.IN_GAME_MENU))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == PauseMenu.CONTINUE_IDX:
            gs.get_instance().menu_manager().set_active_menu(InGameUiState())
            sound_effects.play_sound(soundref.pause_out)
        elif idx == PauseMenu.SOUND_IDX:
            gs.get_instance().menu_manager().set_active_menu(SoundSettingsMenu(MenuManager.PAUSE_MENU))
            sound_effects.play_sound(soundref.menu_select)

    def esc_pressed(self):
        self.option_activated(PauseMenu.CONTINUE_IDX)

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def build_images(self):
        super().build_images()
        MenuWithVersionDisplay.build_version_images(self)

    def layout_rects(self):
        super().layout_rects()
        MenuWithVersionDisplay.layout_version_rects(self)

    def update_imgs(self):
        super().update_imgs()
        MenuWithVersionDisplay.update_version_images(self)

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for bun in MenuWithVersionDisplay.all_bundles(self):
            yield bun


class ReallyQuitMenu(OptionsMenu):

    EXIT_IDX = (0, 0)
    BACK = (1, 0)

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.REALLY_QUIT, "really quit?", ["quit", "back"])

    def option_activated(self, idx):
        OptionsMenu.option_activated(self, idx)
        if idx == ReallyQuitMenu.EXIT_IDX:
            gs.get_instance().add_event(events.QuitToStartMenuEvent())
            sound_effects.play_sound(soundref.game_quit)
        elif idx == ReallyQuitMenu.BACK:
            gs.get_instance().menu_manager().set_active_menu(PauseMenu())
            sound_effects.play_sound(soundref.menu_back)

    def esc_pressed(self):
        self.option_activated(ReallyQuitMenu.BACK)


class TextOnlyMenu(OptionsMenu):

    def __init__(self, text, next_menu, auto_advance_duration=None):
        OptionsMenu.__init__(self, MenuManager.TEXT_MENU, text, ["~hidden~"])
        self.next_menu = next_menu

        # to automatically advance the text menu
        self.count = 0
        self.auto_advance_duration = auto_advance_duration

    def get_clear_color(self):
        return (0, 0, 0)

    def get_option_color(self, idx):
        return self.get_clear_color()

    def handle_inputs(self, world):
        do_advance = InputState.get_instance().was_anything_pressed()

        if self.auto_advance_duration is not None:
            self.count += 1
            if self.count > self.auto_advance_duration:
                do_advance = True

        if do_advance:
            gs.get_instance().menu_manager().set_active_menu(self.next_menu)

            if self.next_menu.get_type() == MenuManager.IN_GAME_MENU:
                gs.get_instance().do_fade_sequence(1.0, 0.0, constants.STANDARD_FADE_DURATION)
                gs.get_instance().pause_world_updates(constants.STANDARD_FADE_DURATION // 2)


class SoundSettingsMenu(OptionsMenu):

    MUSIC_TOGGLE_IDX = (0, 0)
    MUSIC_VOLUME_DOWN_IDX = (0, 1)
    MUSIC_VOLUME_UP_IDX = (0, 2)

    EFFECTS_TOGGLE_IDX = (1, 0)
    EFFECTS_VOLUME_DOWN_IDX = (1, 1)
    EFFECTS_VOLUME_UP_IDX = (1, 2)

    BACK_IDX = (2, 0)

    def __init__(self, prev_id):
        OptionsMenu.__init__(self, MenuManager.SETTINGS_MENU, "sound", [("~music toggle~", " [-]", " [+]"),
                                                                        ("~effects toggle~", " [-]", " [+]"),
                                                                        "back"])
        self.prev_id = prev_id

        self.music_pcnt = gs.get_instance().settings().get(settings.SoundSettings.MUSIC_VOLUME)
        self.music_muted = self.music_pcnt == 0 or gs.get_instance().settings().get(settings.SoundSettings.MUSIC_MUTED)

        self.effects_pcnt = gs.get_instance().settings().get(settings.SoundSettings.EFFECTS_VOLUME)
        self.effects_muted = self.effects_pcnt == 0 or gs.get_instance().settings().get(settings.SoundSettings.EFFECTS_MUTED)

    def get_option_text(self, idx):
        if idx == SoundSettingsMenu.MUSIC_TOGGLE_IDX:
            if not self.music_muted:
                if self.music_pcnt == 100:
                    return "  music: MAX".format(self.music_pcnt)
                else:
                    return "  music: {}%".format(self.music_pcnt)
            else:
                return "  music: OFF"

        elif idx == SoundSettingsMenu.EFFECTS_TOGGLE_IDX:
            if not self.effects_muted:
                if self.effects_pcnt == 100:
                    return "effects: MAX".format(self.effects_pcnt)
                else:
                    return "effects: {}%".format(self.effects_pcnt)
            else:
                return "effects: OFF"
        else:
            return OptionsMenu.get_option_text(self, idx)

    def get_enabled(self, idx):
        if idx == SoundSettingsMenu.EFFECTS_VOLUME_DOWN_IDX:
            return not self.effects_muted
        elif idx == SoundSettingsMenu.EFFECTS_VOLUME_UP_IDX:
            return self.effects_muted or self.effects_pcnt < 100
        elif idx == SoundSettingsMenu.MUSIC_VOLUME_DOWN_IDX:
            return not self.music_muted
        elif idx == SoundSettingsMenu.MUSIC_VOLUME_UP_IDX:
            return self.music_muted or self.music_pcnt < 100
        else:
            return True

    def option_activated(self, idx):
        rebuild = False
        if idx == SoundSettingsMenu.MUSIC_TOGGLE_IDX:
            new_val = not self.music_muted
            gs.get_instance().settings().set(settings.SoundSettings.MUSIC_MUTED, new_val)

            if new_val is False and self.music_pcnt == 0:
                gs.get_instance().settings().set(settings.SoundSettings.MUSIC_VOLUME, 10)

            gs.get_instance().save_settings_to_disk()
            rebuild = True
            sound_effects.play_sound(soundref.menu_select)

        elif idx == SoundSettingsMenu.EFFECTS_TOGGLE_IDX:
            new_val = not self.effects_muted
            gs.get_instance().settings().set(settings.SoundSettings.EFFECTS_MUTED, new_val)

            if new_val is False and self.effects_pcnt == 0:
                gs.get_instance().settings().set(settings.SoundSettings.EFFECTS_VOLUME, 10)

            gs.get_instance().save_settings_to_disk()
            rebuild = True
            sound_effects.play_sound(soundref.menu_select)

        elif idx == SoundSettingsMenu.MUSIC_VOLUME_UP_IDX or idx == SoundSettingsMenu.MUSIC_VOLUME_DOWN_IDX:
            change = 10 if idx == SoundSettingsMenu.MUSIC_VOLUME_UP_IDX else -10
            new_vol = Utils.bound(self.music_pcnt + change, 0, 100)
            if new_vol == 0:
                gs.get_instance().settings().set(settings.SoundSettings.MUSIC_MUTED, True)
            else:
                gs.get_instance().settings().set(settings.SoundSettings.MUSIC_MUTED, False)
            gs.get_instance().settings().set(settings.SoundSettings.MUSIC_VOLUME, new_vol)

            gs.get_instance().save_settings_to_disk()
            rebuild = True
            sound_effects.play_sound(soundref.menu_select)

        elif idx == SoundSettingsMenu.EFFECTS_VOLUME_UP_IDX or idx == SoundSettingsMenu.EFFECTS_VOLUME_DOWN_IDX:
            change = 10 if idx == SoundSettingsMenu.EFFECTS_VOLUME_UP_IDX else -10
            new_vol = Utils.bound(self.effects_pcnt + change, 0, 100)
            if new_vol == 0:
                gs.get_instance().settings().set(settings.SoundSettings.EFFECTS_MUTED, True)
            else:
                gs.get_instance().settings().set(settings.SoundSettings.EFFECTS_MUTED, False)
            gs.get_instance().settings().set(settings.SoundSettings.EFFECTS_VOLUME, new_vol)

            gs.get_instance().save_settings_to_disk()
            rebuild = True
            sound_effects.play_sound(soundref.menu_select)

        elif idx == SoundSettingsMenu.BACK_IDX:
            if self.prev_id == MenuManager.START_MENU:
                gs.get_instance().menu_manager().set_active_menu(StartMenu())
            else:
                gs.get_instance().menu_manager().set_active_menu(PauseMenu())
            gs.get_instance().save_settings_to_disk()
            sound_effects.play_sound(soundref.menu_back)

        if rebuild:
            # rebuilding so the option text will change
            rebuilt = SoundSettingsMenu(self.prev_id)
            rebuilt.set_selected(idx, forcefully=True)
            gs.get_instance().menu_manager().set_active_menu(rebuilt)

    def esc_pressed(self):
        self.option_activated(SoundSettingsMenu.BACK_IDX)


class ControlsMenu(OptionsMenuWithTextBlurb):

    OPTS = [
        ("move up", settings.KeyBindings.KEY_UP),
        ("move left", settings.KeyBindings.KEY_LEFT),
        ("move down", settings.KeyBindings.KEY_DOWN),
        ("move right", settings.KeyBindings.KEY_RIGHT),
        ("skip turn", settings.KeyBindings.KEY_SKIP_TURN),
        ("rotate item", settings.KeyBindings.KEY_ROTATE_CW),
        ("equipment", settings.KeyBindings.KEY_INVENTORY),
        ("map", settings.KeyBindings.KEY_MAP)
    ]
    BACK_OPT_IDX = (len(OPTS), 0)

    def __init__(self, prev_id, selected_idx=(0, 0)):
        OptionsMenuWithTextBlurb.__init__(self, MenuManager.CONTROLS_MENU, "", ["~unused~"], info_text_size=1.0)
        self.prev_id = prev_id
        self.set_selected(selected_idx)

    def get_blurb_text(self):
        return "(click to change)"

    def get_blurb_text_color(self, i=-1):
        return colors.LIGHT_GRAY

    def get_option_text(self, idx):
        if idx == ControlsMenu.BACK_OPT_IDX:
            return "back"
        else:
            opt = ControlsMenu.OPTS[idx[0]]
            cur_values = gs.get_instance().settings().get(opt[1])

            if len(cur_values) == 0:
                return "{} [None]".format(opt[0])
            else:
                cur_value_strings = [Utils.stringify_key(k) for k in cur_values]
                value_str = "[" + ", ".join(cur_value_strings) + "]"

                return "{} {}".format(opt[0], value_str)

    def get_num_option_rows(self):
        return len(ControlsMenu.OPTS) + 1  # extra one is the "back" option

    def get_row_size(self, r):
        return 1

    def option_activated(self, idx):
        if idx == ControlsMenu.BACK_OPT_IDX:
            if self.prev_id == MenuManager.START_MENU:
                gs.get_instance().menu_manager().set_active_menu(StartMenu())
            else:
                gs.get_instance().menu_manager().set_active_menu(PauseMenu())
            sound_effects.play_sound(soundref.menu_back)
            gs.get_instance().save_settings_to_disk()
        elif 0 <= idx[0] < len(ControlsMenu.OPTS):
            opt = ControlsMenu.OPTS[idx[0]]
            gs.get_instance().menu_manager().set_active_menu(KeybindingEditMenu(opt[1], opt[0],
                                                                                lambda: ControlsMenu(self.prev_id, selected_idx=idx)))
            sound_effects.play_sound(soundref.menu_select)

    def esc_pressed(self):
        self.option_activated(ControlsMenu.BACK_OPT_IDX)


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
        sound_effects.play_sound(soundref.menu_back)

    def handle_inputs(self, world):
        input_state = InputState.get_instance()
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

                sound_effects.play_sound(soundref.menu_select)

    def _is_valid_binding(self, key):
        if key in (pygame.K_RETURN, pygame.K_ESCAPE, "MOUSE_BUTTON_1"):
            return False

        return True


# TODO - srsly delete this
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

    def update(self, world):
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

            self.cinematic_panel.update(current_image, current_text)

            dismiss_keys = gs.get_instance().settings().all_dialog_dismiss_keys()

            if self.active_tick_count > 10 and InputState.get_instance().was_pressed(dismiss_keys):
                if text_finished_scrolling:
                    self.active_scene = None
                else:
                    self.active_tick_count = len(full_text) * self.letter_reveal_speed

            self.active_tick_count += 1

        render_eng = RenderEngine.get_instance()
        for bun in self.all_bundles():
            render_eng.update(bun)

    def get_clear_color(self):
        return (0.0, 0.0, 0.0)

    def keep_drawing_world_underneath(self):
        return False

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.cinematic_panel is not None:
            for bun in self.cinematic_panel.all_bundles():
                yield bun


class FadingInFlavorMenu(OptionsMenu):
    """Displays some flavor text, then becomes a new menu"""

    def __init__(self, menu_type, flavor_text, next_menu, auto_next=False):
        OptionsMenu.__init__(self, menu_type, flavor_text, ["~hidden~"], title_size=1.5)
        self._flavor_full_brightness_duration = 100
        self._total_duration = 190
        self._flavor_tick = 0
        self._auto_next = auto_next

        self._next_menu = next_menu

    def get_clear_color(self):
        return (0, 0, 0)

    def get_flavor_progress(self):
        return Utils.bound(self._flavor_tick / self._flavor_full_brightness_duration, 0.0, 1.0)

    def get_title_color(self):
        return Utils.linear_interp(self.get_clear_color(), (1, 1, 1), self.get_flavor_progress())

    def get_option_color(self, idx):
        return self.get_clear_color()

    def update(self, world):
        OptionsMenu.update(self, world)

        self._flavor_tick += 1

        if self._flavor_tick > 5 and InputState.get_instance().was_anything_pressed():
            sound_effects.play_sound(soundref.menu_select)
            if self._flavor_tick >= self._total_duration - 10:
                gs.get_instance().menu_manager().set_active_menu(self._next_menu)
            else:
                self._flavor_tick = self._total_duration - 10
                self._auto_next = True

        elif self._flavor_tick >= self._total_duration and self._auto_next:
            gs.get_instance().menu_manager().set_active_menu(self._next_menu)

    def get_song(self):
        return None

    def option_activated(self, idx):
        pass


class DeathMenu(FadingInFlavorMenu):

    ALL_FLAVOR = [
        "pain!",
        "fail!",
        "dead!",
        "bad!",
        "no!",
        "you died!",
        "epic run!",
        "ouch!"
    ]

    def __init__(self, retry_save_data=None):
        FadingInFlavorMenu.__init__(self, MenuManager.DEATH_MENU, self.get_flavor_text(),
                                    DeathOptionMenu(retry_save_data=retry_save_data), auto_next=True)

    def get_flavor_text(self):
        idx = int(random.random() * len(DeathMenu.ALL_FLAVOR))
        return DeathMenu.ALL_FLAVOR[idx]


class DeathOptionMenu(OptionsMenu):

    RETRY = (0, 0)
    EXIT_OPT = (1, 0)

    def __init__(self, retry_save_data=None):
        self._retry_save_data = retry_save_data

        retry_text = "continue" if self._retry_save_data is not None else "retry"

        OptionsMenu.__init__(self, MenuManager.DEATH_OPTION_MENU, "game over", [retry_text, "quit"])

    def get_song(self):
        return None

    def option_activated(self, idx):
        if idx == DeathOptionMenu.EXIT_OPT:
            gs.get_instance().add_event(events.QuitToStartMenuEvent())
            sound_effects.play_sound(soundref.game_quit)

        elif idx == DeathOptionMenu.RETRY:
            gs.get_instance().add_event(events.NewGameEvent(from_save_data=self._retry_save_data))
            sound_effects.play_sound(soundref.newgame_start)


class DebugMenu(OptionsMenu):

    STORYLINE_ZONE_JUMP = (0, 0)
    SPECIAL_ZONE_JUMP = (1, 0)
    LOOT_ZONE_JUMP = (2, 0)
    DEBUG_SETTINGS = (3, 0)
    RESET_TUTORIALS = (4, 0)
    BACK_OPT = (5, 0)

    def __init__(self):
        OptionsMenu.__init__(self, MenuManager.DEBUG_MENU, "Debug",
                             ["storyline zones", "special zones", "loot zones", "debug settings", "reset tutorials", "back"])

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def esc_pressed(self):
        self.option_activated(DebugMenu.BACK_OPT)

    def option_activated(self, idx):
        if idx == DebugMenu.STORYLINE_ZONE_JUMP:
            gs.get_instance().menu_manager().set_active_menu(DebugZoneSelectMenu(0, DebugZoneSelectMenu.STORYLINE))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == DebugMenu.SPECIAL_ZONE_JUMP:
            gs.get_instance().menu_manager().set_active_menu(DebugZoneSelectMenu(0, DebugZoneSelectMenu.HANDBUILT))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == DebugMenu.LOOT_ZONE_JUMP:
            gs.get_instance().menu_manager().set_active_menu(DebugZoneSelectMenu(0, DebugZoneSelectMenu.LOOT))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == DebugMenu.DEBUG_SETTINGS:
            gs.get_instance().menu_manager().set_active_menu(DebugSettingsMenu())
            sound_effects.play_sound(soundref.menu_select)
        elif idx == DebugMenu.RESET_TUTORIALS:
            gs.get_instance().settings().clear_finished_tutorials()
            sound_effects.play_sound(soundref.menu_select)
        elif idx == DebugMenu.BACK_OPT:
            gs.get_instance().menu_manager().set_active_menu(InGameUiState())
            sound_effects.play_sound(soundref.menu_back)


class DebugSettingsMenu(OptionsMenu):

    def _get_all_debug_settings(self):
        res = []
        base_class = settings.DebugSettings
        for attrib_key in base_class.__dict__:
            attrib_val = base_class.__dict__[attrib_key]
            if attrib_val is not None and isinstance(attrib_val, settings.Setting):
                res.append(attrib_val)
        return res

    def _setting_name(self, setting):
        cur_val = gs.get_instance().settings().get(setting)
        return "{}: {}".format(setting.name, cur_val)

    def get_option_color(self, idx):
        if not self.get_enabled(idx) or idx[0] < 0 or idx[0] >= len(self._debug_settings):
            return super().get_option_color(idx)
        else:
            setting = self._debug_settings[idx[0]]
            cur_val = gs.get_instance().settings().get(setting)

            if cur_val is True:
                if self.get_selected_idx() == idx:
                    return super().get_option_color(idx)
                else:
                    return colors.G_TEXT_COLOR

            return super().get_option_color(idx)

    def __init__(self, active_idx=(0, 0)):
        self._debug_settings = self._get_all_debug_settings()
        option_names = [self._setting_name(x) for x in self._debug_settings]

        self._debug_enable_idx = (0, 0)
        self._back_idx = (len(option_names), 0)

        OptionsMenu.__init__(self, MenuManager.DEBUG_SETTINGS_MENU, "",
                             option_names + ["back"])

        self.set_selected(active_idx)

    def esc_pressed(self):
        self.option_activated(self._back_idx)

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def option_activated(self, idx):
        if idx == self._back_idx:
            gs.get_instance().menu_manager().set_active_menu(DebugMenu())
            sound_effects.play_sound(soundref.menu_back)
        elif 0 <= idx[0] < len(self._debug_settings):
            setting = self._debug_settings[idx[0]]

            cur_val = gs.get_instance().settings().get(setting)
            gs.get_instance().settings().set(setting, not cur_val)

            sound_effects.play_sound(soundref.menu_select)
            gs.get_instance().menu_manager().set_active_menu(DebugSettingsMenu(active_idx=idx))

    def get_enabled(self, idx):
        if idx == self._debug_enable_idx or idx == self._back_idx:
            return True
        else:
            enable_debug_setting = settings.DebugSettings.DEBUG_ENABLED
            return gs.get_instance().settings().get(enable_debug_setting)


class YouWinMenu(FadingInFlavorMenu):

    def __init__(self, total_time, turn_count, kill_count, death_count, cp_count, saved_version=None):
        FadingInFlavorMenu.__init__(self, MenuManager.YOU_WIN_MENU, "You Win!",
                                    YouWinStatsMenu(total_time, turn_count, kill_count, death_count, cp_count,
                                                    saved_version=saved_version), auto_next=True)

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT


class YouWinStatsMenu(OptionsMenuWithTextBlurb, MenuWithVersionDisplay):

    CONTINUE_IDX = (0, 0)

    def __init__(self, total_time, turn_count, kill_count, death_count, cp_count, saved_version=None):
        """
        saved_version: tuple (int, int, int, string) the version of this run's save file if one exists
        """
        if total_time < 216000000:
            time_str = Utils.ticks_to_time_string(total_time, show_hours_if_zero=True, fps=60)
        else:
            time_str = "999:59:59"  # protect the UI, always

        self._result_text = "\n".join(
                [" turns: {}".format(turn_count),
                 "deaths: {}".format(death_count),
                 " kills: {}".format(kill_count),
                 " saves: {}".format(cp_count)])

        OptionsMenuWithTextBlurb.__init__(self, MenuManager.YOU_WIN_MENU, "time: {}".format(time_str), ["continue"],
                                          title_size=1.5, info_text_size=1)

        self.saved_version_text = version.get_pretty_version_string(saved_version)
        MenuWithVersionDisplay.__init__(self)

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT

    def get_version_number_string(self):
        if self.saved_version_text is not None:
            return self.saved_version_text
        else:
            return version.get_pretty_version_string()

    def get_blurb_text(self):
        return self._result_text

    def option_activated(self, idx):
        if idx == YouWinStatsMenu.CONTINUE_IDX:
            gs.get_instance().menu_manager().set_active_menu(CreditsMenu())
            sound_effects.play_sound(soundref.menu_select)

    def esc_pressed(self):
        self.option_activated(YouWinStatsMenu.CONTINUE_IDX)

    def build_images(self):
        super().build_images()
        MenuWithVersionDisplay.build_version_images(self)

    def layout_rects(self):
        super().layout_rects()
        MenuWithVersionDisplay.layout_version_rects(self)

    def update_imgs(self):
        super().update_imgs()
        MenuWithVersionDisplay.update_version_images(self)

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for bun in MenuWithVersionDisplay.all_bundles(self):
            yield bun


class CreditsMenu(Menu):

    SMALL = 1
    NORMAL = 1.5

    SLIDE_TEXT = [
        ("created by", SMALL),
        "David Pendergast",
        ("2020", SMALL),
        "",
        ("art, coding, design, and music by", SMALL),
        "David Pendergast",
        "",
        ("twitter", SMALL),
        "@Ghast_NEOH",
        "",
        ("github", SMALL),
        "davidpendergast",
        "",
        # why does the name have to be sooo long omg
        #("sound effects from", SMALL),
        #("The Essential Retro Video Game ", NORMAL),
        #("Sound Effects Collection", NORMAL),
        #("by Juhani Junkala", SMALL),
        #("released under CC0", SMALL),
        #"",
        ("made with pygame", SMALL),
        "",
        ("thanks for playing <3", SMALL)
    ]

    def __init__(self):
        Menu.__init__(self, MenuManager.CREDITS_MENU)
        self.scroll_speeds = (1.5, 4)  # pixels per tick
        self.scroll_speed_idx = 0
        self.tick_count = 0
        self.empty_line_height = 160
        self.text_y_spacing = 10

        self.scroll_y_pos = 0  # distance from bottom of screen

        self._text_lines = [l for l in CreditsMenu.SLIDE_TEXT]
        self._all_images = []

        self._onscreen_img_indexes = set()

        self.build_images()

    def _scroll_speed(self):
        return self.scroll_speeds[self.scroll_speed_idx]

    def build_images(self):
        for line in self._text_lines:
            if line == "":
                self._all_images.append(None)
            else:
                if isinstance(line, tuple):
                    text = line[0]
                    size = line[1]
                else:
                    text = line
                    size = CreditsMenu.NORMAL

                self._all_images.append(TextImage(0, 0, text, spriteref.UI_0_LAYER, scale=size, x_kerning=0))

    def update(self, world):
        self.tick_count += 1

        enter_keys = gs.get_instance().settings().enter_key()
        if self.tick_count > 5 and InputState.get_instance().was_pressed(enter_keys):
            self.scroll_speed_idx = (self.scroll_speed_idx + 1) % len(self.scroll_speeds)

        self.scroll_y_pos += self._scroll_speed()

        screen_size = RenderEngine.get_instance().get_game_size()
        y_pos = screen_size[1] - int(self.scroll_y_pos)

        for i in range(0, len(self._all_images)):
            text_img = self._all_images[i]
            if text_img is None:
                y_pos += self.empty_line_height
            else:
                w = text_img.w()
                x_pos = screen_size[0] // 2 - w // 2
                text_img = text_img.update(new_x=x_pos, new_y=y_pos)
                self._all_images[i] = text_img

                RenderEngine.get_instance().update(text_img)

                y_pos += text_img.h() + self.text_y_spacing

        if y_pos < 0:
            gs.get_instance().add_event(events.QuitToStartMenuEvent())

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for text_img in self._all_images:
            if text_img is not None:
                for bun in text_img.all_bundles():
                    yield bun

    def get_song(self):
        return music.Songs.CONTINUE_CURRENT


class DebugZoneSelectMenu(OptionsMenu):
    ZONES_PER_PAGE = 8

    STORYLINE = "storyline"
    HANDBUILT = "hand_built"
    LOOT = "loot"

    def __init__(self, page, zone_types):

        self.page = page
        self.zone_types = zone_types

        all_zones = self._zones_to_show()
        start_idx = DebugZoneSelectMenu.ZONES_PER_PAGE * page
        self.first_page = (page == 0)

        if start_idx >= len(all_zones):
            # hmm..
            self.opts = []
            self.last_page = True
        elif start_idx + DebugZoneSelectMenu.ZONES_PER_PAGE < len(all_zones):
            self.opts = all_zones[start_idx:start_idx + DebugZoneSelectMenu.ZONES_PER_PAGE]
            self.last_page = False
        else:
            self.opts = all_zones[start_idx:]
            self.last_page = True

        self.opts.append("next page")
        self.next_page_idx = (len(self.opts) - 1, 0)

        self.opts.append("prev page")
        self.prev_page_idx = (len(self.opts) - 1, 0)

        self.opts.append("back")
        self.back_idx = (len(self.opts) - 1, 0)

        OptionsMenu.__init__(self, MenuManager.DEBUG_ZONE_SELECT_MENU, "zone select", self.opts)

    def _zones_to_show(self):
        import src.worldgen.zones as zones
        if self.zone_types == DebugZoneSelectMenu.HANDBUILT:
            all_zones = zones.all_handbuilt_zone_ids()
            all_zones.sort(key=lambda z_id: zones.get_zone(z_id).get_level())
        elif self.zone_types == DebugZoneSelectMenu.STORYLINE:
            all_zones = zones.all_storyline_zone_ids()
        elif self.zone_types == DebugZoneSelectMenu.LOOT:
            all_zones = zones.all_loot_zone_ids()
        else:
            all_zones = []

        return all_zones

    def get_enabled(self, idx):
        if idx == self.prev_page_idx and self.first_page:
            return False
        elif idx == self.next_page_idx and self.last_page:
            return False
        else:
            return True

    def esc_pressed(self):
        self.option_activated(self.back_idx)

    def option_activated(self, idx):
        if idx == self.back_idx:
            gs.get_instance().menu_manager().set_active_menu(DebugMenu())
            sound_effects.play_sound(soundref.menu_back)
        elif idx == self.next_page_idx:
            gs.get_instance().menu_manager().set_active_menu(DebugZoneSelectMenu(self.page + 1, self.zone_types))
            sound_effects.play_sound(soundref.menu_select)
        elif idx == self.prev_page_idx:
            gs.get_instance().menu_manager().set_active_menu(DebugZoneSelectMenu(self.page - 1, self.zone_types))
            sound_effects.play_sound(soundref.menu_select)
        elif 0 <= idx[0] < len(self.opts):
            selected_opt = self.opts[idx[0]]
            print("INFO: used debug menu to jump to zone: {}".format(selected_opt))
            new_zone_evt = events.NewZoneEvent(selected_opt, gs.get_instance().current_zone,
                                               show_zone_title_menu=False, do_fade_in=False)
            gs.get_instance().add_event(new_zone_evt)
            sound_effects.play_sound(soundref.menu_select)


class TitleMenu(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.TITLE_MENU)

        self.tick_count = 0

        self.title_fade_range = (60, 80)
        self.world_fade_range = (0, 30)
        self.show_press_any_tick = 120

        self.title_img = None

        self.title_fade_img = None
        self.world_fade_img = None

        self.press_any_key_img = None
        self.press_any_key_outlines = []

    def get_song(self):
        return music.Songs.MENU_THEME

    def keep_drawing_world_underneath(self):
        return False

    def update(self, world):
        if self.tick_count > 15 and InputState.get_instance().was_anything_pressed():
            if self.tick_count > self.show_press_any_tick:
                gs.get_instance().menu_manager().set_active_menu(StartMenu())
                return
            else:
                self.tick_count = max(self.tick_count, self.show_press_any_tick)

        if self.title_img is None:
            self.title_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, scale=2)
        idx = (gs.get_instance().anim_tick // 4) % len(spriteref.TitleScene.frames)
        model = spriteref.TitleScene.frames[idx]

        x = RenderEngine.get_instance().get_game_size()[0] // 2 - model.size()[0] * self.title_img.scale() // 2
        y = RenderEngine.get_instance().get_game_size()[1] // 2 - model.size()[1] * self.title_img.scale() // 2

        self.title_img = self.title_img.update(new_model=model, new_x=x, new_y=y, new_depth=50)

        title_fade_dur = self.title_fade_range[1] - self.title_fade_range[0]
        title_alpha = Utils.bound((self.tick_count - self.title_fade_range[0]) / title_fade_dur, 0, 1)
        if title_alpha == 1:
            if self.title_fade_img is not None:
                RenderEngine.get_instance().remove(self.title_fade_img)
                self.title_fade_img = None
        else:
            if self.title_fade_img is None:
                self.title_fade_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, depth=-10)

            sprite = spriteref.get_floor_lighting(title_alpha)
            ratio = (int(0.5 + self.title_img.width() / sprite.width()),
                     int(0.5 + (self.title_img.height() // 3) / sprite.height()))

            self.title_fade_img = self.title_fade_img.update(new_model=sprite, new_x=x, new_y=y,
                                                             new_ratio=ratio, new_color=(0, 0, 0))

        world_fade_dur = self.world_fade_range[1] - self.world_fade_range[0]
        world_alpha = Utils.bound((self.tick_count - self.world_fade_range[0]) / world_fade_dur, 0, 1)
        if world_alpha == 1:
            if self.world_fade_img is not None:
                RenderEngine.get_instance().remove(self.world_fade_img)
                self.world_fade_img = None
        else:
            if self.world_fade_img is None:
                self.world_fade_img = ImageBundle.new_bundle(spriteref.UI_0_LAYER, depth=-10)

            sprite = spriteref.get_floor_lighting(world_alpha)
            scr_size = RenderEngine.get_instance().get_game_size()
            ratio = (int(0.5 + scr_size[0] / sprite.width()), int(0.5 + ((scr_size[1] * 2) // 3) / sprite.height()))

            self.world_fade_img = self.world_fade_img.update(new_model=sprite, new_x=0, new_y=scr_size[1] // 3,
                                                             new_ratio=ratio, new_color=(0, 0, 0))

        press_any_text_scale = 1.5

        if self.press_any_key_img is None and self.tick_count > self.show_press_any_tick:
            self.press_any_key_img = TextImage(0, 0, "press any key", spriteref.UI_0_LAYER, scale=press_any_text_scale,
                                               x_kerning=0)

        if self.press_any_key_img is not None:
            text_w = self.press_any_key_img.w()
            text_h = self.press_any_key_img.h()
            text_x = x + self.title_img.width() // 2 - text_w // 2
            text_y = y + (self.title_img.height() * 15) // 16 - text_h // 2
            text_color = gs.get_instance().get_pulsing_color(colors.RED)

            self.press_any_key_img = self.press_any_key_img.update(new_x=text_x, new_y=text_y, new_color=text_color)

            if len(self.press_any_key_outlines) == 0:
                for _ in range(0, 4):
                    self.press_any_key_outlines.append(TextImage(0, 0, self.press_any_key_img.get_text(),
                                                                 spriteref.UI_0_LAYER, scale=press_any_text_scale,
                                                                 depth=10, color=(0, 0, 0), x_kerning=0))

            outline_positions = [n for n in Utils.neighbors(text_x, text_y, dist=press_any_text_scale)]
            for i in range(0, len(self.press_any_key_outlines)):
                outline_text = self.press_any_key_outlines[i]
                outline_x = outline_positions[i][0]
                outline_y = outline_positions[i][1]
                self.press_any_key_outlines[i] = outline_text.update(new_x=outline_x, new_y=outline_y)

        self.tick_count += 1

        render_eng = RenderEngine.get_instance()
        for bun in self.all_bundles():
            render_eng.update(bun)

    def all_bundles(self):
        if self.title_img is not None:
            yield self.title_img
        if self.title_fade_img is not None:
            yield self.title_fade_img
        if self.world_fade_img is not None:
            yield self.world_fade_img
        for outline_img in self.press_any_key_outlines:
            for bun in outline_img.all_bundles():
                yield bun
        if self.press_any_key_img is not None:
            for bun in self.press_any_key_img.all_bundles():
                yield bun


class InGameUiState(Menu):

    def __init__(self):
        Menu.__init__(self, MenuManager.IN_GAME_MENU)

        self.sidepanel = None
        self.health_bar_panel = None
        self.dialog_panel = None

        self.item_on_cursor_info = None  # tuple (item, ItemImage, offset)

        self.current_cursor_override = None

    def get_song(self):
        # zones specify their songs
        return music.Songs.CONTINUE_CURRENT

    def keep_drawing_world_underneath(self):
        return True

    def get_camera_center_point_on_screen(self):
        """
            Returns the point (x, y) on screen where the camera center should be drawn. This position will
            vary depending on the state of the UI. For example, when a sidebar is open, the world will
            be pushed to the right so that the player's visibily is restricted evenly between the left and right.
        """

        screen_w, screen_h = RenderEngine.get_instance().get_game_size()
        if self.sidepanel is not None:
            inv_w = self.sidepanel.get_rect()[2]
        else:
            inv_w = 0

        hb_height = HealthBarPanel.SIZE[1]

        cx = inv_w + (screen_w - inv_w) // 2
        cy = (screen_h - hb_height) // 2

        return (cx, cy)

    def _get_obj_at_screen_pos(self, world, xy):
        """returns: Item, ItemEntity, EnemyEntity, Entity, or None"""
        if xy is None:
            return None
        else:
            inv_open = self.sidepanel is not None and self.sidepanel.get_panel_type() == SidePanelTypes.INVENTORY
            if inv_open and self.sidepanel.contains_point(xy[0], xy[1]):
                inv_panel = self.sidepanel
                grid, cell = inv_panel.get_grid_and_cell_at_pos(*xy)
                if grid is not None and cell is not None:
                    return grid.item_at_position(cell)
            else:
                world_pos = gs.get_instance().screen_to_world_coords(xy)
                item_entity = world.get_entity_for_mouseover(world_pos, cond=lambda x: x.is_item())
                if item_entity is not None:
                    return item_entity

                enemy_entity = world.get_entity_for_mouseover(world_pos, cond=lambda x: x.is_enemy())
                if enemy_entity is not None:
                    return enemy_entity

                return world.get_entity_for_mouseover(world_pos)

    def cursor_style_at(self, world, xy):
        if self.item_on_cursor_info is not None:
            return None
        else:
            for image in self._top_level_interactable_imgs():
                if image.contains_point(*xy):
                    return image.get_cursor_at(*xy)

            obj_at_xy = self._get_obj_at_screen_pos(world, xy)
            if obj_at_xy is not None:
                if isinstance(obj_at_xy, item_module.Item):
                    return spriteref.UI.Cursors.hand_cursor

                import src.world.entities as entities
                if isinstance(obj_at_xy, entities.ItemEntity):
                    player = world.get_player()
                    if player is not None:
                        pos = world.to_grid_coords(*obj_at_xy.center())
                        pickup_action = gameengine.PickUpItemAction(player, obj_at_xy.get_item(), pos)
                        if pickup_action.is_possible(world):
                            return spriteref.UI.Cursors.hand_cursor

            return super().cursor_style_at(world, xy)

    def _top_level_interactable_imgs(self):
        if self.dialog_panel is not None:
            yield self.dialog_panel
        if self.health_bar_panel is not None:
            yield self.health_bar_panel
        if self.sidepanel is not None:
            yield self.sidepanel

    def _update_tooltip(self, world):
        input_state = InputState.get_instance()
        screen_pos = input_state.mouse_pos() if input_state.mouse_in_window() else None
        obj_to_display = None

        if screen_pos is not None and self.item_on_cursor_info is None:
            cursor_in_world = True
            for ui_img in self._top_level_interactable_imgs():
                if ui_img.contains_point(*screen_pos):
                    cursor_in_world = False
                    tt_target = ui_img.get_tooltip_target_at(*screen_pos)
                    if tt_target is not None:
                        obj_to_display = tt_target
                        break

            if cursor_in_world:
                obj_to_display = self._get_obj_at_screen_pos(world, screen_pos)

        if obj_to_display is None:
            self.set_active_tooltip(None)
        else:
            needs_update = False
            current_tooltip = self.get_active_tooltip()

            if obj_to_display is not None:
                obj_text = TooltipFactory.get_tooltip_text(obj_to_display)

                if obj_text is None:
                    self.set_active_tooltip(None)

                elif TooltipFactory.needs_rebuild(obj_text, current_tooltip):
                    new_tooltip = TooltipFactory.build_tooltip(obj_to_display, text_builder=obj_text, xy=(0, 0))
                    self.set_active_tooltip(new_tooltip)
                    needs_update = True

            current_tooltip = self.get_active_tooltip()

            render_eng = RenderEngine.get_instance()
            if current_tooltip is not None:
                tt_width = current_tooltip.get_rect()[2]
                tt_height = current_tooltip.get_rect()[3]
                tt_x = min(screen_pos[0], RenderEngine.get_instance().get_game_size()[0] - tt_width)

                y_offs = 12
                if screen_pos[1] + y_offs + tt_height > RenderEngine.get_instance().get_game_size()[1]:
                    if screen_pos[1] - y_offs - tt_height >= 0:
                        tt_y = screen_pos[1] - y_offs - tt_height
                    else:
                        tt_y = screen_pos[1] + 12  # if it's too tall to fit on the screen at all, we've got a problem
                else:
                    tt_y = screen_pos[1] + 12

                offs = (-tt_x, -tt_y)
                render_eng.set_layer_offset(spriteref.UI_TOOLTIP_LAYER, *offs)

            if needs_update and current_tooltip is not None:
                for bun in current_tooltip.all_bundles():
                    render_eng.update(bun)

    def _update_dialog_panel(self):
        should_destroy = (self.dialog_panel is not None and (not gs.get_instance().dialog_manager().is_active() or
                          self.dialog_panel.get_dialog() is not gs.get_instance().dialog_manager().get_dialog()))

        if should_destroy:
            self._destroy_panel(self.dialog_panel)
            self.dialog_panel = None

        if gs.get_instance().dialog_manager().is_active():
            if self.dialog_panel is None:
                dialog = gs.get_instance().dialog_manager().get_dialog()
                self.dialog_panel = DialogPanel(dialog)

        if self.dialog_panel is not None:
            self.dialog_panel.update()

    def _update_sidepanel(self, world):
        if not gs.get_instance().player_state().is_alive():
            gs.get_instance().set_active_sidepanel(None, play_sound=False)

        elif InputState.get_instance().was_pressed(gs.get_instance().settings().inventory_key()):
            gs.get_instance().toggle_sidepanel(SidePanelTypes.INVENTORY, play_sound=False)
        elif InputState.get_instance().was_pressed(gs.get_instance().settings().map_key()):
            gs.get_instance().toggle_sidepanel(SidePanelTypes.MAP, play_sound=False)

        # TODO - add 'close' key

        expected_id = gs.get_instance().get_active_sidepanel()
        actual_id = None if self.sidepanel is None else self.sidepanel.get_panel_type()

        if expected_id != actual_id:
            self.rebuild_and_set_sidepanel(expected_id)
        else:
            if self.sidepanel is not None:
                self.sidepanel.update(world)

                if self.sidepanel.needs_rebuild():
                    self.rebuild_and_set_sidepanel(self.sidepanel.get_panel_type())
                elif self.sidepanel.is_dirty():
                    self.sidepanel.update_images()

    def _update_health_bar_panel(self):
        if not gs.get_instance().player_state().is_alive():
            if self.health_bar_panel is not None:
                self._destroy_panel(self.health_bar_panel)
                self.health_bar_panel = None

        else:
            if self.health_bar_panel is None:
                self.health_bar_panel = HealthBarPanel(1)

            if self.health_bar_panel.is_dirty():
                self.health_bar_panel.update_images()
                for bun in self.health_bar_panel.all_bundles():
                    RenderEngine.get_instance().update(bun)

    def _get_mouse_pos_in_world(self):
        if not InputState.get_instance().mouse_in_window():
            return None
        else:
            screen_pos = InputState.get_instance().mouse_pos()
            for i in self._top_level_interactable_imgs():
                if i.contains_point(*screen_pos):
                    return None

            return gs.get_instance().screen_to_world_coords(screen_pos)

    def _update_item_on_cursor_info(self):
        destroy_image = False
        create_image = False

        held_item = gs.get_instance().held_item()

        if not gs.get_instance().player_state().is_alive() or not InputState.get_instance().mouse_in_window():
            destroy_image = True

        elif held_item is not None and self.item_on_cursor_info is None:
            create_image = True
        elif held_item is None and self.item_on_cursor_info is not None:
            destroy_image = True
        elif (held_item is not None and self.item_on_cursor_info is not None
              and held_item != self.item_on_cursor_info[0]):
                destroy_image = True
                create_image = True

        # TODO - this ought to be an action probably
        did_rotate_input = InputState.get_instance().was_pressed(gs.get_instance().settings().rotate_cw_key())
        if did_rotate_input and not gs.get_instance().world_updates_paused():
            if held_item is not None and held_item.can_rotate():
                new_held_item = held_item.rotate()
                gs.get_instance().set_held_item(new_held_item)

                if not destroy_image:  # so you can't flicker the image after death basically
                    create_image = True
                destroy_image = True

                gs.get_instance().add_event(events.RotatedItemEvent(new_held_item))
                sound_effects.play_sound(soundref.item_rotate)

        if destroy_image and self.item_on_cursor_info is not None:
            self._destroy_panel(self.item_on_cursor_info[1])
            self.item_on_cursor_info = None

        if create_image:
            held_item = gs.get_instance().held_item()
            size = ItemImage.calc_size(held_item, 1)
            item_img = ItemImage(0, 0, held_item, spriteref.UI_TOOLTIP_LAYER, 1, 0)
            item_offs = (-size[0] // 2, -size[1] // 2)
            self.item_on_cursor_info = (held_item, item_img, item_offs)
            render_eng = RenderEngine.get_instance()
            for bun in self.item_on_cursor_info[1].all_bundles():
                render_eng.update(bun)

        if self.item_on_cursor_info is not None:
            screen_pos = InputState.get_instance().mouse_pos()
            if screen_pos is not None:
                x_offs = -screen_pos[0] - self.item_on_cursor_info[2][0]
                y_offs = -screen_pos[1] - self.item_on_cursor_info[2][1]
                RenderEngine.get_instance().set_layer_offset(spriteref.UI_TOOLTIP_LAYER, x_offs, y_offs)

    def rebuild_and_set_sidepanel(self, panel_id):
        render_eng = RenderEngine.get_instance()
        if self.sidepanel is not None:
            for bun in self.sidepanel.all_bundles():
                render_eng.remove(bun)

        if panel_id == SidePanelTypes.INVENTORY:
            self.sidepanel = InventoryPanel()
        elif panel_id == SidePanelTypes.MAP:
            self.sidepanel = MapPanel()
        else:
            self.sidepanel = None

        if self.sidepanel is not None:
            for bun in self.sidepanel.all_bundles():
                render_eng.update(bun)

    def update(self, world):
        input_state = InputState.get_instance()
        screen_pos = input_state.mouse_pos()

        click_actions = []

        if screen_pos is not None:
            button1 = input_state.mouse_was_pressed(button=1)
            button3 = input_state.mouse_was_pressed(button=3)
            if button1 or button3:
                button = 1 if button1 else 3

                absorbed_click = False
                for image in self._top_level_interactable_imgs():
                    if image.contains_point(*screen_pos):
                        absorbed_click = image.on_click(*screen_pos, button=button)
                    if absorbed_click:
                        break

                if not absorbed_click:
                    # do click in world then
                    world_pos = gs.get_instance().screen_to_world_coords(screen_pos)
                    click_actions = gameengine.get_actions_from_click(world, world_pos, button=button)

        self._update_item_on_cursor_info()
        self._update_tooltip(world)
        self._update_sidepanel(world)

        # these inputs are allowed to bleed through world_updates_paused because they're
        # sorta "meta-inputs" (i.e. they don't affect the world).
        for i in range(0, 6):
            cur_targeting_action = gs.get_instance().get_targeting_action_provider()
            if input_state.was_pressed(gs.get_instance().settings().action_key(i)):
                new_targeting_action = gs.get_instance().get_mapped_action(i)
                if cur_targeting_action == new_targeting_action:
                    gs.get_instance().set_targeting_action_provider(None)
                    sound_effects.play_sound(soundref.action_deactivate)
                else:
                    gs.get_instance().set_targeting_action_provider(new_targeting_action)
                    sound_effects.play_sound(soundref.action_activate)

        self._update_health_bar_panel()
        self._update_dialog_panel()

        gs.get_instance().set_targetable_coords_in_world(None)

        if len(gs.get_instance().get_cinematics_queue()) > 0:
            gs.get_instance().menu_manager().set_active_menu(CinematicMenu())

        elif input_state.was_pressed(gs.get_instance().settings().exit_key()):
            gs.get_instance().menu_manager().set_active_menu(PauseMenu())
            sound_effects.play_sound(soundref.pause_in)

        else:
            target_coords = self.calc_visually_targetable_coords_in_world(world)
            gs.get_instance().set_targetable_coords_in_world(target_coords)

            p = world.get_player()
            if p is not None and not gs.get_instance().world_updates_paused():
                self.send_action_requests(p, world, click_actions=click_actions)

        # processing dialog last so that it'll block other things from getting inputs this frame
        # (because gs.world_updates_paused will get flipped to false when we interact).
        if gs.get_instance().dialog_manager().is_active():
            keys = gs.get_instance().settings().all_dialog_dismiss_keys()
            if input_state.was_pressed(keys):
                gs.get_instance().dialog_manager().interact()

    def send_action_requests(self, player, world, click_actions=None):
        dx = 0
        dy = 0
        input_state = InputState.get_instance()
        if input_state.is_held(gs.get_instance().settings().left_key()):
            dx -= 1
        elif input_state.is_held(gs.get_instance().settings().up_key()):
            dy -= 1
        elif input_state.is_held(gs.get_instance().settings().right_key()):
            dx += 1
        elif input_state.is_held(gs.get_instance().settings().down_key()):
            dy += 1

        pos = world.to_grid_coords(*player.center())
        target_pos = None
        if dx != 0:
            target_pos = (pos[0] + dx, pos[1])
        elif dy != 0:
            target_pos = (pos[0], pos[1] + dy)

        res_list = []
        if target_pos is not None:
            res_list.extend(gameengine.get_keyboard_action_requests(world, player, target_pos))

        if input_state.was_pressed(gs.get_instance().settings().skip_turn_key()):
            res_list.append(gameengine.SkipTurnAction(player, pos))

        pc = gs.get_instance().player_controller()

        if click_actions is not None:
            pc.add_requests(click_actions, pc.HIGHEST_PRIORITY)

        pc.add_requests(res_list)
        pc.add_requests(gameengine.PlayerWaitAction(player, position=target_pos), pc.LOWEST_PRIORITY)

    def calc_visually_targetable_coords_in_world(self, world):
        """:returns: map: (x, y) -> color"""

        if gs.get_instance().dialog_manager().is_active():
            return {}

        p = world.get_player()

        if p is None:
            return {}

        target_coords = {}

        pos = world.to_grid_coords(*p.center())
        for n in Utils.neighbors(pos[0], pos[1]):
            for act in gameengine.get_keyboard_action_requests(world, p, n):
                if act.is_possible(world):
                    position = act.get_position()
                    color = act.get_targeting_color(for_mouse=False)
                    if position is not None and color is not None:
                        target_coords[position] = color
                    break

        mouse_pos = self._get_mouse_pos_in_world()
        if mouse_pos is not None:
            for act in gameengine.get_actions_from_click(world, mouse_pos):
                if act.is_possible(world):
                    position = act.get_position()

                    if position is None:
                        # some actions have no positions (like applying items to the player).
                        position = world.to_grid_coords(*mouse_pos)

                    color = act.get_targeting_color(for_mouse=True)
                    if position is not None and color is not None:
                        target_coords[position] = color
                    break

        return target_coords

    def cleanup(self):
        Menu.cleanup(self)

        # TODO - not sure whether this feels right.
        # should the inv always close when you pause or change zones?
        gs.get_instance().set_active_sidepanel(None, play_sound=False)

        self.sidepanel = None
        self.item_on_cursor_info = None

    def all_bundles(self):
        for bun in Menu.all_bundles(self):
            yield bun
        if self.sidepanel is not None:
            for bun in self.sidepanel.all_bundles():
                yield bun
        if self.health_bar_panel is not None:
            for bun in self.health_bar_panel.all_bundles():
                yield bun
        if self.item_on_cursor_info is not None:
            for bun in self.item_on_cursor_info[1].all_bundles():
                yield bun
        if self.dialog_panel is not None:
            for bun in self.dialog_panel.all_bundles():
                yield bun