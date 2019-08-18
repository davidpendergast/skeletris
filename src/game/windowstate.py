
import pygame

_INSTANCE = None


class WindowState:

    def __init__(self, fullscreen, window_size):
        self._is_fullscreen = fullscreen
        self._window_size = window_size
        self._window_visible = False

    @staticmethod
    def create_instance(fullscreen, window_size):
        global _INSTANCE
        if _INSTANCE is not None:
            raise ValueError("WindowState instance is already created")
        else:
            _INSTANCE = WindowState(fullscreen, window_size)

    @staticmethod
    def get_instance():
        return _INSTANCE

    def _get_mods(self):
        if self.get_fullscreen():
            return pygame.FULLSCREEN | pygame.OPENGL
        else:
            return pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE

    def show_window(self):
        self._window_visible = True
        pygame.display.set_mode(self.get_size(), self._get_mods())

    def set_caption(self, title):
        pygame.display.set_caption(title)

    def set_icon(self, surface):
        pygame.display.set_icon(surface)

    def get_size(self):
        return self._window_size

    def set_size(self, w, h):
        self._window_size = (w, h)

    def get_fullscreen(self):
        return self._is_fullscreen

    def set_fullscreen(self, val, new_size=None):
        if self.get_fullscreen() == val:
            print("WARN: is_fullscreen already {}".format(val))

        self._is_fullscreen = val

        if new_size is not None:
            self._window_size = (new_size[0], new_size[1])

        self.show_window()

