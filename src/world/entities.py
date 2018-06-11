import pygame
import random

import renderengine.img as img

class Entity:
    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self._cur_img = 0
        
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
        
    def get_image_bundles(self):
        return img.player_move_all[self._cur_img]
        
    def update(self, world, input_state):
        if random.random() < 0.05:
            self._cur_img = (self._cur_img + 1) % 4
        else:
            if random.random() < 0.25:
                self.set_x(self._x + random.random() - 0.5)  
                self.set_y(self._y + random.random() - 0.5)  
        
    def should_remove_from_world(self):
        return False
        
        
class Wall:
    pass
        
    
