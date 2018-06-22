import math
import random

class Utils:

    @staticmethod
    def add(v1, v2):
        return (v1[0] + v2[0], v1[1] + v2[1])

    @staticmethod
    def sub(v1, v2):
        return (v1[0] - v2[0], v1[1] - v2[1])

    @staticmethod
    def mult(v, a):
        return (a*v[0], a*v[1])

    @staticmethod
    def set_length(v, length):
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1])
        if mag == 0:
            return Utils.rand_vec(length)
        else:
            return Utils.mult(v, length / mag)

    @staticmethod
    def mag(v):
        return math.sqrt(v[0]*v[0] + v[1]*v[1])

    @staticmethod
    def dist(v1, v2):
        return Utils.mag(Utils.sub(v1, v2))

    @staticmethod
    def rand_vec(length=1):
        angle = 6.2832 * random.random()
        return [length*math.cos(angle), length*math.sin(angle)]

    @staticmethod
    def rect_contains(rect, v):
        return (v[0] >= rect[0] and v[0] < rect[0] + rect[2]
                and v[1] >= rect[1] and v[1] < rect[1] + rect[3])
        
