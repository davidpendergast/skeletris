
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
        """returns: (x_pos, y_pos, strength)"""
        return None

    def __contains__(self, pos):
        """pos: a tuple (int x, int y)."""
        if isinstance(pos, tuple):
            return Utils.rect_contains(self.get_rect(), (pos[0], pos[1]))
        else:
            raise ValueError("pos must be grid coordinate, instead got: {}".format(pos))


class SnapToEntityModifier(CameraModifier):
    """A region that focuses the camera on a particular entity."""

    def __init__(self, grid_rect, target_entity, offset=(0, 0), max_move=(2000, 1500),
                 fade_in_time=5, fade_out_time=5):
        CameraModifier.__init__(self, grid_rect)
        self._target_uid = target_entity.get_uid()
        self._offset = offset
        self._max_move = max_move

        # bleh we'd rather not have state in here but we kinda need it to handle fading
        # in and out of camera snaps...
        self._last_target_pos = None

        # some clever math here, just trust me
        self._fade_in_inc = fade_out_time  # intentionally swapped
        self._fade_out_inc = fade_in_time
        self._total_fade_time = fade_in_time * fade_out_time
        self._fade_count = 0

    def modify_camera_center(self, world, current_xy):
        target_ent = world.get_entity(self._target_uid, onscreen=False)
        if target_ent is None or not target_ent.is_visible_in_world(world):
            center = None
        else:
            center = target_ent.center()

            # if entity is outside of the region, it's best not to snap
            grid_pos = world.to_grid_coords(*center)
            if grid_pos not in self:
                center = None

        new_xy = None

        if center is not None:
            new_xy = Utils.add(center, self._offset)
            if abs(new_xy[0] - current_xy[0]) > self._max_move[0]:
                new_xy = None

            if abs(new_xy[1] - current_xy[1]) > self._max_move[1]:
                new_xy = None

        if new_xy is not None:
            self._last_target_pos = new_xy
            self._fade_count = min(self._total_fade_time, self._fade_count + self._fade_in_inc)
        else:
            self._fade_count = max(0, self._fade_count - self._fade_out_inc)

        if self._last_target_pos is None or self._fade_count <= 0:
            return None
        else:
            fade = self._fade_count / self._total_fade_time
            v = Utils.sub(self._last_target_pos, current_xy)
            v = Utils.mult(v, fade)
            return Utils.round(Utils.add(current_xy, v))






