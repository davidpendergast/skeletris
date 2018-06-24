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
            self._shadow = img.ImageBundle(self.get_shadow_sprite(), 0, 0, layer=spriteref.SHADOW_LAYER,
                scale=2, depth=-1)
        
        if self._shadow is not None:    
            sh_model = self.get_shadow_sprite()
            if sh_model is None:
                # TODO no way to del shadows
                return
            
            sh_scale = self._shadow.scale()    
            sh_x = self.x() - (sh_model.width() * sh_scale - self.w()) // 2
            sh_y = self.y() + self.h() - (sh_model.height() * sh_scale // 2)
            self._shadow = self._shadow.update(new_model=sh_model, 
                    new_x=sh_x, new_y=sh_y)
    
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
        
    def is_enemy(self):
        return False


class AnimationEntity(Entity):

        def __init__(self, x, y, sprites, duration, layer_id, scale=2):
            Entity.__init__(self, x, y, 8, 8)
            self.initial_duration = duration
            self.duration = duration
            self.sprites = sprites
            self.layer_id = layer_id
            self.scale = scale
            self._img = None

        def cleanup(self, gs, render_engine):
            if self._img is not None:
                render_engine.remove(self._img)

        def update_images(self, gs):
            progress = min(1, max(0, 1 - self.duration / self.initial_duration))
            idx = int(progress * len(self.sprites))
            sprite = self.sprites[idx]
            x = self.x() - (sprite.width() * 2 - self.w()) // 2
            y = self.y() - (sprite.height() * 2 - self.h()) // 2

            if self._img is None:
                self._img = img.ImageBundle(sprite, x, y, layer=self.layer_id, scale=self.scale, depth=0)
            else:
                self._img = self._img.update(new_model=sprite, new_x=x, new_y=y)

        def update(self, world, gs, input_state, render_engine):
            if self.duration <= 0:
                world.remove(self)
            else:
                self.update_images(gs)
                render_engine.update(self._img)
                self.duration -= 1


class AttackCircleArt(AnimationEntity):

    def __init__(self, cx, cy, duration):
        AnimationEntity.__init__(self, cx - 4, cy - 4, spriteref.att_circles, duration, spriteref.SHADOW_LAYER)
        self.initial_duration = duration
        self.duration = duration
        self._img = None
                 

class Player(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 12)
        self._img = None
        self._shadow_sprite = spriteref.medium_shadow 
    
    def set_shadow_sprite(self, sprite):
        self._shadow_sprite = sprite
        
    def get_shadow_sprite(self):
        return self._shadow_sprite
               
    def update_images(self, sprite, facing_right):        
        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=2, depth=self.get_depth())

        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (sprite.height() * self._img.scale() - self.h())        
        
        depth = self.get_depth()
        xflip = not facing_right
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip)
        
        super().update_images(0)  # get the shadow
            
    def update(self, world, gs, input_state, render_engine):
        render_engine.update(self._img)
        render_engine.update(self._shadow)
        
    def is_player(self):
        return True
 
 
class Enemy(Entity):

    def __init__(self, x, y, state):
        Entity.__init__(self, x, y, 32, 32)
        self.state = state
        self._img = None
        
    def get_shadow_sprite(self):
        return spriteref.large_shadow 
    
    def update_images(self, sprite, facing_left, color=(1, 1, 1)):
        if self._img is None:
            self._img = img.ImageBundle(sprite, 0, 0, layer=spriteref.ENTITY_LAYER, scale=2)
        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (sprite.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        xflip = not facing_left
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, 
                new_depth=depth, new_xflip=xflip, new_color=color)
        
    def cleanup(self, gs, render_engine):
        render_engine.remove(self._img)
        render_engine.remove(self._shadow)
        
    def update(self, world, gs, input_state, render_engine):
        self.state.update(self, world, gs, input_state)
        super().update_images(gs.anim_tick) # TODO - shadows are dumb
        
        render_engine.update(self._img)
        render_engine.update(self._shadow)
        
    def is_enemy(self):
        return True
        

