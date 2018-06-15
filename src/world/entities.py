import pygame
import random
import math

import src.renderengine.img as img
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.worldstate import World

class Entity:

    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self.rect = pygame.Rect(int(x), int(y), w, h)
        
    def x(self):
        return self.rect[0]
        
    def y(self):
        return self.rect[1]
        
    def w(self):
        return self.rect[2]
        
    def h(self):
        return self.rect[3]
        
    def center(self):
        return self.rect.center
        
    def set_x(self, x):
        self._x = x
        self.rect[0] = int(x)
    
    def set_y(self, y):
        self._y = y
        self.rect[1] = int(y)
        
    def _can_move(self, dx, dy, world):
        x1 = int(self._x + dx)
        x2 = int(self._x + self.w() + dx) 
        y1 = int(self._y + dy)
        y2 = int(self._y + self.h() + dy)
        return not (world.is_solid_at(x1, y1) or world.is_solid_at(x2-1, y1)
                or world.is_solid_at(x2-1, y2-1) or world.is_solid_at(x1, y2-1))
    
    def move(self, dx, dy, world=None, and_search=False):
        """
            returns: True if move was successful
        """
        if dx == 0 and dy == 0:
            return True
        
        if world is not None and not self._can_move(dx, dy, world):
            if not and_search:
                return False
            else:    
                self.set_x(self.x()) # elim decimal points
                self.set_y(self.y())             
                
                x_can_move = True
                y_can_move = True
                
                x_dir = 1 if dx > 0 else -1 if dx < 0 else 0
                y_dir = 1 if dy > 0 else -1 if dy < 0 else 0
                
                did_move = False
                
                while x_can_move or y_can_move:
                    if x_can_move:
                        x_can_move = self.move(x_dir, 0, world=world, and_search=False)
                        did_move = did_move or x_can_move
                        dx -= x_dir
                        if dx == 0 or dx*x_dir < 0:
                            x_can_move = False     
                    if y_can_move:
                        y_can_move = self.move(0, y_dir, world=world, and_search=False)
                        did_move = did_move or y_can_move
                        dy -= y_dir
                        if dy == 0 or dy*y_dir < 0:
                            y_can_move = False
                
                return did_move
                    
        self.set_x(self._x + dx)
        self.set_y(self._y + dy)
        return True
        
    def update(self, world, gs, input_state, render_engine):
        pass 

    def get_depth(self):
        """
            returns: value in [4, 5]
        """
        return 5 - max(0, min(1, (self.y() + self.h()) / 100000))  
    
    def is_player(self):
        return False
        
             

