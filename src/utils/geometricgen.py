import pygame
import math

import src.utils.colors as colors
from src.utils.util import Utils


def to_rgb(color):
    return (Utils.bound(round(256 * color[0]), 0, 255),
            Utils.bound(round(256 * color[1]), 0, 255),
            Utils.bound(round(256 * color[2]), 0, 255))


def to_rgba(color, opacity=1.0):
    return (Utils.bound(round(256 * color[0]), 0, 255),
            Utils.bound(round(256 * color[1]), 0, 255),
            Utils.bound(round(256 * color[2]), 0, 255),
            Utils.bound(round(256 * opacity), 0, 255))


def replace_color(sheet, rect, rgb, rgba):
    for x in range(rect[0], rect[0] + rect[2]):
        for y in range(rect[1], rect[1] + rect[3]):
            if x < 0 or x >= sheet.get_width() or y < 0 or y >= sheet.get_height():
                continue
            if sheet.get_at((x, y)) == rgb:
                sheet.set_at((x, y), rgba)


class GeometricGenerator:

    def draw(self, sheet, rect, prog, color=colors.WHITE, opacity=1.0):
        self.draw_frame(sheet, rect, prog, to_rgb(color))
        replace_color(sheet, rect, to_rgb(color), to_rgba(color, opacity))

    def draw_frame(self, sheet, rect, prog, rgb):
        pass


class CompositeGenerator(GeometricGenerator):

    def __init__(self, sub_generators):
        self._sub_generators = sub_generators

    def draw_frame(self, sheet, rect, prog, rgb):
        for g in self._sub_generators:
            g.draw_frame(sheet, rect, prog, rgb)


class OuterCircleGenerator(GeometricGenerator):

    def draw_frame(self, sheet, rect, prog, rgb):
        pygame.draw.ellipse(sheet, rgb, rect, 1)


class ResizingCircleGenerator(OuterCircleGenerator):

    def __init__(self, start_size, end_size):
        self.start_size = start_size
        self.end_size = end_size

    def draw_frame(self, sheet, rect, prog, rgb):
        cur_size = self.start_size + prog * (self.end_size - self.start_size)
        cx = rect[0] + rect[2] / 2
        cy = rect[1] + rect[3] / 2
        new_rect = [
            int(cx - cur_size * rect[2] / 2),
            int(cy - cur_size * rect[3] / 2),
            round(rect[2] * cur_size),
            round(rect[3] * cur_size)
        ]

        bounded_new_rect = Utils.get_rect_intersect(rect, new_rect)

        if bounded_new_rect is not None:
            super().draw_frame(sheet, bounded_new_rect, prog, rgb)


class RotatingCirclesGenerator(GeometricGenerator):

    def __init__(self, n_circles=4, relative_size=0.5, speed=1):
        self.n_circles = n_circles
        self.relative_size = relative_size
        self.speed = speed

    def draw_frame(self, sheet, rect, prog, rgb):
        small_circle_size = (rect[2] * self.relative_size, rect[3] * self.relative_size)
        for i in range(0, self.n_circles):
            angle = (prog * self.speed + i) / self.n_circles * 2 * math.pi
            cx = rect[0] + rect[2] // 2 + int(small_circle_size[0] * (1 - self.relative_size) * math.cos(angle))
            cy = rect[1] + rect[3] // 2 + int(small_circle_size[1] * (1 - self.relative_size) * math.sin(angle))
            small_rect = [int(cx - small_circle_size[0] / 2),
                          int(cy - small_circle_size[1] / 2),
                          int(small_circle_size[0]),
                          int(small_circle_size[1])]
            pygame.draw.ellipse(sheet, rgb, small_rect, 1)


class OuterRotatingPolygonGenerator(GeometricGenerator):

    def __init__(self, n_vertices, speed=1):
        self.n_vertices = n_vertices
        self.speed = speed

    def get_vertex_positions(self, rect, prog):
        vertices = []
        center = (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
        for i in range(0, self.n_vertices):
            angle = (prog * self.speed + i) / self.n_vertices * 2 * math.pi
            vertices.append((int(center[0] + rect[2] / 2 * math.cos(angle)),
                             int(center[1] + rect[3] / 2 * math.sin(angle))))
        return vertices

    def draw_frame(self, sheet, rect, prog, rgb):
        vertices = self.get_vertex_positions(rect, prog)
        pygame.draw.polygon(sheet, rgb, vertices, 1)


class OuterRotatingStarGenerator(OuterRotatingPolygonGenerator):

    def __init__(self, n_vertices, jump_n, speed=1):
        OuterRotatingPolygonGenerator.__init__(self, n_vertices, speed=speed)
        self.jump_n = jump_n

    def draw_frame(self, sheet, rect, prog, rgb):
        vertices = self.get_vertex_positions(rect, prog)
        for i in range(0, self.n_vertices):
            j = (i + self.jump_n) % self.n_vertices
            p_i = vertices[i]
            p_j = vertices[j]
            pygame.draw.line(sheet, rgb, p_i, p_j, 1)
