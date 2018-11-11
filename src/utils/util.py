import math
import random
import os
import json
import sys
import numbers


class Utils:

    @staticmethod
    def bound(val, lower, upper):
        if upper is not None and val > upper:
            return upper
        elif lower is not None and val < lower:
            return lower
        else:
            return val

    @staticmethod
    def add(v1, v2):
        return tuple(i[0] + i[1] for i in zip(v1, v2))

    @staticmethod
    def sub(v1, v2):
        return tuple(i[0] - i[1] for i in zip(v1, v2))

    @staticmethod
    def mult(v, a):
        return tuple(a*v_i for v_i in v)

    @staticmethod
    def rotate(v, rad):
        cos = math.cos(rad)
        sin = math.sin(rad)
        return (v[0]*cos - v[1]*sin, v[0]*sin + v[1]*cos)

    @staticmethod
    def to_degrees(rads):
        return rads * 180 / 3.141529

    @staticmethod
    def to_rads(degrees):
        return degrees * 3.141529 / 180

    @staticmethod
    def set_length(v, length):
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1])
        if mag == 0:
            return Utils.rand_vec(length)
        else:
            return Utils.mult(v, length / mag)

    @staticmethod
    def mag(v):
        return math.sqrt(sum(i*i for i in v))

    @staticmethod
    def dist(v1, v2):
        return Utils.mag(Utils.sub(v1, v2))

    @staticmethod
    def rand_vec(length=1):
        angle = 6.2832 * random.random()
        return [length*math.cos(angle), length*math.sin(angle)]

    @staticmethod
    def rect_contains(rect, v):
        return rect[0] <= v[0] < rect[0] + rect[2] and rect[1] <= v[1] < rect[1] + rect[3]

    @staticmethod
    def linear_interp(v1, v2, a):
        if isinstance(v1, numbers.Number):
            return v1 * (1 - a) + v2 * a
        else:
            return tuple([v1[i] * (1 - a) + v2[i] * a for i in range(0, len(v1))])

    @staticmethod
    def round(v):
        return tuple([round(i) for i in v])

    @staticmethod
    def replace_all_except(text, replace_txt, except_for=()):
        return "".join(x if (x in except_for) else replace_txt for x in text)

    @staticmethod
    def listify(obj):
        if (isinstance(obj, list)):
            return obj
        else:
            return [obj]

    @staticmethod
    def min_component(v_list, i):
        res = None
        for v in v_list:
            if i < len(v):
                res = min(v[i], res) if res is not None else v[i]
        return res

    @staticmethod
    def max_component(v_list, i):
        res = None
        for v in v_list:
            if i < len(v):
                res = max(v[i], res) if res is not None else v[i]
        return res

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def load_json_from_path(filepath):
        with open(filepath) as f:
            data = json.load(f)
            return data

    @staticmethod
    def save_json_to_path(json_blob, filepath):
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as outfile:
            json.dump(json_blob, outfile)

    @staticmethod
    def read_int(json_blob, key, default):
        return Utils.read_safely(json_blob, key, default, mapper=lambda x: int(x))

    @staticmethod
    def read_string(json_blob, key, default):
        return Utils.read_safely(json_blob, key, default, mapper=lambda x: str(x))

    @staticmethod
    def read_bool(json_blob, key, default):
        return Utils.read_safely(json_blob, key, default, mapper=lambda x: bool(x))

    @staticmethod
    def read_safely(json_blob, key, default, mapper=lambda x: x):
        if key not in json_blob or json_blob[key] is None:
            print("returning default {} for key {}".format(default, key))
            return default
        else:
            try:
                return mapper(json_blob[key])
            except ValueError:
                return default

