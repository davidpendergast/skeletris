
class InputState:

    _INSTANCE = None

    @staticmethod
    def create_instance():
        if InputState._INSTANCE is None:
            InputState._INSTANCE = InputState()
        return InputState._INSTANCE

    @staticmethod
    def get_instance():
        if InputState._INSTANCE is not None:
            return InputState._INSTANCE
        else:
            raise ValueError("cannot get InputState instance before creation")

    def __init__(self):
        self._pressed_this_frame = {}  # keycode -> num times
        self._pressed_last_frame = {}  # keycode -> num times
        self._held_keys = {}           # keycode -> time pressed
        self._mouse_pos = (0, 0)
        self._mouse_moved_at_time = -1
        self._current_time = 0
    
    def set_key(self, key, held):
        if held:
            if key not in self._pressed_last_frame:
                self._pressed_last_frame[key] = 0
            self._pressed_last_frame[key] += 1

        if held and key not in self._held_keys:
                self._held_keys[key] = self._current_time
        elif not held and key in self._held_keys:
            del self._held_keys[key]

    def to_key_code(self, mouse_button):
        return "MOUSE_BUTTON_" + str(mouse_button)

    def set_mouse_down(self, down, button=1):
        keycode = self.to_key_code(button)
        self.set_key(keycode, down)

    def set_mouse_pos(self, pos):
        if self._mouse_pos != pos:
            self._mouse_moved_at_time = self._current_time
        self._mouse_pos = pos
    
    def is_held(self, key):
        """:param key - single key or list of keys"""
        if isinstance(key, list):
            return any(map(lambda k: self.is_held(k), key))
        else:
            return key in self._held_keys
    
    def time_held(self, key):
        """:param key - single key or list of keys"""
        if isinstance(key, list):
            return max(map(lambda k: self.time_held(k), key))
        else:
            if key not in self._held_keys:
                return -1
            else:
                return self._current_time - self._held_keys[key]
    
    def mouse_is_held(self, button=1):
        keycode = self.to_key_code(button)
        return self.is_held(keycode)
    
    def mouse_held_time(self, button=1):
        keycode = self.to_key_code(button)
        return self.time_held(keycode)

    def mouse_was_pressed(self, button=1):
        keycode = self.to_key_code(button)
        return self.was_pressed(keycode) and self.mouse_in_window()
        
    def mouse_pos(self):
        return self._mouse_pos

    def mouse_moved(self):
        return self._mouse_moved_at_time == self._current_time - 1
        
    def mouse_in_window(self):
        return self._mouse_pos is not None    
            
    def was_pressed(self, key):
        """:param key - single key or list of keys"""
        if isinstance(key, list):
            for k in key:
                if k in self._pressed_this_frame and self._pressed_this_frame[k] > 0:
                    return True
            return False
        else:
            return key in self._pressed_this_frame and self._pressed_this_frame[key] > 0
    
    def all_held_keys(self):
        return self._held_keys.keys()

    def all_pressed_keys(self):
        return [x for x in self._pressed_this_frame if self._pressed_this_frame[x] > 0]

    def was_anything_pressed(self):
        if len(self.all_pressed_keys()) > 0:
            return True
        else:
            for i in range(0, 3):
                if self.mouse_was_pressed(button=i):
                    return True
        return False
        
    def update(self, current_time):
        """Remember that this gets called *after* inputs are passed in, and *before* game updates occur."""
        self._current_time = current_time

        self._pressed_this_frame.clear()
        self._pressed_this_frame.update(self._pressed_last_frame)
        self._pressed_last_frame.clear()
