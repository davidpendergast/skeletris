
import pygame

_INSTANCE = None


class WindowState:

    def __init__(self, window_size, min_size=(0, 0)):
        self._is_fullscreen = False
        self._window_size = window_size
        self._min_size = min_size

        self._cached_fullscreen_size = None

    @staticmethod
    def create_instance(window_size=(640, 480), min_size=(0, 0)):

        global _INSTANCE
        if _INSTANCE is not None:
            raise ValueError("WindowState instance is already created")
        else:
            _INSTANCE = WindowState(window_size, min_size=min_size)

    @staticmethod
    def get_instance():
        return _INSTANCE

    def _get_mods(self):
        mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE

        if self.is_fullscreen():
            mods = pygame.FULLSCREEN | mods

        return mods

    def show(self):
        self._update_display_mode()

    def _update_display_mode(self):
        if self._is_fullscreen:
            new_size = self._calc_fullscreen_size_for_set_mode()
            self._cached_fullscreen_size = new_size
        else:
            new_size = self._window_size

        pygame.display.set_mode(new_size, self._get_mods())

        from src.renderengine.engine import RenderEngine
        render_eng = RenderEngine.get_instance()
        if render_eng is not None:
            # XXX otherwise everything breaks on Windows (see docs on this method)
            render_eng.reset_for_display_mode_change()

    def set_caption(self, title):
        pygame.display.set_caption(title)

    def set_icon(self, surface):
        pygame.display.set_icon(surface)

    def get_display_size(self):
        if self._is_fullscreen:
            return self._cached_fullscreen_size
        else:
            return self._window_size

    def _calc_fullscreen_size_for_set_mode(self):
        fullscreen_modes = pygame.display.list_modes()
        if fullscreen_modes != -1 and len(fullscreen_modes) > 0:
            # XXX this give bizarre results when multiple monitors are present.
            return fullscreen_modes[0]

        print("WARN: falling back to display.Info() to calculate fullscreen size")
        # indicates some kind of error state, just going to try our best
        info = pygame.display.Info()
        return (info.current_w, info.current_h)  # this gets the current window size

    def set_window_size(self, w, h):
        # print("INFO: set window size to: ({}, {})".format(w, h))
        self._window_size = (w, h)
        self._update_display_mode()

    def is_fullscreen(self):
        return self._is_fullscreen

    def set_fullscreen(self, val):
        if self.is_fullscreen() == val:
            return
        else:
            self._cached_fullscreen_size = None

            self._is_fullscreen = val
            self._update_display_mode()

    def window_to_screen_pos(self, pos):
        if pos is None:
            return None
        else:
            # screen is anchored at bottom left corner of window.
            # no real reason for that, it's just what happened
            if self.get_display_size()[1] < self._min_size[1]:
                dy = self._min_size[1] - self.get_display_size()[1]
            else:
                dy = 0
            return (pos[0], pos[1] + dy)

