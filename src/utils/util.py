import math
import random
import os
import json
import numbers
import pathlib
import sys


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
    def next_power_of_2(val):
        return 1 if val <= 0 else 2 ** math.ceil(math.log2(val))

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
    def average(v_list):
        if len(v_list) == 0:
            raise ValueError("cannot take average of 0 vectors.")
        n = len(v_list[0])
        if n == 0:
            return tuple()

        sum_v = [0 for _ in range(0, n)]
        for v in v_list:
            for i in range(0, n):
                sum_v[i] = sum_v[i] + v[i]

        return Utils.mult(sum_v, 1 / len(v_list))

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
    def dist_manhattan(v1, v2):
        res = 0
        for i, j in zip(v1, v2):
            res += abs(i - j)
        return res

    @staticmethod
    def rand_vec(length=1):
        angle = 6.2832 * random.random()
        return [length*math.cos(angle), length*math.sin(angle)]

    @staticmethod
    def rect_expand(rect, left_expand=0, right_expand=0, up_expand=0, down_expand=0):
        return [rect[0] - left_expand,
                rect[1] - up_expand,
                rect[2] + (left_expand + right_expand),
                rect[3] + (up_expand + down_expand)]

    @staticmethod
    def rect_contains(rect, v):
        return rect[0] <= v[0] < rect[0] + rect[2] and rect[1] <= v[1] < rect[1] + rect[3]

    @staticmethod
    def rect_center(rect):
        return (int(rect[0] + rect[2] / 2),
                int(rect[1] + rect[3] / 2))

    @staticmethod
    def get_rect_corners(rect, inclusive=False):
        yield (rect[0], rect[1])
        if inclusive:
            if rect[2] == 0 or rect[3] == 0:
                if rect[2] > 0:
                    yield (rect[0] + rect[2] - 1, rect[1])
                elif rect[3] > 0:
                    yield (rect[0], rect[1] + rect[3] - 1)
            else:
                yield (rect[0] + rect[2] - 1, rect[1])
                yield (rect[0], rect[1] + rect[3] - 1)
                yield (rect[0] + rect[2] - 1, rect[1] + rect[3] - 1)
        else:
            yield (rect[0] + rect[2], rect[1])
            yield (rect[0], rect[1] + rect[3])
            yield (rect[0] + rect[2], rect[1] + rect[3])

    @staticmethod
    def get_rect_intersect(rect1, rect2):
        x1 = max(rect1[0], rect2[0])
        x2 = min(rect1[0] + rect1[2], rect2[0] + rect2[2])
        y1 = max(rect1[1], rect2[1])
        y2 = min(rect1[1] + rect1[3], rect2[1] + rect2[3])
        if x1 >= x2 or y1 >= y2:
            return None
        else:
            return Utils.get_rect_containing_points([(x1, y1), (x2, y2)])

    @staticmethod
    def get_rect_containing_points(pts, inclusive=False):
        if len(pts) == 0:
            raise ValueError("pts is empty")
        else:
            min_x = pts[0][0]
            max_x = pts[0][0]
            min_y = pts[0][1]
            max_y = pts[0][1]

            for pt in pts:
                min_x = min(min_x, pt[0])
                max_x = max(max_x, pt[0])
                min_y = min(min_y, pt[1])
                max_y = max(max_y, pt[1])

            if inclusive:
                max_x += 1
                max_y += 1

            return [min_x, min_y, (max_x - min_x), (max_y - min_y)]

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
    def flatten_list(l):
        return [x for x in Utils._flatten_helper(l)]

    @staticmethod
    def _flatten_helper(l):
        for x in l:
            if isinstance(x, list):
                for y in Utils._flatten_helper(x):
                    yield y
            else:
                yield x

    @staticmethod
    def cells_between(p1, p2, include_endpoints=True):
        if p1 == p2:
            return [tuple(p1)] if include_endpoints else []

        start = [p1[0] + 0.5, p1[1] + 0.5]
        end = [p2[0] + 0.5, p2[1] + 0.5]

        xy = [start[0], start[1]]
        step_dist = 0.1
        step_vec = Utils.set_length(Utils.sub(end, start), step_dist)

        res = []
        for i in range(0, int(Utils.dist(start, end) // step_dist)):
            xy[0] = xy[0] + step_vec[0]
            xy[1] = xy[1] + step_vec[1]
            cur_cell = (int(xy[0]), int(xy[1]))
            if len(res) > 0 and res[-1] == cur_cell:
                continue
            else:
                if cur_cell == p1 or cur_cell == p2:
                    if include_endpoints:
                        res.append(cur_cell)
                else:
                    res.append(cur_cell)

        return res

    @staticmethod
    def add_to_list_and_return(val, the_list):
        the_list.append(val)
        return val

    @staticmethod
    def stringify_key(keycode):
        import pygame
        if keycode == pygame.K_LEFT:
            return "←"
        elif keycode == pygame.K_UP:
            return "↑"
        elif keycode == pygame.K_RIGHT:
            return "→"
        elif keycode == pygame.K_DOWN:
            return "↓"
        elif isinstance(keycode, str) and keycode.startswith("MOUSE_BUTTON_"):
            num = keycode.replace("MOUSE_BUTTON_", "")
            return "M{}".format(num)
        else:
            res = pygame.key.name(keycode)
            if len(res) == 1 and res.islower():
                return res.upper()
            else:
                return res

    @staticmethod
    def stringify_keylist(keycodes, or_else=""):
        """returns: comma separated list of the given keys formatted as strings."""
        if len(keycodes) == 0:
            return or_else
        else:
            key_strings = [Utils.stringify_key(k) for k in keycodes]
            return ",".join(key_strings)

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, str(pathlib.Path(relative_path)))

    @staticmethod
    def load_json_from_path(filepath):
        with open(filepath) as f:
            data = json.load(f)
            return data

    @staticmethod
    def save_json_to_path(json_blob, filepath):
        try:
            json.dumps(json_blob, indent=4, sort_keys=True)
        except (ValueError, TypeError) as e:
            print("ERROR: tried to save invalid json to file: {}".format(filepath))
            print("ERROR: json_blob: {}".format(json_blob))
            raise e

        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as outfile:
            json.dump(json_blob, outfile, indent=4, sort_keys=True)

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
    def read_map(json_blob, key, default):
        return default  # hmmm, one day~

    @staticmethod
    def parabola_height(vertex_y, x):
        """
        finds f(x) of the parabola for which f(0) = 0, f(0.5) = vertex_y, f(1.0) = 0
        """
        #  mmm delicious math
        a = -4 * vertex_y
        b = 4 * vertex_y
        return (a * x * x) + (b * x)

    @staticmethod
    def get_shake_points(strength, duration, falloff=3, freq=6):
        """
        int strength: max pixel offset of shake
        int duration: ticks for which the shake will remain active
        int freq: "speed" of the shake. 1 is really fast, higher is slower
        """

        if duration % freq != 0:
            duration += freq - (duration % freq)

        decay = lambda t: math.exp(-falloff*(t / duration))
        num_keypoints = int(duration / freq)
        x_pts = [round(2 * (0.5 - random.random()) * strength * decay(t * freq)) for t in range(0, num_keypoints)]
        y_pts = [round(2 * (0.5 - random.random()) * strength * decay(t * freq)) for t in range(0, num_keypoints)]
        x_pts.append(0)
        y_pts.append(0)

        shake_pts = []
        for i in range(0, duration):
            if i % freq == 0:
                shake_pts.append((x_pts[i // freq], y_pts[i // freq]))
            else:
                prev_pt = (x_pts[i // freq], y_pts[i // freq])
                next_pt = (x_pts[i // freq + 1], y_pts[i // freq + 1])
                shake_pts.append(Utils.linear_interp(prev_pt, next_pt, (i % freq) / freq))

        if len(shake_pts) == 0:
            return  # this shouldn't happen but ehh

        shake_pts.reverse()  # this is used as a stack
        return shake_pts

    @staticmethod
    def neighbors(x, y, and_diags=False, dist=1):
        if dist <= 0:
            return
        yield (x + dist, y)
        yield (x, y + dist)
        yield (x - dist, y)
        yield (x, y - dist)
        if and_diags:
            yield (x + dist, y + dist)
            yield (x - dist, y + dist)
            yield (x + dist, y - dist)
            yield (x - dist, y - dist)

    @staticmethod
    def ticks_to_time_string(n_ticks, fps=60, show_hours_if_zero=False):
        seconds = max(0, n_ticks // fps)
        hours = seconds // 3600
        seconds = seconds % 3600
        minutes = seconds // 60
        seconds = seconds % 60

        res = str(seconds)
        if seconds < 10:
            res = ":0" + res
        else:
            res = ":" + res

        if minutes < 10 and (hours > 0 or show_hours_if_zero):
            res = "0" + str(minutes) + res
        else:
            res = str(minutes) + res

        if hours == 0:
            return "0:" + res if show_hours_if_zero else res
        else:
            return str(hours) + ":" + res

    @staticmethod
    def read_safely(json_blob, key, default, mapper=lambda x: x):
        if key not in json_blob or json_blob[key] is None:
            return default
        else:
            try:
                return mapper(json_blob[key])
            except Exception:
                return default

    @staticmethod
    def python_version_string():
        major = sys.version_info[0]
        minor = sys.version_info[1]
        patch = sys.version_info[2]
        return "{}.{}.{}".format(major, minor, patch)

    @staticmethod
    def string_checksum(the_string, m=982451653):
        res = 0
        for c in the_string:
            res += ord(c)
            res = (res * 31) % m
        return res

    @staticmethod
    def checksum(blob, m=982451653, strict=True):
        """
            Calculates a checksum of any composition of dicts, lists, tuples, bools, strings, and ints.
            Lists and tuples are considered identical. The only restriction is that keys of maps must
            be comparable, and there can't be loops (like a map containing itself).

            param strict: if False, illegal types will be converted to strings and included in the checksum.
                          if True, illegal types will cause a ValueError to be thrown.
        """
        if blob is None:
            return 11 % m
        elif isinstance(blob, bool):
            return (31 if blob else 1279) % m
        elif isinstance(blob, int):
            return blob % m
        elif isinstance(blob, str):
            return Utils.string_checksum(blob, m=m)
        elif isinstance(blob, (list, tuple)):
            res = 0
            for c in blob:
                res += Utils.checksum(c)
                res = (res * 37) % m
            return res
        elif isinstance(blob, dict):
            keys = [k for k in blob]
            keys.sort()

            res = 0
            for key in keys:
                k_checksum = Utils.checksum(key, m=m)
                val_checksum = Utils.checksum(blob[key])
                res += k_checksum
                res = (res * 41) % m
                res += val_checksum
                res = (res * 53) % m

            return res
        else:
            if strict:
                raise ValueError("blob has illegal type: {}".format(blob))
            else:
                return Utils.string_checksum(str(blob), m=m)
