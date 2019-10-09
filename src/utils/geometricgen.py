import pygame
import math
import src.utils.colors as colors


def draw_ellipse(sheet, rect, color=colors.WHITE, opacity=1.0):
    int_color = (int(255 * color[0]), int(255 * color[1]), int(255 * color[2]))
    pygame.draw.ellipse(sheet, int_color, rect, 1)

    for x in range(rect[0], rect[0] + rect[2]):
        for y in range(rect[1], rect[1] + rect[3]):
            # it's good enoughTM don't @ me
            if x < 0 or x >= sheet.get_width() or y < 0 or y >= sheet.get_height():
                continue
            if sheet.get_at((x, y)) == int_color:
                sheet.set_at((x, y), (int_color[0], int_color[1], int_color[2], int(opacity*255)))


class GeometricGenerator:

    def draw_frame(self, sheet, rect, prog, color=colors.WHITE, opacity=1.0):
        pass


class CompositeGenerator:

    def __init__(self, sub_generators):
        self._sub_generators = sub_generators

    def draw_frame(self, sheet, rect, prog, color=colors.WHITE, opacity=1.0):
        for g in self._sub_generators:
            g.draw_frame(sheet, rect, prog, color=color, opacity=opacity)


class OuterCircleGenerator(GeometricGenerator):

    def draw_frame(self, sheet, rect, prog, color=colors.WHITE, opacity=1.0):
        draw_ellipse(sheet, rect, color=color, opacity=opacity)


class RotatingCirclesGenerator(GeometricGenerator):

    def __init__(self, n_circles=4, relative_size=0.5, period=1):
        self.n_circles = n_circles
        self.relative_size = relative_size
        self.period = min(n_circles, period)

    def draw_frame(self, sheet, rect, prog, color=colors.WHITE, opacity=1.0):
        small_circle_size = (rect[2] * self.relative_size, rect[3] * self.relative_size)
        for i in range(0, self.n_circles):
            angle = (prog / self.period + i / self.n_circles) * 2 * math.pi
            cx = rect[0] + rect[2] // 2 + int(small_circle_size[0] * (1 - self.relative_size) * math.cos(angle))
            cy = rect[1] + rect[3] // 2 + int(small_circle_size[1] * (1 - self.relative_size) * math.sin(angle))
            small_rect = [int(cx - small_circle_size[0] / 2),
                          int(cy - small_circle_size[1] / 2),
                          int(small_circle_size[0]),
                          int(small_circle_size[1])]
            draw_ellipse(sheet, small_rect, color=color, opacity=opacity)

