import pygame

UP = [pygame.K_w, pygame.K_UP]
JUMP = UP + [pygame.K_SPACE]
LEFT = [pygame.K_a, pygame.K_LEFT]
RIGHT = [pygame.K_d, pygame.K_RIGHT]
DOWN = [pygame.K_s, pygame.K_DOWN]
CROUCH = DOWN + [pygame.K_LSHIFT, pygame.K_RSHIFT]
ATTACK = [pygame.K_j, pygame.K_x]
INVENTORY = [pygame.K_r]
INTERACT = [pygame.K_k, pygame.K_e]
EXIT = [pygame.K_ESCAPE]


class InputState:
    def __init__(self):
        self._held_keys = {}  # keycode -> time pressed
        self._mouse_pos = (0, 0)
        self._mouse_down_time = None
        self._current_time = 0
    
    def set_key(self, key, held):
        if held and key not in self._held_keys:
                self._held_keys[key] = self._current_time
        elif not held and key in self._held_keys:
            del self._held_keys[key]
            
    def set_mouse_down(self, down):
        self._mouse_down_time = self._current_time if down else None 
            
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
    
    def mouse_is_held(self):
        return self._mouse_down_time is not None
    
    def mouse_held_time(self):
        if self._mouse_down_time is None:
            return -1
        else:
            return self._current_time - self._mouse_down_time  
    
    def mouse_was_pressed(self):
        return self.mouse_held_time() == 1 and self.mouse_in_window()
        
    def mouse_pos(self):
        return self._mouse_pos
        
    def mouse_in_window(self):
        return self._mouse_pos is not None    
            
    def was_pressed(self, key):
        """:param key - single key or list of keys"""
        return self.time_held(key) == 1
    
    def all_held_keys(self):
        return self._held_keys.keys()
        
    def update(self, global_state):
        self._current_time = global_state.tick_counter
