
import pygame

_INSTANCE = None


class WindowState:

    def __init__(self, fullscreen, screen_size, window_size, fullscreen_size, resizeable):
        self._is_fullscreen = fullscreen

        self._fullscreen_size = fullscreen_size  # AKA the monitor's size
        self._window_size = window_size

        self._window_visible = False
        self._is_resizeable = resizeable
        self._screen_size = screen_size

    @staticmethod
    def create_instance(fullscreen=False, resizeable=False,
                        screen_size=(640, 480), window_size=(640, 480), fullscreen_size=(640, 480)):

        global _INSTANCE
        if _INSTANCE is not None:
            raise ValueError("WindowState instance is already created")
        else:
            _INSTANCE = WindowState(fullscreen, screen_size, window_size, fullscreen_size, resizeable)

    @staticmethod
    def get_instance():
        return _INSTANCE

    def _get_mods(self):
        if self.get_fullscreen():
            return pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE
        else:
            res = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE

            if self._is_resizeable:
                res = res | pygame.RESIZABLE

            return res

    def show_window(self, engine):
        self._window_visible = True
        display_size = self.get_display_size()
        mods = self._get_mods()

        # print("INFO: called pygame.display.set_mode({}, {})".format(display_size, mods))
        pygame.display.set_mode(display_size, mods)

        if engine is not None:
           engine.reset_for_display_mode_change()

    def set_caption(self, title):
        pygame.display.set_caption(title)

    def set_icon(self, surface):
        pygame.display.set_icon(surface)

    def get_window_size(self):
        return self._window_size

    def get_display_size(self):
        if self._is_fullscreen:
            return self._fullscreen_size
        else:
            return self._window_size

    def set_window_size(self, w, h, engine, forcefully=False):
        self._window_size = (w, h)

        if forcefully:
            self.show_window(engine)

    def get_screen_size(self):
        return self._screen_size

    def set_screen_size(self, w, h):
        self._screen_size = (w, h)

    def get_fullscreen(self):
        return self._is_fullscreen

    def set_fullscreen(self, val, engine, forcefully=True):
        print("INFO: setting fullscreen to {}".format(val))
        self._is_fullscreen = val

        if forcefully:
            self.show_window(engine)

    def get_resizeable(self):
        return self._is_resizeable

    def set_resizeable(self, engine, val):
        self._is_resizeable = val
        self.show_window(engine)

    def window_to_screen_pos(self, pos):
        if pos is None:
            return None
        else:
            # screen is anchored at bottom left corner of window.
            # no real reason for that, it's just what happened
            dy = self.get_screen_size()[1] - self.get_display_size()[1]
            return (pos[0], pos[1] + dy)