class ChestEntity(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.ticks_to_open = 60
        self.current_cooldown = self.ticks_to_open
        
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

        if self._img is None:
            self._img = img.ImageBundle(spriteref.chest_closed, 0, 0, layer=spriteref.ENTITY_LAYER)

        x = self.x() - (model.width() * self._img.scale() - self.w())
        y = self.y() - (model.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        self._img = self._img.update(new_model=model, new_scale=2, new_x=x, new_y=y, new_depth=depth)
        
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
        render_engine.update(self._img)
        render_engine.update(self._shadow)
        
        
class ItemEntity(Entity):
    def __init__(self, item, cx, cy, vel=None):
        self.item = item
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self._cube_imgs = []
        self.pickup_delay = 45
        self.vel = [vel[0], vel[1]] if vel is not None else ItemEntity.rand_vel()
        self.fric = 0.90
        self.bounce_offset = int(random.random() * 100)
        
        # for moving away from other stuff
        self.push_radius = 20
        self.situated = False
        self.unsituated_time = 0

    @staticmethod
    def rand_vel(speed=None, direction=None):
        speed = speed if speed is not None else 2 + random.random() * 3
        if direction is None:
            direction = (0, 0) # becomes random
        direction = Utils.set_length(direction, 1.0)
        return [speed*direction[0], speed*direction[1]]
        
    def get_shadow_sprite(self):
        return spriteref.small_shadow
    
    def get_item(self):
        return self.item
        
    def is_item(self):
        return True
            
    def update_images(self, anim_tick):
        if len(self._cube_imgs) == 0:
            for c in self.item.cubes:
                c_img = img.ImageBundle(spriteref.item_piece_small, 0, 0, layer=spriteref.ENTITY_LAYER,
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
            render_engine.update(c_img)
        render_engine.update(self._shadow)
        
    def cleanup(self, gs, render_eng):
        for c_img in self._cube_imgs:
            render_eng.remove(c_img)
        render_eng.remove(self._shadow)
        

class PotionEntity(Entity):
    def __init__(self, cx, cy, vel=None):
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self._img = img.ImageBundle(spriteref.potion_small, x, y, layer=spriteref.ENTITY_LAYER,
               scale=2, depth=5)
        self.pickup_delay = 45
        self.vel = [vel[0], vel[1]] if vel is not None else ItemEntity.rand_vel()
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
        render_engine.update(self._img)


class DoorEntity(Entity):

    def __init__(self, grid_x, grid_y):
        Entity.__init__(self, grid_x*64, grid_y*64, 64, 64)
        self._is_horz = None
        self.sprites = None
        self.delay_duration = 45
        self.delay_count = 0
        self.opening_duration = 15
        self.opening_count = 0

        self.open_radius = 75

    def update_images(self):
        if self._is_horz is None:
            print("tried to update door image before _is_horz was calculated...")
            return

        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=4)

        if self.delay_count > 0:
            sprite = self.sprites[1]
        elif self.opening_count > 0:

            n = len(self.sprites) - 2
            idx = 2 + int(n * min(0.99, self.opening_count / self.opening_duration))
            sprite = self.sprites[idx]
        else:
            sprite = self.sprites[0]

        x = self.x()
        y = self.y() - (sprite.height() * self._img.scale() - self.h())
        depth = 100
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, new_depth=depth)

    def _calc_is_horz(self, world):
        solid_up = world.is_solid_at(*Utils.sub(self.center(), (0, self.h())))
        solid_down = world.is_solid_at(*Utils.add(self.center(), (0, self.h())))
        if solid_up and solid_down:
            return True

        solid_left = world.is_solid_at(*Utils.sub(self.center(), (self.w(), 0)))
        solid_right = world.is_solid_at(*Utils.add(self.center(), (self.w(), 0)))
        if solid_left and solid_right:
            return False

        # invalid door, hopefully shouldn't happen
        return random.random() < 0.5

    def cleanup(self, gs, render_engine):
        if self._img is not None:
            render_engine.remove(self._img)

    def update(self, world, gs, input_state, render_engine):
        if self._is_horz is None:
            self._is_horz = self._calc_is_horz(world)
            self.sprites = spriteref.door_h if self._is_horz else spriteref.door_v

        if self.opening_count >= self.opening_duration:
            # XXX kinda jank, we set the geo value to FLOOR when the door is set to open
            # but we don't update the surrounding tile sprites until the opening animation
            # is finished. This allows the player to pass through while the door is partially
            # open, while also keeping the wall sprites correct.
            #
            # TODO this <will> cause bugs in the future
            grid_xy = world.to_grid_coords(*self.center())
            world.update_geo_bundle(*grid_xy, and_neighbors=True)
            world.remove(self)
        elif self.opening_count > 0:
            self.opening_count += 1
        else:
            p = world.get_player()
            if p is not None and Utils.dist(p.center(), self.center()) <= self.open_radius:
                self.delay_count += 1
                if self.delay_count >= self.delay_duration:
                    # door will open now
                    self.delay_count = 0
                    self.opening_count = 1
                    grid_xy = world.to_grid_coords(*self.center())
                    world.set_geo(*grid_xy, World.FLOOR)
            else:
                self.delay_count = 0

        self.update_images()
        render_engine.update(self._img)


class ExitEntity(Entity):

    def __init__(self, x, y):
        pass
    
