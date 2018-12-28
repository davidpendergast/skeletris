
class InputState:

    def __init__(self):
        self._held_keys = {}  # keycode -> time pressed
        self._mouse_pos_last_update = (0, 0)
        self._mouse_pos = (0, 0)
        self._current_time = 0
    
    def set_key(self, key, held):
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
        return self._mouse_pos != self._mouse_pos_last_update
        
    def mouse_in_window(self):
        return self._mouse_pos is not None    
            
    def was_pressed(self, key):
        """:param key - single key or list of keys"""
        return self.time_held(key) == 1
    
    def all_held_keys(self):
        return self._held_keys.keys()

    def all_pressed_keys(self):
        return [x for x in self.all_held_keys() if self.was_pressed(x)]
        
    def update(self, global_state):
        self._mouse_pos_last_update = self.mouse_pos
        self._current_time = global_state.tick_counter