class Player(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self._bundle = img.ImageBundle(spriteref.player_idle_0, x, y, 
                absolute=False, scale=2, depth=self.get_depth())
        self.is_moving = False
        self.facing_right = True
        self.move_speed = 2
            
               
    def _regen_bundle(self, anim_tick):
        if self.is_moving:
            model = spriteref.player_move_all[anim_tick % len(spriteref.player_move_all)]
        else:
            model = spriteref.player_idle_all[(anim_tick // 2) % len(spriteref.player_idle_all)]
        x = self.x() - (model.width() * self._bundle.scale() - self.w()) // 2
        y = self.y() - (model.height() * self._bundle.scale() - self.h())
        depth = self.get_depth()
        xflip = not self.facing_right
        self._bundle = self._bundle.update(new_model=model, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip)
        return self._bundle
            
            
    def update(self, world, gs, input_state, render_engine):
        move_x = int(input_state.is_held(inputs.RIGHT)) - int(input_state.is_held(inputs.LEFT)) 
        move_y = int(input_state.is_held(inputs.DOWN)) - int(input_state.is_held(inputs.UP)) 
        
        self.is_moving = move_x != 0 or move_y != 0
        
        if move_x != 0 and move_y != 0:
            move_x /= 1.4142 
            move_y /= 1.4142   
        
        move_x *= self.move_speed
        move_y *= self.move_speed
        
        self.move(move_x, move_y, world=world, and_search=True)
        
        if move_x != 0:
            self.facing_right = move_x > 0
            
        render_engine.update(self._regen_bundle(gs.anim_tick), layer_id=gs.ENTITY_LAYER) 
        
        if input_state.was_pressed(inputs.INTERACT):
            print("player_pos={}, ({}, {})".format(self.rect, self._x, self._y))
        
    def is_player(self):
        return True
        

class Enemy(Entity):
    def __init__(self, x, y, sprites):
        Entity.__init__(self, x, y, 32, 32)
        self._bundle = img.ImageBundle(sprites[0], x, y, absolute=False, scale=2, depth=self.get_depth())
        self.facing_left = True
        self.sprites = sprites
        self.dir = [0, 0]
    
    def _regen_bundle(self, anim_tick):
        model = self.sprites[(anim_tick // 2) % len(self.sprites)]
        x = self.x() - (model.width() * self._bundle.scale() - self.w()) // 2
        y = self.y() - (model.height() * self._bundle.scale() - self.h())
        depth = self.get_depth()
        xflip = not self.facing_left
        self._bundle = self._bundle.update(new_model=model, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip)
        return self._bundle
        
    def update(self, world, gs, input_state, render_engine):
        if random.random() < 0.01:
            i = int(10 * random.random())
            if i >= 4:
                self.dir = [0, 0]
            else:
                self.dir = [[-1, 0], [1, 0], [0, 1], [0, -1]][i]
        
        x1 = self.x()
        x2 = self.x() + self.w()
        y1 = self.y()
        y2 = self.y() + self.h()
        
        if self.dir[0] < 0:
            if world.get_geo_at(x1 - 1, y1) == World.WALL or world.get_geo_at(x1 - 1, y2) == World.WALL:
                self.dir[0] = 1
        elif self.dir[0] > 0:
            if world.get_geo_at(x2 + 1, y1) == World.WALL or world.get_geo_at(x2 + 1, y2) == World.WALL:
                self.dir[0] = -1
        elif self.dir[1] > 0:
            if world.get_geo_at(x1, y2 + 1) == World.WALL or world.get_geo_at(x2, y2 + 1) == World.WALL:
                self.dir[1] = -1
        elif self.dir[1] < 0:
            if world.get_geo_at(x1, y1 - 1) == World.WALL or world.get_geo_at(x2, y1 - 1) == World.WALL:
                self.dir[1] = 1
        
        move_x = self.dir[0] * 0.65
        move_y = self.dir[1] * 0.65
        self.move(move_x, move_y, world=world, and_search=True)
        
        if move_x != 0:
            self.facing_left = move_x < 0 

        render_engine.update(self._regen_bundle(gs.anim_tick), layer_id=gs.ENTITY_LAYER) 
        

class ChestEntity(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.ticks_to_open = 60
        self.current_cooldown = self.ticks_to_open
        self._bundle = img.ImageBundle(spriteref.chest_closed, x, y, absolute=False, scale=2, depth=self.get_depth())
    
    def _regen_bundle(self):
        if self.is_open():
            model = spriteref.chest_open_1
        elif self.current_cooldown < self.ticks_to_open:
            model = spriteref.chest_open_0
        else:
            model = spriteref.chest_closed
            
        x = self.x() - (model.width() * self._bundle.scale() - self.w())
        y = self.y() - (model.height() * self._bundle.scale() - self.h())
        depth = self.get_depth()
        self._bundle = self._bundle.update(new_model=model, new_x=x, new_y=y, new_depth=depth)
        return self._bundle
        
    def is_open(self):
        return self.current_cooldown <= 0
    
    def _do_open(self, world):
        num_potions = 1 + int(random.random()*3)
        for _ in range(0, num_potions):
            c = self.center()
            angle = random.random() * 6.28 # 2pi-ish
            speed = 2 + random.random() * 3
            vel = (speed*math.cos(angle), speed*math.sin(angle))
            world.add(PotionEntity(c[0], c[1], vel=vel))
            
    
    def update(self, world, gs, input_state, render_engine):
        
        if not self.is_open():
            player_nearby = False
            p = world.get_player()
            if p is not None:
                dx = self.center()[0] - p.center()[0]
                dy = self.center()[1] - p.center()[1]
                player_nearby = dx*dx + dy*dy < 30*30
            
            if player_nearby:
                self.current_cooldown -= 1
            else:
                self.current_cooldown = self.ticks_to_open
                
            if self.is_open():
                self._do_open(world)           
             
        render_engine.update(self._regen_bundle(), layer_id=gs.ENTITY_LAYER) 
        
        
class ItemEntity(Entity):
    pass
    
    
class PotionEntity(Entity):
    def __init__(self, cx, cy, vel=(0, 0)):
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self._bundle = img.ImageBundle(spriteref.potion_small, x, y, absolute=False, scale=2, depth=5)
        self.pickup_delay = 45
        self.vel = [vel[0], vel[1]]
        self.fric = 0.90
    
    def _regen_bundle(self):
        model = self._bundle.model()
        x = self.x() - (model.width() * self._bundle.scale() - self.w())
        y = self.y() - (model.height() * self._bundle.scale() - self.h())
        depth = self.get_depth()
        self._bundle = self._bundle.update(new_model=model, new_x=x, new_y=y, new_depth=depth)   
        return self._bundle
        
    def can_pickup(self):
        return self.pickup_delay <= 0
        
    def update(self, world, gs, input_state, render_engine):
        if self.pickup_delay > 0:
            self.pickup_delay -= 1
              
        if self.vel[0] != 0:
            self.vel[0] = 0 if abs(self.vel[0]) < 0.05 else self.vel[0] * self.fric 
           
        if self.vel[1] != 0:
            self.vel[1] = 0 if abs(self.vel[1]) < 0.05 else self.vel[1] * self.fric
            
        self.move(*self.vel, world=world, and_search=True)
            
        render_engine.update(self._regen_bundle(), layer_id=gs.ENTITY_LAYER) 
        
    
