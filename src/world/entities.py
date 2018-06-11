import pygame
import random

import renderengine.img as img
import spriteref

class Entity:
    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self.rect = pygame.Rect(int(x), int(y), w, h)
        
    def x(self):
        return self.rect[0]
        
    def y(self):
        return self.rect[1]
        
    def set_x(self, x):
        self._x = x
        self.rect[0] = int(x)
    
    def set_y(self, y):
        self._y = y
        self.rect[1] = int(y)
        
    def get_updated_bundles(self):
        return []
        
    def update(self, world, input_state):
        pass 
        
    def should_remove_from_world(self):
        return False
        

class Player(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self._needs_bun_update = True
        self._bundle = img.ImageBundle(spriteref.player_idle_0, x, y, absolute=False, scale=2, depth=5)
        
    def get_updated_bundles(self):
        if self._needs_bun_update:
            self._needs_bun_update = False
            return [self._bundle]
        else:
            return []
            
    def update(self, world, input_state):
        pass 
            
            
        
    
