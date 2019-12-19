
import pygame

_INSTANCE = None


class WindowState:

    def __init__(self, window_size, min_size=(0, 0)):
        self._is_fullscreen = False

        self._window_pos = None
        self._window_size = window_size

        self._min_size = min_size

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
        self._update_window(None)

    def _update_window(self, engine):
        display_size = self.get_display_size()
        mods = self._get_mods()

        pygame.display.set_mode(display_size, mods)

        if engine is not None:
           engine.reset_for_display_mode_change()

    def set_caption(self, title):
        pygame.display.set_caption(title)

    def set_icon(self, surface):
        pygame.display.set_icon(surface)

    def get_display_size(self):
        if self._is_fullscreen:
            return self.get_fullscreen_size()
        else:
            return self._window_size

    def get_fullscreen_size(self):
        """returns: the size of pygame's active monitor"""
        fullscreen_modes = pygame.display.list_modes()
        if fullscreen_modes != -1 and len(fullscreen_modes) > 0:
            return fullscreen_modes[0]
        else:
            # indicates some kind of error state, just going to try our best
            info = pygame.display.Info()
            return (info.current_w, info.current_h)

    def set_window_size(self, w, h, engine):
        self._window_size = (w, h)
        self._update_window(engine)

    def is_fullscreen(self):
        return self._is_fullscreen

    def set_fullscreen(self, val, engine):
        self._is_fullscreen = val
        self._update_window(engine)

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

