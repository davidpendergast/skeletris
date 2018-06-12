import pygame
import random

import renderengine.img as img
import spriteref
import inputs

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
        
    def update(self, world, global_state, input_state, render_engine):
        pass 
        

class Player(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self._needs_bun_update = True
        self._bundle = img.ImageBundle(spriteref.player_idle_0, x, y, 
                absolute=False, scale=2, depth=5)
        self.is_moving = False
        self.facing_left = True
            
            
    def _regen_bundle(self, anim_tick):
        if self.is_moving:
            model = spriteref.player_move_all[anim_tick % len(spriteref.player_move_all)]
        else:
            model = spriteref.player_idle_all[anim_tick % len(spriteref.player_idle_all)]
        x = self.x()
        y = self.y()
        self._bundle = self._bundle.update(new_model=model, new_x=x, new_y=y)
        return self._bundle
            
            
    def update(self, world, global_state, input_state, render_engine):
        move_x = int(input_state.is_held(inputs.RIGHT)) - int(input_state.is_held(inputs.LEFT)) 
        move_y = int(input_state.is_held(inputs.DOWN)) - int(input_state.is_held(inputs.UP)) 
        
        self.is_moving = move_x != 0 or move_y != 0
        
        if move_x != 0 and move_y != 0:
            move_x /= 1.4142 
            move_y /= 1.4142   
        
        self.set_x(self._x + move_x * 1.5)
        self.set_y(self._y + move_y * 1.5)
        render_engine.update(self._regen_bundle(global_state.anim_tick)) 
            
            
        
    
