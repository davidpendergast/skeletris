import pygame
import random
import math

from src.utils.util import Utils


class Branch:

    def __init__(self, angle, thickness, length, depth):
        self.angle = angle  # angle relative to parent branch
        self.length = length
        self.kids = []
        self.thickness = thickness
        self.finalized = False
        self.depth = depth

    def __repr__(self):
        return "Branch({}, {}, {}, {})".format(self.angle, self.thickness, self.length, self.depth)


class Tree:

    def __init__(self, root, root_pos):
        self.root_pos = root_pos
        self.root = root

    def all_branches(self):
        q = []
        if self.root is not None:
            q.append(self.root)

        while len(q) > 0:
            cur = q.pop(0)
            yield cur
            for kid in cur.kids:
                q.append(kid)

    def all_leafs(self):
        for branch in self.all_branches():
            if len(branch.kids) == 0 and not branch.finalized:
                yield branch

    def depth(self):
        res = 0
        for branch in self.all_branches():
            res = max(res, branch.depth)
        return res


def _rand_sgn():
    return 1 - 2 * int(2 * random.random())


def gen_tree(bounding_rect, base_thickness, branch_factor_range, twistiness_range, max_depth):
    bound_w = bounding_rect[2]
    bound_h = bounding_rect[3]
    b_length_range = (bound_h / max_depth, bound_h / (2 * max_depth))
    min_thickness = 1

    root_angle = (10 - 20 * random.random())
    root = Branch(root_angle, base_thickness, b_length_range[0], 0)
    root_pos = (bounding_rect[0] + bound_w / 2, bounding_rect[1] + bound_h)
    tree = Tree(root, root_pos)

    while True:
        leafs = [l for l in tree.all_leafs()]
        if len(leafs) == 0:
            break

        cur_leaf = leafs[int(random.random() * len(leafs))]

        if cur_leaf.thickness <= min_thickness or cur_leaf.depth >= max_depth:
            cur_leaf.finalized = True
            continue

        depth_ratio = cur_leaf.depth / max_depth

        did_branch = False
        branch_chance = Utils.linear_interp(*branch_factor_range, depth_ratio)
        if random.random() < branch_chance:
            b1_angle = (1 - 2 * random.random()) * Utils.linear_interp(*twistiness_range, depth_ratio)
            b2_angle = (1 - 2 * random.random()) * Utils.linear_interp(*twistiness_range, depth_ratio)
            if abs(b2_angle - b1_angle) > 10:
                b1_weight = 1
                b2_weight = 1
                b_length = Utils.linear_interp(*b_length_range, depth_ratio)
                b1_thickness = max(min_thickness, b1_weight * base_thickness * (1 - depth_ratio))
                b2_thickness = max(min_thickness, b2_weight * base_thickness * (1 - depth_ratio))
                cur_leaf.kids.append(Branch(b1_angle, b1_thickness, b_length, cur_leaf.depth + 1))
                cur_leaf.kids.append(Branch(b2_angle, b2_thickness, b_length, cur_leaf.depth + 1))
                cur_leaf.finalized = True
                did_branch = True

        if not did_branch:
            b_angle = (1 - 2 * random.random()) * Utils.linear_interp(*twistiness_range, depth_ratio)
            b_length = Utils.linear_interp(*b_length_range, depth_ratio)
            b_thickness = max(min_thickness, base_thickness * (1 - depth_ratio))
            cur_leaf.kids.append(Branch(b_angle, b_thickness, b_length, cur_leaf.depth + 1))
            cur_leaf.finalized = True

    for branch in tree.all_branches():
        branch.finalized = True

    return tree


def _transform_helper(branch, branch_funct):
    new_kids = [_transform_helper(kid, branch_funct) for kid in branch.kids]
    new_branch = branch_funct(branch)
    new_branch.depth = branch.depth
    new_branch.finalized = True
    new_branch.kids = new_kids
    return new_branch


def transform(tree, branch_funct):
    new_root = _transform_helper(tree.root, branch_funct)
    return Tree(new_root, tree.root_pos)


def sway_tree(tree, sway_degree):
    total_depth = tree.depth()

    def sway_branch(branch):
        min_flex = 0
        max_flex = total_depth
        if branch.depth < min_flex or branch.depth > max_flex:
            return Branch(branch.angle, branch.thickness, branch.length, -1)
        else:
            d = (branch.depth - min_flex) / (total_depth - min_flex)
            flex = sway_degree * math.cos(3.1415 * d)
            return Branch(branch.angle + flex, branch.thickness, branch.length, -1)

    return transform(tree, sway_branch)


def _draw_branches_recurs(surface, base_pos, base_angle, branch):
    tot_angle = base_angle + branch.angle
    tot_rads = Utils.to_rads(tot_angle)

    branch_vector = Utils.set_length((math.cos(tot_rads), math.sin(tot_rads)), branch.length)
    end_pos = Utils.add(base_pos, branch_vector)
    color = (0, 0, 0)
    pygame.draw.line(surface, color, base_pos, end_pos, max(1, round(branch.thickness / 3)))

    for kid in branch.kids:
        _draw_branches_recurs(surface, end_pos, tot_angle, kid)


def draw_tree(surface, tree):
    _draw_branches_recurs(surface, tree.root_pos, 270, tree.root)


if __name__ == "__main__":
    grid_size = (12, 8)
    tree_size = (256, 256)
    test_surface = pygame.Surface((grid_size[0] * tree_size[0], grid_size[1] * tree_size[1]))
    test_surface.fill((255, 255, 255))

    branch_factor_range = (0.2, 0.45)
    twistiness_range = (10, 80)
    max_depth = 16
    base_thickness_range = (12, 25)

    for y in range(0, grid_size[1]):
        tree_rect = [0, y * tree_size[1], tree_size[0], tree_size[1]]
        base_thickness = Utils.linear_interp(*base_thickness_range, random.random())
        tree = gen_tree(tree_rect, base_thickness, branch_factor_range, twistiness_range, max_depth)
        for x in range(0, grid_size[0]):
            sway = 1 * math.sin(6.28 * x / grid_size[0])
            tilted_tree = sway_tree(tree, sway)
            tilted_tree.root_pos = (x * tree_size[0] + tree_size[0] // 2, (y + 1) * tree_size[1] - 1)
            draw_tree(test_surface, tilted_tree)

    pygame.image.save(test_surface, "test_trees.png")

