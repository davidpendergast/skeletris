import random

class CubeUtils:

    @staticmethod
    def item_size(cubes):
        x_range = [cubes[0][0], cubes[0][0]]
        y_range = [cubes[0][1], cubes[0][1]]
        for c in cubes:
            x_range[0] = min(x_range[0], c[0])
            x_range[1] = max(x_range[1], c[0])
            y_range[0] = min(y_range[0], c[1])
            y_range[1] = max(y_range[1], c[1])
        return (x_range[1] - x_range[0] + 1, y_range[1] - y_range[0] + 1)

    @staticmethod
    def sort_cubes(cubes):
        temp = list(cubes)
        temp.sort(key=lambda c: c[0] + 1000 * c[1])
        return tuple(temp)

    @staticmethod
    def clean_cubes(cubes):
        res = CubeUtils._push_to_origin(cubes)
        return CubeUtils.sort_cubes(res)

    @staticmethod
    def rotate_cubes(cubes):
        rot_mapping = CubeUtils.calc_rotation_mapping(cubes)
        res = tuple(rot_mapping[cube] for cube in cubes)
        return CubeUtils.sort_cubes(res)

    @staticmethod
    def calc_rotation_mapping(cubes):
        """returns: map (x, y) -> (x, y)"""
        res = {}
        min_x = float('inf')
        min_y = float('inf')
        for cube in cubes:
            res[cube] = (5 - cube[1], cube[0])
            min_x = min(min_x, res[cube][0])
            min_y = min(min_y, res[cube][1])

        if min_x != 0 or min_y != 0:
            for cube in cubes:
                res[cube] = (res[cube][0] - min_x, res[cube][1] - min_y)

        return res

    @staticmethod
    def calc_mirror_mapping(cubes):
        """returns: map (x, y) -> (x, y)"""
        res = {}
        min_x = float('inf')
        min_y = float('inf')
        for cube in cubes:
            res[cube] = (5 - cube[0], cube[1])
            min_x = min(min_x, res[cube][0])
            min_y = min(min_y, res[cube][1])

        if min_x != 0 or min_y != 0:
            for cube in cubes:
                res[cube] = (res[cube][0] - min_x, res[cube][1] - min_y)

        return res

    @staticmethod
    def do_seed(seed):
        if seed is not None:
            random.seed(seed)

    @staticmethod
    def gen_cubes(n, size=(5, 5), seed=None):
        CubeUtils.do_seed(seed)
        if n > size[0] * size[1]:
            raise ValueError("{} is too many cubes for {}".format(n, size))

        choices = []
        for x in range(0, size[0]):
            for y in range(0, size[1]):
                choices.append((x, y))
        random.shuffle(choices)
        rejects = []
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diag = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        res = [choices.pop()]

        while len(res) < n:
            c = choices.pop()

            # if it's touching a cube we already have, add it.
            touch = sum([int((n[0] + c[0], n[1] + c[1]) in res) for n in neighbors])
            touch_diag = sum([int((n[0] + c[0], n[1] + c[1]) in res) for n in diag])

            if touch > 0 and (touch_diag == 0 or random.random() < 0.5):
                res.append(c)
            else:
                rejects.append(c)

            if len(choices) == 0:
                choices = rejects
                random.shuffle(choices)
                rejects = []

        res = CubeUtils.clean_cubes(res)

        return tuple(res)

    @staticmethod
    def is_holy(cubes):
        """return: whether the cube configuration has a hole"""
        size = CubeUtils.item_size(cubes)
        for x in range(1, size[0] - 1):
            for y in range(1, size[1] - 1):
                if (x, y) not in cubes:
                    fully_surrounded = True
                    for n_offs in CubeUtils.NEIGHBORS:
                        neighbor = (x + n_offs[0], y + n_offs[1])
                        if neighbor not in cubes:
                            fully_surrounded = False
                            break

                    if fully_surrounded:
                        return True
        return False


    @staticmethod
    def _push_to_origin(cubes):
        min_x = min([c[0] for c in cubes])
        min_y = min([c[1] for c in cubes])
        if min_x != 0 or min_y != 0:
            return [(c[0] - min_x, c[1] - min_y) for c in cubes]
        else:
            return cubes

    NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    @staticmethod
    def _get_all_possible_cube_configs_helper(n, size, base, already_seen):
        if n <= 0:
            return []
        else:
            res = []
            for cube in base:
                for n_offs in CubeUtils.NEIGHBORS:
                    neighbor = (cube[0] + n_offs[0], cube[1] + n_offs[1])
                    if neighbor not in base:
                        base_copy = [c for c in base]
                        base_copy.append(neighbor)
                        base_copy = CubeUtils.clean_cubes(base_copy)

                        bc_size = CubeUtils.item_size(base_copy)

                        if bc_size[0] <= size[0] and bc_size[1] <= size[1] and base_copy not in already_seen:
                            already_seen.add(base_copy)
                            if n == 1:
                                res.append(base_copy)
                            else:
                                res.extend(CubeUtils._get_all_possible_cube_configs_helper(n - 1, size,
                                                                                                      base_copy,
                                                                                                      already_seen))
            return res

    @staticmethod
    def get_all_possible_cube_configs(n=(5, 6, 7), size=(5, 5)):
        """
        :param n: number of allowable cubes. Either a list of numbers or a single number.
        :param size: bounding size of allowable cube configs.
        :return: all possible cube configurations
        """
        try:
            res = []
            for num in n:
                res.extend(CubeUtils._get_all_possible_cube_configs_helper(num - 1, size, [(0, 0)], set()))
            return res
        except TypeError:
            return CubeUtils._get_all_possible_cube_configs_helper(n - 1, size, [(0, 0)], set())
