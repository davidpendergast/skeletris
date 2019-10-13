
from src.utils.util import Utils


class CameraModifier:

    def __init__(self, grid_rect):
        self._rect = grid_rect

    def x(self):
        return self._rect[0]

    def y(self):
        return self._rect[1]

    def w(self):
        return self._rect[2]

    def h(self):
        return self._rect[3]

    def get_rect(self):
        return self._rect

    def modify_camera_center(self, world, current_xy):
        return None

    def __contains__(self, pos):
        """:param item: a tuple (int x, int y)."""
        if isinstance(pos, tuple):
            return Utils.rect_contains(self.get_rect(), (pos[0], pos[1]))
        else:
            raise ValueError("pos must be grid coordinate, instead got: {}".format(pos))


class SnapToEntityModifier(CameraModifier):
    """A region that focuses the camera on a particular entity."""

    def __init__(self, grid_rect, target_entity, offset=(0, 0), max_move=(2000, 1500)):
        CameraModifier.__init__(self, grid_rect)
        self._target_uid = target_entity.get_uid()
        self._offset = offset
        self._max_move = max_move

    def modify_camera_center(self, world, current_xy):
        target_ent = world.get_entity(self._target_uid, onscreen=False)
        if target_ent is None or not target_ent.is_visible_in_world(world):
            return None

        center = target_ent.center()

        # if entity is outside of the region, it's best not to snap
        grid_pos = world.to_grid_coords(*center)
        if grid_pos not in self:
            return None

        new_xy = Utils.add(center, self._offset)
        if abs(new_xy[0] - current_xy[0]) > self._max_move[0]:
            return None

        if abs(new_xy[1] - current_xy[1]) > self._max_move[1]:
            return None

        return new_xy





