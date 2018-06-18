import pygame
import random
import math

import src.renderengine.img as img
import src.game.spriteref as spriteref
import src.game.inputs as inputs
from src.world.worldstate import World
from src.items.item import ItemFactory
from src.utils.util import Utils

class Entity:

    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self._img = None     # main image: ImageBundle
        self._shadow = None  # shadow image: ImageBundle
        
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
        
    def cleanup(self, gs, render_engine):
        pass

    def update_images(self, anim_tick):
        if self._shadow is None and self.get_shadow_sprite() is not None:
            self._shadow = img.ImageBundle(self.get_shadow_sprite(), 0, 0,
                scale=2, depth=-1)
        
        if self._shadow is not None:    
            sh_model = self._shadow.model()    
            sh_scale = self._shadow.scale()    
            sh_x = self.x() - (sh_model.width() * sh_scale - self.w()) // 2
            sh_y = self.y() + self.h() - (sh_model.height() * sh_scale // 2)
            self._shadow = self._shadow.update(new_x=sh_x, new_y=sh_y)
    
    def get_shadow_sprite(self):
        return None

    def get_depth(self):
        """
            returns: value in [4, 5]
        """
        return 5 - max(0, min(1, (self.y() + self.h()) / 100000))  
    
    def is_player(self):
        return False
        
    def is_item(self):
        return False
        
    def is_chest(self):
        return False
        

class Player(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 12)
        self._img = img.ImageBundle(spriteref.player_idle_0, x, y, 
                scale=2, depth=self.get_depth())
        self.is_moving = False
        self.facing_right = True
        self.move_speed = 2
        
    def get_shadow_sprite(self):
        return spriteref.medium_shadow    
    
    def raw_center(self):
        """returns: unrounded center coordinates"""
        return (self._x + self.w(), self._y + self.h())
               
    def update_images(self, anim_tick):
        if self.is_moving:
            model = spriteref.player_move_all[anim_tick % len(spriteref.player_move_all)]
        else:
            model = spriteref.player_idle_all[(anim_tick // 2) % len(spriteref.player_idle_all)]
        
        x = self.x() - (model.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (model.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        xflip = not self.facing_right
        self._img = self._img.update(new_model=model, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip)
        
        super().update_images(anim_tick) # get the shadow
  
            
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
        
        self.update_images(gs.anim_tick)
        render_engine.update(self._img, layer_id=gs.ENTITY_LAYER) 
        render_engine.update(self._shadow, layer_id=gs.SHADOW_LAYER) 
        
        if input_state.was_pressed(inputs.INTERACT):
            print("player_pos={}, ({}, {})".format(self.rect, self._x, self._y))
        
    def is_player(self):
        return True
        

class Enemy(Entity):
    def __init__(self, x, y, sprites):
        Entity.__init__(self, x, y, 32, 32)
        self._img = img.ImageBundle(sprites[0], x, y, scale=2, depth=self.get_depth())
        self.facing_left = True
        self.sprites = sprites
        self.dir = [0, 0]
        
    def get_shadow_sprite(self):
        return spriteref.large_shadow 
    
    def update_images(self, anim_tick):
        model = self.sprites[(anim_tick // 2) % len(self.sprites)]
        x = self.x() - (model.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (model.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        xflip = not self.facing_left
        self._img = self._img.update(new_model=model, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip)
                
        super().update_images(anim_tick)
        
        
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

        self.update_images(gs.anim_tick)
        render_engine.update(self._img, layer_id=gs.ENTITY_LAYER) 
        render_engine.update(self._shadow, layer_id=gs.SHADOW_LAYER)
        

class ChestEntity(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.ticks_to_open = 60
        self.current_cooldown = self.ticks_to_open
        self._img = img.ImageBundle(spriteref.chest_closed, x, y, scale=2, depth=self.get_depth())
        
    def is_chest(self):
        return True
    
    def get_shadow_sprite(self):
        return spriteref.chest_shadow
        
    def update_images(self, anim_tick):
        if self.is_open():
            model = spriteref.chest_open_1
        elif self.current_cooldown < self.ticks_to_open:
            model = spriteref.chest_open_0
        else:
            model = spriteref.chest_closed
            
        x = self.x() - (model.width() * self._img.scale() - self.w())
        y = self.y() - (model.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        self._img = self._img.update(new_model=model, new_x=x, new_y=y, new_depth=depth)
        
        super().update_images(anim_tick)
        sh_x = self._shadow.x()
        sh_y = self._shadow.y()
        sh_s = self._shadow.scale()
        self._shadow = self._shadow.update(new_x=(sh_x + 7*sh_s), new_y=(sh_y - 2*sh_s))
        
          
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
            
        for _ in range(0, 3):
            c = self.center()
            angle = random.random() * 6.28 # 2pi-ish
            speed = 2 + random.random() * 3
            vel = (speed*math.cos(angle), speed*math.sin(angle))
            item = ItemFactory.gen_item()
            world.add(ItemEntity(item, c[0], c[1], vel=vel))
            
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
             
        self.update_images(gs.anim_tick)
        render_engine.update(self._img, layer_id=gs.ENTITY_LAYER) 
        render_engine.update(self._shadow, layer_id=gs.SHADOW_LAYER)
        
        
class ItemEntity(Entity):
    def __init__(self, item, cx, cy, vel=None):
        self.item = item
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self._cube_imgs = []
        self.pickup_delay = 45
        self.vel = [vel[0], vel[1]] if vel is not None else self.rand_vel()
        self.fric = 0.90
        self.bounce_offset = int(random.random() * 100)
        
        # for moving away from other stuff
        self.push_radius = 20
        self.situated = False
        self.unsituated_time = 0
        
    def rand_vel(self):
        angle = random.random() * 6.28 # 2pi-ish
        speed = 2 + random.random() * 3
        return [speed*math.cos(angle), speed*math.sin(angle)]
        
    def get_shadow_sprite(self):
        return spriteref.small_shadow
    
    def get_item(self):
        return self.item
        
    def is_item(self):
        return True
            
    def update_images(self, anim_tick):
        if len(self._cube_imgs) == 0:
            for c in self.item.cubes:
                c_img = img.ImageBundle(spriteref.item_piece_small, 0, 0, 
                        scale=2, color=self.item.color)
                self._cube_imgs.append(c_img)
        
        bounce = round(2*math.cos((anim_tick + self.bounce_offset) // 2))
        
        item_w = self.item.w()
        item_h = self.item.h()
        
        for i in range(0, len(self._cube_imgs)):
            cube = self.item.cubes[i]
            c_img = self._cube_imgs[i]
            
            model = c_img.model()
            c_w = model.width() * c_img.scale()
            c_h = model.height() * c_img.scale()

            x = (self.x() + self.w() // 2) - (c_w * item_w // 2) + cube[0] * c_w
            y = (self.y() + self.h()) - c_h * item_h + cube[1] * c_h - (2 - bounce)
            depth = self.get_depth()
            self._cube_imgs[i] = c_img.update(new_model=model, 
                    new_x=x, new_y=y, new_depth=depth)   
                    
        super().update_images(anim_tick)
                    
    def _handle_pushes(self, world):
          if not self.situated:
            nearby_ents = world.entities_in_circle(self.center(), self.push_radius)
            other_items = [i for i in nearby_ents if (i.is_item() or i.is_chest()) and i is not self]
            if len(other_items) > 0 and Utils.mag(self.vel) < 2:
                for i in other_items:
                    if i.is_item() and i.can_unsituate():
                        i.situated = False # 'wake up' the other items too
                i = other_items[int(random.random()*len(other_items))] 
                direction = Utils.sub(self.center(), i.center())
                push = Utils.set_length(direction, 0.25)
                self.vel[0] += push[0]
                self.vel[1] += push[1]
            
            if len(other_items) == 0:
                self.situated = True
                self.unsituated_time = 0
            elif not self.can_unsituate():
                self.situated = True 
                # means it's probably crammed in a corner,
                # don't reset unsituated_time so other items
                # will stop waking it up 
                   
    def can_unsituate(self):
        return self.unsituated_time < 500      
          
    def update(self, world, gs, input_state, render_engine):
        if self.pickup_delay > 0:
            self.pickup_delay -= 1
        
        self._handle_pushes(world)
               
        if self.vel[0] != 0:
            self.vel[0] = 0 if abs(self.vel[0]) < 0.05 else self.vel[0] * self.fric 
           
        if self.vel[1] != 0:
            self.vel[1] = 0 if abs(self.vel[1]) < 0.05 else self.vel[1] * self.fric
            
        self.move(*self.vel, world=world, and_search=True)
            
        self.update_images(gs.anim_tick)
        for c_img in self._cube_imgs:
            render_engine.update(c_img, layer_id=gs.ENTITY_LAYER) 
        render_engine.update(self._shadow, layer_id=gs.SHADOW_LAYER)
        
    def cleanup(self, gs, render_eng):
        for c_img in self._cube_imgs:
            render_eng.remove(c_img, layer_id=gs.ENTITY_LAYER) 
        render_eng.remove(self._shadow, layer_id=gs.SHADOW_LAYER)
        
            
    
    
class PotionEntity(Entity):
    def __init__(self, cx, cy, vel=(0, 0)):
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self._img = img.ImageBundle(spriteref.potion_small, x, y, 
               scale=2, depth=5)
        self.pickup_delay = 45
        self.vel = [vel[0], vel[1]]
        self.fric = 0.90
    
    def update_images(self):
        model = self._img.model()
        x = self.x() - (model.width() * self._img.scale() - self.w())
        y = self.y() - (model.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        self._img = self._img.update(new_model=model, new_x=x, new_y=y, new_depth=depth)   
        
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
            
        self.update_images()
        render_engine.update(self._img, layer_id=gs.ENTITY_LAYER) 
        
    
