import pygame
import random
import math

import src.renderengine.img as img
from src.ui.ui import TextImage
import src.game.spriteref as spriteref
from src.world.worldstate import World
from src.utils.util import Utils
from src.game.loot import LootFactory
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.events as events
from src.game.updatable import Updateable
import src.game.globalstate as gs
import src.game.sound_effects as sound_effects

ENTITY_UID_COUNTER = 0


class Entity(Updateable):

    @staticmethod
    def gen_uid():
        global ENTITY_UID_COUNTER
        ENTITY_UID_COUNTER += 1
        return ENTITY_UID_COUNTER - 1

    def __init__(self, x, y, w, h):
        self._uid = Entity.gen_uid()
        self._x = x
        self._y = y
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self._img = None     # main image: ImageBundle
        self._shadow = None  # shadow image: ImageBundle
        self._last_vel = (0, 0)
        self._alive = False  # World sets this upon adding/removing the entity
        
    def x(self):
        return self.rect[0]
        
    def y(self):
        return self.rect[1]
        
    def w(self):
        return self.rect[2]
        
    def h(self):
        return self.rect[3]

    def get_vel(self):
        return self._last_vel
        
    def center(self):
        return self.rect.center

    def set_center(self, cx, cy):
        self.set_x(cx - self.w() / 2)
        self.set_y(cy - self.h() / 2)
        
    def set_x(self, x):
        self._x = x
        self.rect[0] = int(x)
        self._last_vel = (0, 0)
    
    def set_y(self, y):
        self._y = y
        self.rect[1] = int(y)
        self._last_vel = (0, 0)

    def valid_to_stand_on(self, world, x, y):
        return not world.is_solid_at(x, y) and world.get_geo_at(x, y) != World.EMPTY
        
    def _can_move(self, dx, dy, world):
        x1 = int(self._x + dx)
        x2 = int(self._x + self.w() + dx) 
        y1 = int(self._y + dy)
        y2 = int(self._y + self.h() + dy)
        return (self.valid_to_stand_on(world, x1, y1) and self.valid_to_stand_on(world, x2-1, y1)
                and self.valid_to_stand_on(world, x2-1, y2-1) and self.valid_to_stand_on(world, x1, y2-1))
    
    def move(self, dx, dy, world=None, and_search=False):
        """
            returns: True if move was successful
        """
        if dx == 0 and dy == 0:
            self._last_vel = (0, 0)
            return True
        
        if world is not None and not self._can_move(dx, dy, world):
            if not and_search:
                return False
            else:    
                self.set_x(self.x())  # elim decimal points
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
        self._last_vel = (dx, dy)
        return True
        
    def update(self, world, input_state, render_engine):
        pass

    def alive(self):
        """whether the entity is in a World"""
        return self._alive
        
    def cleanup(self, render_engine):
        for bundle in self.all_bundles():
            render_engine.remove(bundle)

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

    def is_pickup(self):
        return False

    def is_attack_pickup(self):
        return False

    def is_potion(self):
        return False

    def is_save_station(self):
        return False

    def is_npc(self):
        return False

    def is_exit(self):
        return False

    def is_door(self):
        return False

    def is_interactable(self):
        return False

    def interact(self, world):
        pass

    def interact_text(self):
        return None

    def interact_radius(self):
        return 64

    def is_pushable(self):
        return isinstance(self, Pushable)

    def can_damage(self, other):
        return ((self.is_player() and other.is_enemy()) or
                (self.is_enemy() and other.is_player()))

    def get_actorstate(self):
        return None

    def __eq__(self, other):
        return other is not None and self._uid == other._uid

    def __hash__(self):
        return self._uid

    def get_uid(self):
        return self._uid

    def all_bundles(self, extras=[]):
        if self._shadow is not None:
            yield self._shadow
        if self._img is not None:
            yield self._img

        for bun in extras:
            if bun is not None:
                yield bun


class Pushable:

    class Push:
        def __init__(self, vector, duration):
            self.vector = tuple(vector)
            self.duration = duration
            self.tick_count = 0

        def __hash__(self):
            return hash((self.vector[0], self.vector[1], self.duration))

    def __init__(self):
        self.active_pushes = set()

    def update_pushes(self):
        to_remove = []
        for push in self.active_pushes:
            push.tick_count += 1
            if push.tick_count >= push.duration:
                to_remove.append(push)

        if len(to_remove) > 0:
            for push in to_remove:
                self.active_pushes.remove(push)

    def get_total_push(self, max_vel=None):
        if len(self.active_pushes) == 0:
            return (0, 0)
        else:
            x_sum = 0
            y_sum = 0

            for push in self.active_pushes:
                x_sum += push.vector[0] * max(0, 1 - push.tick_count / push.duration)
                y_sum += push.vector[1] * max(0, 1 - push.tick_count / push.duration)

            vel = (x_sum, y_sum)
            if max_vel is not None and Utils.mag(vel) > max_vel:
                return Utils.set_length(vel, max_vel)
            else:
                return vel

    def push(self, vector, duration):
        self.active_pushes.add(Pushable.Push(vector, duration))


class ProjectileEntity(Entity):

    def __init__(self, cx, cy, radius, source, duration, source_state, attack):
        Entity.__init__(self, cx-radius, cy-radius, radius*2, radius*2)
        self._sprite_offset = (0, 0)
        self._radius = radius
        self._source = source
        self._tick_count = 0
        self._duration = duration
        self._attack = attack
        self._source_state = source_state
        self._poll_rate = 0.1

    def _update_images(self, sprite, color):
        Entity.update_images(self, gs.get_instance().anim_tick)

        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)
        self._img = self._img.update(new_model=sprite)

        x = self.center()[0] - self._img.width() // 2 + self._sprite_offset[0]
        y = self.center()[1] - self._img.height() // 2 + self._sprite_offset[1]

        self._img = self._img.update(new_color=color, new_x=x, new_y=y)

    def update(self, world, input_state, render_engine):
        was_removed = False
        if not gs.get_instance().world_updates_paused():
            if 0 < self._duration <= self._tick_count:
                world.remove(self)
                was_removed = True
            else:
                vel = self.get_vel()

                self.move(vel[0], vel[1])

                # check every five-ish ticks, lol
                if random.random() < self._poll_rate:
                    potential_hits = self.get_potential_hits(world)
                    for e in potential_hits:
                        self_destroyed = self.touched_entity(e, world)
                        if self_destroyed:
                            break

        if not was_removed:
            color = self.get_color(world)
            spr = self.get_sprite(world)
            self._update_images(spr, color)

        if not gs.get_instance().world_updates_paused():
            self._tick_count += 1

    def get_potential_hits(self, world):
        res = []
        in_range = world.entities_in_circle(self.center(), self._radius)
        for e in in_range:
            if self.get_source().can_damage(e):
                res.append(e)
        random.shuffle(res)
        return res

    def get_progress(self):
        if self._duration > 0:
            return Utils.bound(self._tick_count / self._duration, 0, 0.999)
        else:
            return 0.0

    def get_vel(self):
        return (0, 0)

    def get_sprite(self, world):
        return spriteref.explosions

    def get_color(self, world):
        return (1, 1, 1)

    def get_radius(self):
        return self._radius

    def set_sprite_offset(self, offset):
        self._sprite_offset = offset

    def touched_entity(self, entity, world):
        return False

    def get_shadow_sprite(self):
        return spriteref.small_shadow

    def get_attack(self):
        return self._attack

    def get_source(self):
        return self._source

    def get_source_state(self):
        return self._source_state


class MinionProjectile(ProjectileEntity):

    def __init__(self, cx, cy, source, target, duration, color, source_state, attack):
        ProjectileEntity.__init__(self, cx, cy, 24, source, duration, source_state, attack)
        self._target = target
        self._color = color
        self._min_speed = 1.25
        self._max_speed = 2.5
        self._vel = Utils.rand_vec(self._min_speed)

    def get_sprite(self, world):
        return spriteref.floaty_guys[gs.get_instance().anim_tick % 2]

    def get_color(self, world):
        return self._color

    def get_vel(self):
        prog = self.get_progress()
        if prog < 0.15:
            pass
        elif prog < 0.35:
            a = Utils.bound((prog - 0.15) / 0.15, 0, 1)
            speed = self._min_speed * (1 - a) + self._max_speed * a
            vel = Utils.set_length(Utils.sub(self._target.center(), self.center()), speed)
            self._vel = vel

        return self._vel

    def touched_entity(self, entity, world):
        if entity is self._target:
            t_state = entity.get_actorstate()
            if t_state is None:
                return True  # uhh weird

            if t_state.is_invuln():
                return False

            att_state = self.get_source_state().get_attack_state()
            att_state.delayed_attack_landed(self.center(), entity, self.get_attack())
            world.remove(self)

            explosion = AnimationEntity(*self.center(), spriteref.explosions, 45,
                                        spriteref.ENTITY_LAYER, scale=2)
            explosion.set_color(self.get_color(world))
            world.add(explosion)

            return True

    def get_potential_hits(self, world):
        if Utils.dist(self._target.center(), self.center()) <= self.get_radius():
            return [self._target]
        else:
            return []


class AnimationEntity(Entity):

        LOOP_ON_FINISH = 1
        FREEZE_ON_FINISH = 2
        DELETE_ON_FINISH = 3

        def __init__(self, x, y, sprites, duration, layer_id, w=8, h=8, scale=2):
            Entity.__init__(self, x, y, w, h)
            self.duration = duration
            self.tick_count = 0
            self.sprites = sprites
            self.layer_id = layer_id
            self.scale = scale
            self._img = None
            self.xflipped = False
            self.sprite_offset = (0, 0)
            self.centered = [True, True]
            self.on_finish_mode = AnimationEntity.DELETE_ON_FINISH
            self._color = (1, 1, 1)

            self.vel = (0, 0)
            self.fric = 0.90
            self.collides = False

        def set_vel(self, vel, fric=None, collides=None):
            self.vel = vel
            self.fric = self.fric if fric is None else fric
            self.collides = self.collides if collides is None else collides

        def set_finish_behavior(self, mode):
            self.on_finish_mode = mode

        def set_xflipped(self, val):
            self.xflipped = val

        def set_sprite_offset(self, offs):
            self.sprite_offset = offs

        def set_x_centered(self, val):
            self.centered[0] = val

        def set_y_centered(self, val):
            self.centered[1] = val

        def set_color(self, color):
            self._color = color

        def set_sprites(self, new_sprites):
            self.sprites = new_sprites

        def get_current_sprite(self):
            idx = int(self.get_progress() * len(self.sprites))
            return self.sprites[idx]

        def update_attributes(self):
            pass

        def _update_images(self):
            sprite = self.get_current_sprite()

            x = self.x() + self.sprite_offset[0]
            y = self.y() + self.sprite_offset[1]

            if self.centered[0]:
                x -= (sprite.width() * 2 - self.w()) // 2
            if self.centered[1]:
                y -= (sprite.height() * 2 - self.h()) // 2

            if self._img is None:
                self._img = img.ImageBundle(sprite, x, y, layer=self.layer_id, scale=self.scale, depth=0)

            self._img = self._img.update(new_model=sprite, new_x=x, new_y=y,
                                         new_xflip=self.xflipped, new_depth=self.get_depth(),
                                         new_color=self._color)

        def get_progress(self):
            return Utils.bound(self.tick_count / self.duration, 0.0, 0.999)

        def update(self, world, input_state, render_engine):
            # these keep updating when game is paused
            if self.tick_count >= self.duration and self.on_finish_mode == AnimationEntity.DELETE_ON_FINISH:
                world.remove(self)
                return

            if self.tick_count >= self.duration:
                if self.on_finish_mode == AnimationEntity.LOOP_ON_FINISH:
                    self.tick_count = 0
                elif self.on_finish_mode == AnimationEntity.FREEZE_ON_FINISH:
                    self.tick_count = self.duration
                else:
                    raise ValueError("invalid on_finish_mode: {}".format(self.on_finish_mode))

            if self.vel != (0, 0):
                if self.collides:
                    self.move(self.vel[0], self.vel[1], world=world, and_search=True)
                else:
                    self.move(self.vel[0], self.vel[1])

                if self.fric < 1:
                    self.vel = Utils.mult(self.vel, self.fric)
                    if Utils.mag(self.vel) < 0.01:
                        self.vel = (0, 0)

            self.update_attributes()

            self._update_images()
            self.tick_count += 1


class AttackCircleArt(AnimationEntity):

    def __init__(self, cx, cy, radius, duration, color=(1, 0, 1), color_end=(0, 0, 0)):
        sprites = spriteref.get_attack_circles(radius * 2 // 2)
        AnimationEntity.__init__(self, cx - 4, cy - 4, sprites, duration, spriteref.SHADOW_LAYER)
        self._start_color = color
        self._end_color = color_end

    def update_attributes(self):
        prog = self.get_progress()
        if self._end_color is not None:
            color = Utils.linear_interp(self._start_color, self._end_color, prog)
        else:
            color = self._start_color
        self.set_color(color)


class FloatingTextEntity(Entity):

    def __init__(self, text, duration, color, anchor=None, scale=2, start_offs=(0, 0), end_offs=(0, 0), fadeout=True):
        self.text = text
        self.color = color
        self.scale = scale
        self.anchor = anchor
        self.start_offs = start_offs
        self.end_offs = end_offs
        self.fadeout = fadeout

        self.duration = duration
        self.tick_count = 0

        self.text_img = self._build_text_img()
        Entity.__init__(self, 0, 0, *self.text_img.size())

    def get_progress(self):
        return Utils.bound(self.tick_count / self.duration, 0.0, 1.0)

    def _build_text_img(self):
        return TextImage(0, 0, self.text, spriteref.ENTITY_LAYER, color=self.color, scale=self.scale)

    def update_images(self):
        prog = self.get_progress()
        offs_x = self.start_offs[0] * (1 - prog) + self.end_offs[0] * prog
        offs_y = self.start_offs[1] * (1 - prog) + self.end_offs[1] * prog

        x = self.x() + offs_x
        y = self.y() + offs_y

        self.text_img.update(new_x=x, new_y=y)

    def update(self, world, input_state, render_engine):
        # these keep updating even when updates are paused
        if self.tick_count >= self.duration:
            world.remove(self)
        else:
            if self.anchor is not None:
                size = self.text_img.size()
                self.set_x(self.anchor.center()[0] - size[0] // 2)
                self.set_y(self.anchor.center()[1] - size[1] // 2)

            self.update_images()
            self.tick_count += 1

    def all_bundles(self, extras=[]):
        for i in self.text_img.all_bundles():
            yield i
        for e in extras:
            yield e


class Player(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 12)

        self._img = None
        self._shadow_sprite = spriteref.medium_shadow
    
    def set_shadow_sprite(self, sprite):
        self._shadow_sprite = sprite
        
    def get_shadow_sprite(self):
        return self._shadow_sprite
               
    def update_images(self, sprite, facing_right, color=(1.0, 1.0, 1.0)):
        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=2, depth=self.get_depth())

        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (sprite.height() * self._img.scale() - self.h())        
        
        depth = self.get_depth()
        xflip = not facing_right
        self._img = self._img.update(new_model=sprite, new_color=color, new_x=x, new_y=y,
                new_depth=depth, new_xflip=xflip)
        
        super().update_images(0)  # get the shadow

    def cleanup(self, render_engine):
        render_engine.remove(self._img)
        render_engine.remove(self._shadow)
            
    def update(self, world, input_state, render_engine):
        # player updates are handled by PlayerState
        pass
        
    def is_player(self):
        return True

    def get_actorstate(self):
        return gs.get_instance().player_state()

    def valid_to_stand_on(self, world, x, y):
        return (Entity.valid_to_stand_on(self, world, x, y) and
                not world.get_hidden_at(x, y))
 
 
class Enemy(Entity):

    def __init__(self, x, y, state):
        Entity.__init__(self, x, y, 32, 32)
        self.state = state
        self._img = None
        self._healthbar_img = None
        self._shadow_sprite = spriteref.large_shadow
        self._hurtbox_radius = 0
        
    def get_shadow_sprite(self):
        return self._shadow_sprite

    def set_hurtbox(self, radius):
        self._hurtbox_radius = radius

    def hurtbox(self):
        return self._hurtbox_radius
    
    def update_images(self, sprite, facing_left, health_ratio, color=(1, 1, 1), hp_color=(1, 0, 0),
                      shadow_sprite=None, offset=(0, 0)):

        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        if shadow_sprite is not None:
            self._shadow_sprite = shadow_sprite

        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2 + offset[0]
        y = self.y() - (sprite.height() * self._img.scale() - self.h()) + offset[1]
        depth = self.get_depth()
        xflip = not facing_left
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y,
                                     new_depth=depth, new_xflip=xflip, new_color=color)

        if health_ratio < 1.0 and self._healthbar_img is None:
            self._healthbar_img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        if self._healthbar_img is not None:
            n = len(spriteref.progress_spinner)
            hp_sprite = spriteref.progress_spinner[int(min(0.99, health_ratio) * n)]
            hp_x = self.x() - (hp_sprite.width() * self._healthbar_img.scale() - self.w()) // 2
            hp_y = y - hp_sprite.height() - 4 * self._healthbar_img.scale()
            self._healthbar_img = self._healthbar_img.update(new_model=hp_sprite, new_x=hp_x, new_y=hp_y,
                                                             new_depth=depth, new_color=hp_color)

    def all_bundles(self, extras=[]):
        for bun in Entity.all_bundles(self, extras=extras):
            yield bun

        if self._healthbar_img is not None:
            yield self._healthbar_img
        
    def update(self, world, input_state, render_engine):
        self.state.update(self, world, input_state)
        super().update_images(gs.get_instance().anim_tick)  # TODO - shadows are dumb
        
    def is_enemy(self):
        return True

    def get_actorstate(self):
        return self.state
        

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
    
    def _do_open(self, world, level):
        loot = LootFactory.gen_chest_loot(level)

        for item in loot:
            world.add(ItemEntity(item, *self.center()))
            
    def update(self, world, input_state, render_engine):
        
        if not gs.get_instance().world_updates_paused() and not self.is_open():
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
                self._do_open(world, gs.get_instance().get_zone_level())
             
        self.update_images(gs.get_instance().anim_tick)


class PickupEntity(Entity):

    @staticmethod
    def rand_vel(speed=None, direction=None):
        speed = speed if speed is not None else 2 + random.random() * 3
        if direction is None:
            direction = (0, 0)  # becomes random
        direction = Utils.set_length(direction, 1.0)
        return [speed * direction[0], speed * direction[1]]

    def __init__(self, cx, cy, sprites, vel=None):
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self.sprites = sprites
        self.vel = [vel[0], vel[1]] if vel is not None else ItemEntity.rand_vel()
        self.fric = 0.95
        self.bounce_offset = int(random.random() * 100)

        self.pickup_radius = 32
        self.pickup_delay = 45
        self.time_touched = 0

        # for moving away from other stuff
        self.push_radius = 20

    def get_pickup_progress(self):
        return Utils.bound(self.time_touched / self.pickup_delay, 0, 1.0)

    def get_shadow_sprite(self):
        return spriteref.small_shadow

    def get_color(self):
        return (1, 1, 1)

    def get_sprite(self, anim_tick):
        return self.sprites[anim_tick % len(self.sprites)]

    def get_sprite_offset(self):
        return (0, 0)

    def update_images(self, anim_tick):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        bounce = round(2*math.cos((anim_tick + self.bounce_offset) // 2))

        cur_sprite = self.get_sprite(anim_tick)

        offs = self.get_sprite_offset()
        x = self.x() - (cur_sprite.width() * self._img.scale() - self.w()) // 2 + offs[0]
        y = self.y() - (cur_sprite.height() * self._img.scale() - self.h()) + (2 - bounce) + offs[1]
        depth = self.get_depth()
        self._img = self._img.update(new_x=x, new_y=y, new_color=self.get_color(),
                                     new_model=cur_sprite, new_depth=depth)

        super().update_images(anim_tick)

    def _get_pushes(self, world):
        if not self.vel == (0, 0):
            nearby_ents = world.entities_in_circle(self.center(), self.push_radius)
            other_pickups = [i for i in nearby_ents if (i.is_pickup() or i.is_chest()) and i is not self]
            if len(other_pickups) > 0:
                i = other_pickups[int(random.random()*len(other_pickups))]
                direction = Utils.sub(self.center(), i.center())
                return Utils.set_length(direction, 0.75)
            else:
                return (0, 0)

    def update(self, world, input_state, render_engine):
        if not gs.get_instance().world_updates_paused():
            vel_before = Utils.mag(self.vel)

            if vel_before > 0:
                pushes = self._get_pushes(world)
                self.vel = Utils.add(self.vel, pushes)
                self.vel = Utils.set_length(self.vel, vel_before)

                if Utils.mag(self.vel) < 0.05:
                    self.vel = (0, 0)
                else:
                    self.vel = Utils.mult(self.vel, self.fric)

                self.move(*self.vel, world=world, and_search=True)

            # lol, this is weird but w/evs
            pickup_polling = 5
            if random.random() < 1 / pickup_polling:
                p = world.get_player()
                if p is not None and Utils.dist(p.center(), self.center()) <= self.pickup_radius:
                    self.time_touched += pickup_polling
                else:
                    self.time_touched = 0

        self.update_images(gs.get_instance().anim_tick)

        if not gs.get_instance().world_updates_paused() and self.can_pickup():
            self.on_pickup(world)
            world.remove(self)

    def on_pickup(self, world):
        gs.get_instance().player_state().picked_up(self, world)

    def is_pickup(self):
        return True

    def can_pickup(self):
        return self.time_touched >= self.pickup_delay


class ItemEntity(PickupEntity):
    def __init__(self, item, cx, cy, vel=None):
        self.item = item
        sprite = spriteref.get_item_entity_sprite(self.item.cubes)
        PickupEntity.__init__(self, cx, cy, [sprite], vel=vel)

    def get_color(self):
        return self.get_item().color

    def get_item(self):
        return self.item
        
    def is_item(self):
        return True

    def can_pickup(self):
        return False

    def is_interactable(self):
        return True

    def interact_text(self):
        return "pick up"

    def interact(self, world):
        if gs.get_instance().player_state().held_item is not None:
            print("ERROR: cannot pick up item. already holding one.")
            return
        else:
            gs.get_instance().player_state().held_item = self.item
            print("INFO: picked up item " + str(self.item))
            world.remove(self)


class PotionEntity(PickupEntity):
    def __init__(self, cx, cy, vel=None):
        PickupEntity.__init__(self, cx, cy, [spriteref.potion_small], vel=vel)
        self.pickup_delay = 10

    def get_sprite_offset(self):
        return (0, -2)

    def is_potion(self):
        return True


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
        depth = 100  ## umm what
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

    def player_in_range(self, in_range):
        if in_range:
            if self.delay_count == 0:
                sound_effects.play_sound(sound_effects.Effects.DOOR_OPEN)
            self.delay_count += 1
        else:
            self.delay_count = 0

    def _get_sprites(self, is_horz):
        return spriteref.door_h if is_horz else spriteref.door_v

    def update(self, world, input_state, render_engine):
        if self._is_horz is None:
            self._is_horz = self._calc_is_horz(world)

        if not gs.get_instance().world_updates_paused():

            if self.opening_count >= self.opening_duration:
                # XXX kinda jank, we set the geo value to FLOOR when the door is set to open
                # but we don't update the surrounding tile sprites until the opening animation
                # is finished. This allows the player to pass through while the door is partially
                # open, while also keeping the wall sprites correct.
                #
                # TODO this <will> cause bugs in the future
                grid_xy = world.to_grid_coords(*self.center())
                world.update_geo_bundle(*grid_xy, and_neighbors=True)
                world.door_opened(*grid_xy)
                world.remove(self)
                gs.get_instance().event_queue().add(events.DoorOpenEvent(self.get_uid(), *grid_xy))
            elif self.opening_count > 0:
                self.opening_count += 1
            else:
                self._update_internal(world, input_state, render_engine)

        self.sprites = self._get_sprites(self._is_horz)
        self.update_images()

    def _update_internal(self, world, input_state, render_engine):
        if self.delay_count >= self.delay_duration:
            # door will open now
            self.delay_count = 0
            self.opening_count = 1
            grid_xy = world.to_grid_coords(*self.center())
            world.set_geo(*grid_xy, World.FLOOR)
        else:
            p = world.get_player()
            p_in_range = (p is not None and Utils.dist(p.center(), self.center()) <= self.open_radius)
            self.player_in_range(p_in_range)

    def is_door(self):
        return True

    def is_locked(self):
        return False

    def do_open(self):
        self.delay_count = self.delay_duration


class LockedDoorEntity(DoorEntity):

    def __init__(self, grid_x, grid_y, interact_text_list=["it's locked."], hover_text="inspect"):
        self._interact_text_list = interact_text_list
        self._hover_text = hover_text
        DoorEntity.__init__(self, grid_x, grid_y)
        self._is_locked = True

    def player_in_range(self, in_range):
        # do nothing, we're locked
        pass

    def _get_sprites(self, is_horz):
        return spriteref.door_h_locked if is_horz else spriteref.door_v_locked

    def is_interactable(self):
        return (self.is_locked() and self._interact_text_list is not None)

    def interact_radius(self):
        return self.open_radius

    def interact(self, world):
        if self._interact_text_list is not None:
            dialogs = [PlayerDialog(text) for text in self._interact_text_list]
            gs.get_instance().dialog_manager().set_dialog(Dialog.link_em_up(dialogs))

    def interact_text(self):
        return self._hover_text

    def do_open(self):
        print("INFO: unlocking door {}".format(self.get_uid()))
        self._is_locked = False
        DoorEntity.do_open(self)

    def is_locked(self):
        return self._is_locked


class SensorDoorEntity(DoorEntity):
    def __init__(self, grid_x, grid_y, sensor_radius=64*6, interact_dialog=None):
        DoorEntity.__init__(self, grid_x, grid_y)
        self.delay_duration = 90  # will unlock when no enemies are in range for this many frames
        self.sensor_radius = sensor_radius
        self.interact_dialog = interact_dialog

    def _get_sprites(self, is_horz):
        if self.opening_count > 0:
            use_white = False
        elif self.delay_count == 0:
            use_white = True
        else:
            # flash colors while detecting that enemies are missing
            if (self.delay_count // 8) % 2 == 0:
                use_white = True
            else:
                use_white = False

        if use_white:
            return spriteref.door_h_sensor if is_horz else spriteref.door_v_sensor
        else:
            return spriteref.door_h if is_horz else spriteref.door_v

    def is_interactable(self):
        return self.delay_count < self.delay_duration

    def interact(self, world):
        print("interacted with sensor door")
        if self.is_interactable():
            if self.interact_dialog is None:
                gs.get_instance().dialog_manager().set_dialog(PlayerDialog("this door won't open while enemies are nearby."))
            else:
                gs.get_instance().dialog_manager().set_dialog(self.interact_dialog)

    def _update_internal(self, world, input_state, render_engine):
        p = world.get_player()
        p_in_range = (p is not None and Utils.dist(p.center(), self.center()) <= self.open_radius)

        if not p_in_range:
            self.delay_count = 0
            return

        e_in_range = world.entities_in_circle(self.center(), self.sensor_radius, onscreen=True,
                                              cond=lambda e: e.is_enemy() and not world.get_hidden_at(*e.center()))

        if len(e_in_range) > 0:
            self.delay_count = 0
        else:
            self.delay_count += 1

            if self.delay_count >= self.delay_duration:
                # door will open now
                self.delay_count = 0
                self.opening_count = 1
                grid_xy = world.to_grid_coords(*self.center())
                world.set_geo(*grid_xy, World.FLOOR)


class SaveStationEntity(Entity):

    def __init__(self, grid_x, grid_y):
        Entity.__init__(self, grid_x * 64 + 16, grid_y * 64, 32, 8)

    def get_shadow_sprite(self):
        return spriteref.chest_shadow

    def update_images(self, anim_tick):
        Entity.update_images(self, anim_tick)  # update shadow

        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=2)

        sprite = spriteref.save_stations[(anim_tick // 3) % len(spriteref.save_stations)]

        x = self.x()
        y = self.y() - sprite.height() * 2 + 8
        self._img = self._img.update(new_x=x, new_y=y, new_model=sprite, new_depth=self.get_depth())

        if self._shadow is not None:
            self._shadow = self._shadow.update(new_x=x)

    def update(self, world, input_state, render_engine):
        self.update_images(gs.get_instance().anim_tick)

    def is_save_station(self):
        return True

    def is_interactable(self):
        return True

    def interact_text(self):
        return "save station"

    def interact(self, world):
        question = NpcDialog("save game?\n\n" +
                             "{yes} {no}", spriteref.save_station_faces)

        def _do_save(event, w):
            if event.get_option_idx() == 0:
                result, pw = gs.get_instance().save_game_to_disk()
                if result:
                    dialog = NpcDialog("game saved with password: {}".format(pw), spriteref.save_station_faces)
                    gs.get_instance().dialog_manager().set_dialog(dialog)
                else:
                    gs.get_instance().dialog_manager().set_dialog(Dialog("failed to save.", spriteref.save_station_faces))

            gs.get_instance().player_state().do_full_heal()
            gs.get_instance().player_state().remove_all_statuses()

        e_listener = question.build_listener(_do_save, single_use=True)

        gs.get_instance().add_trigger(e_listener)
        gs.get_instance().dialog_manager().set_dialog(question)


class ExitEntity(Entity):

    def __init__(self, grid_x, grid_y, next_zone_id):
        Entity.__init__(self, grid_x * 64, grid_y * 64, 64, 2)

        self.next_zone_id = next_zone_id
        self.count = 0
        self.open_duration = 60
        self.radius = 48

        self._was_interacted_with = False

        try:
            # TODO - zone info should be more accessible...
            import src.worldgen.zones as zones
            self.hover_text = zones.get_zone_name(next_zone_id)
        except ValueError:
            self.hover_text = "Unknown"

    def get_sprite(self, anim_tick):
        if self.count == 0:
            sprite = self.idle_sprites()[(anim_tick // 2) % 2]
        else:
            open_spr = self.opening_sprites()
            idx = int(self.get_progress() * len(open_spr))
            sprite = open_spr[idx]
        return sprite

    def get_zone(self):
        return self.next_zone_id

    def idle_sprites(self):
        return spriteref.normal_door_idle

    def opening_sprites(self):
        return spriteref.normal_door_opening

    def sprite_offset(self, sprite, scale):
        return (0, -sprite.height() * scale)

    def update_images(self, anim_tick):
        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=4)

        sprite = self.get_sprite(anim_tick)

        offs = self.sprite_offset(sprite, 4)

        x = self.x() + offs[0]
        y = self.y() + offs[1]
        self._img = self._img.update(new_x=x, new_y=y, new_model=sprite, new_depth=self.get_depth())

    def get_progress(self):
        return Utils.bound(self.count / self.open_duration, 0.0, 0.999)

    def is_exit(self):
        return True

    def is_open(self):
        return self.count >= self.open_duration

    def set_open(self, val):
        if val:
            self.count = self.open_duration
        else:
            self.count = 0

    def update(self, world, input_state, render_engine):

        if not gs.get_instance().world_updates_paused():
            if self.count < self.open_duration:
                player = world.get_player()
                if player is not None:
                    p_center = player.center()
                    if Utils.dist(p_center, self.center()) <= self.radius:
                        self.count += 1
                    else:
                        self.count -= 2
                    self.count = Utils.bound(self.count, 0, self.open_duration)
            elif self._was_interacted_with:
                    gs.get_instance().event_queue().add(self.make_new_zone_event())

        self.update_images(gs.get_instance().anim_tick)

    def make_new_zone_event(self):
        # TODO - maybe better if exits already know their current zones
        return events.NewZoneEvent(self.next_zone_id, gs.get_instance().get_zone_id())

    def is_interactable(self):
        return self.is_open()

    def interact(self, world):
        self._was_interacted_with = True

    def interact_text(self):
        return self.hover_text


class ReturnExitEntity(ExitEntity):

    def __init__(self, grid_x, grid_y, next_zone_id):
        ExitEntity.__init__(self, grid_x, grid_y, next_zone_id)
        self.set_y(self.y() + 62)
        self.open_duration = 15

    def make_new_zone_event(self):
        return events.NewZoneEvent(self.next_zone_id, gs.get_instance().get_zone_id(),
                                   transfer_type=events.NewZoneEvent.RETURNING)

    def get_sprite(self, anim_tick):
        sprites = spriteref.return_door_smoke
        return sprites[anim_tick % len(sprites)]

    def sprite_offset(self, sprite, scale):
        return (0, -62)


class BossExitEntity(ExitEntity):

    def idle_sprites(self):
        return spriteref.boss_door_idle

    def opening_sprites(self):
        return spriteref.boss_door_opening


class DecorationEntity(Entity):

    def __init__(self, sprite, x_center, y_bottom, scale=2, draw_offset=(0, 0), hover_text="inspect",
                 interact_dialog=None):
        """
        sprite: ImageModel or a list of ImageModels
        interact_dialog: Dialog
        """
        Entity.__init__(self, x_center, y_bottom, 1, 0)

        self._interact_dialog = interact_dialog
        self._hover_text = hover_text
        self._draw_offset = draw_offset
        self._sprites = Utils.listify(sprite)
        self._scale = scale

    def update(self, world, input_state, render_engine):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=self._scale)

        sprite = self._sprites[gs.get_instance().anim_tick // 2 % len(self._sprites)]
        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2 + self._draw_offset[0]
        y = self.y() - (sprite.height() * self._img.scale() - self.h()) + self._draw_offset[1]
        depth = self.get_depth()

        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, new_depth=depth)

    def all_bundles(self, extras=[]):
        for bun in Entity.all_bundles(self, extras=extras):
            yield bun
        if self._img is not None:
            yield self._img

    @staticmethod
    def wall_decoration(sprites, grid_x, grid_y, scale=2, interact_dialog=None, hover_text="inspect"):
        """
        sprite: ImageModel or a list of ImageModels
        interact_dialog: Dialog
        """
        sprites = Utils.listify(sprites)
        h = sprites[0].height() * scale
        CELLSIZE = 64  # this better never change~
        offset = (0, 8 * scale)
        x_center = (grid_x + 0.5) * CELLSIZE
        y_bottom = (grid_y) * CELLSIZE
        return DecorationEntity(sprites, x_center, y_bottom, scale=scale, draw_offset=offset,
                                interact_dialog=interact_dialog, hover_text=hover_text)

    @staticmethod
    def sign_decoration(grid_x, grid_y, dialog_text, hover_text):
        sprite = spriteref.standalone_sign_decoration
        CELLSIZE = 64  # this better never change~
        scale = 2
        x_center = (grid_x + 0.5) * CELLSIZE
        y_bottom = (grid_y + 0.5) * CELLSIZE
        offset = (0, -(sprite.height() - 1) * scale)

        return DecorationEntity(sprite, x_center, y_bottom, scale=scale, draw_offset=offset,
                                interact_dialog=PlayerDialog(dialog_text), hover_text=hover_text)

    def is_interactable(self):
        return self._interact_dialog is not None

    def interact(self, world):
        if self._interact_dialog is not None:
            gs.get_instance().dialog_manager().set_dialog(self._interact_dialog)

    def interact_text(self):
        return self._hover_text


class TreeEntity(Entity):

    def __init__(self):
        Entity.__init__(self, 0, 0, 8, 8)
        self._tree_id = int(999 * random.random())
        self.lean_ratio = random.random()
        self.wind_offset = int(random.random() * 10)

    def get_shadow_sprite(self):
        return spriteref.medium_shadow

    def update_images(self, anim_tick, lean_ratio):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        sprite = spriteref.Trees.get_tree(self._tree_id, lean_ratio)
        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (sprite.height() * self._img.scale() - self.h())
        depth = self.get_depth()

        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, new_depth=depth)

        Entity.update_images(self, anim_tick)

    def update(self, world, input_state, render_engine):
        num = gs.get_instance().anim_tick + self.wind_offset
        cool_lean = ((num % 480) / 480 + (num % 200) / 200) / 2
        self.lean_ratio = Utils.bound(cool_lean, 0, 0.999)
        self.update_images(gs.get_instance().anim_tick, self.lean_ratio)


class NpcEntity(Entity):

    def __init__(self, npc_id):
        Entity.__init__(self, 0, 0, 24, 12)
        self.npc_id = npc_id
        self._shadow_sprite = None
        self.facing_player = True

    def get_shadow_sprite(self):
        return self._shadow_sprite

    def update_images(self, sprite, facing_left, color=(1, 1, 1), shadow_sprite=None):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        x = self.x() - (sprite.width() * self._img.scale() - self.w()) // 2
        y = self.y() - (sprite.height() * self._img.scale() - self.h())
        depth = self.get_depth()
        xflip = not facing_left
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y,
                                     new_depth=depth, new_xflip=xflip, new_color=color)

        self._shadow_sprite = shadow_sprite
        Entity.update_images(self, 0)  # just updating shadow

    def update(self, world, input_state, render_engine):
        gs.get_instance().npc_state().update(self, world, input_state, render_engine)

    def get_id(self):
        return self.npc_id

    def is_npc(self):
        return True

    def is_interactable(self):
        return True

    def interact_text(self):
        return "talk"

    def interact(self, world):
        gs.get_instance().event_queue().add(events.NpcInteractEvent(self.get_id()))

    def __repr__(self):
        return "NpcEntity({})".format(self.get_id())


class TriggerBox(Entity):
    """performs an action when the player enters or leaves the box"""
    def __init__(self, grid_pos, grid_size=(1, 1), just_once=False, delay=0, ignore_updates_paused=False, box_id=None):
        cell_size = 64  # ehhh
        Entity.__init__(self, grid_pos[0] * cell_size, grid_pos[1] * cell_size,
                        cell_size * grid_size[0], cell_size * grid_size[1])
        self.player_inside = False
        self.player_in_range_count = 0
        self.delay = delay
        self.just_once = just_once
        self.no_more_firings = False
        self.ignore_updates_paused = ignore_updates_paused
        self.box_id = box_id

    def update(self, world, input_state, render_engine):
        if gs.get_instance().world_updates_paused() and not self.ignore_updates_paused:
            return

        p = world.get_player()
        inside = p is not None and Utils.rect_contains(self.rect, p.center())
        if self.player_inside != inside:
            if inside:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_enter_event(self.box_id))
                self.player_entered(p, world, input_state, render_engine)
            else:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_exit_event(self.box_id))
                self.player_left(p, world, input_state, render_engine)
            self.player_inside = inside
            self.player_in_range_count = 0

        if self.player_inside:
            if not self.no_more_firings and self.player_in_range_count == self.delay:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_trigger_event(self.box_id))
                self.fire_action(p, world, input_state, render_engine)
                if self.just_once:
                    self.no_more_firings = True

            self.player_in_range_count += 1

    def player_entered(self, player, world, input_state, render_action):
        pass

    def fire_action(self, player, world, input_state, render_action):
        pass

    def player_left(self, player, world, input_state, render_action):
        pass


class DialogTriggerBox(TriggerBox):

    def __init__(self, dialog, grid_pos, grid_size=(1, 1), just_once=False, delay=0, ignore_updates_paused=False, box_id=None):
        TriggerBox.__init__(self, grid_pos, grid_size=grid_size, just_once=just_once, delay=delay,
                            ignore_updates_paused=ignore_updates_paused, box_id=box_id)
        self.dialog = dialog

    def fire_action(self, player, world, input_state, render_action):
        gs.get_instance().dialog_manager().set_dialog(self.dialog)


class MessageTriggerBox(TriggerBox):

    def __init__(self, text, grid_pos, grid_size=(1, 1), just_once=False, delay=0, ignore_updates_paused=False, box_id=None):
        TriggerBox.__init__(self, grid_pos, grid_size=grid_size, just_once=just_once, delay=delay,
                            ignore_updates_paused=ignore_updates_paused, box_id=box_id)
        self.text = text
        self._hover_text = None

    def fire_action(self, player, world, input_state, render_action):
        self._hover_text = HoverTextEntity(self.text, player, offset=(0, -90), bounds=self.rect)
        world.add(self._hover_text)

    def player_left(self, player, world, input_state, render_action):
        self._hover_text = None


class HoverTextEntity(Entity):

    def __init__(self, text, target_entity, offset=(0, 0), bounds=None):
        Entity.__init__(self, 0, 0, 8, 8)
        self.text = text
        self.target_entity = target_entity
        self.offset = offset
        self.anchor_point = (0.5, 1.0)
        self.inset = 5
        self.bounds = bounds

        self._text_img = None
        self._border_imgs = [None] * 9  # [TL, T, TR, L, C, R, BL, None, BR]
        self._bottom_imgs = [None, None, None]  # [B1, B_Arrow, B2]
        self._y_bob_range = 8
        self.bob_height = 0
        self._update_position()
        self._dirty = True

    def should_remove(self):
        if self.bounds is not None:
            return not Utils.rect_contains(self.bounds, self.center())

        return False

    def _update_position(self):
        """sets self.center to target_entity.center() + offset
            returns: True if position changed, else False
        """
        changed = False

        if self.target_entity is not None:
            t_center = self.target_entity.center()
            x_pos = t_center[0]
            y_pos = t_center[1]
            if self.center() != (x_pos, y_pos):
                changed = True
                self.set_center(x_pos, y_pos)

        if gs is not None:
            new_bob_height = round(self._y_bob_range + (0.5 * self._y_bob_range * math.cos(6.28 * gs.get_instance().anim_tick / 15)))
            if new_bob_height != self.bob_height:
                changed = True
                self.bob_height = new_bob_height

        return changed

    def update(self, world, input_state, render_engine):
        if self._dirty:
            if self._text_img is not None:
                for bun in self._text_img.all_bundles():
                    render_engine.remove(bun)
                self._text_img = None

        sc = 2

        if self._text_img is None:
            self._text_img = TextImage(0, 0, self.text, spriteref.ENTITY_LAYER, scale=sc)

        for i in range(0, len(self._border_imgs)):
            if i == 7:
                continue  # bottom border is more complicated
            if self._border_imgs[i] is None:
                self._border_imgs[i] = img.ImageBundle(spriteref.UI.hover_text_edges[i], 0, 0, scale=sc, layer=spriteref.ENTITY_LAYER)

        if self._bottom_imgs[0] is None:
            self._bottom_imgs[0] = img.ImageBundle(spriteref.UI.hover_text_edges[7], 0, 0, scale=sc, layer=spriteref.ENTITY_LAYER)
        if self._bottom_imgs[1] is None:
            self._bottom_imgs[1] = img.ImageBundle(spriteref.UI.hover_text_bottom_arrow, 0, 0, scale=sc, layer=spriteref.ENTITY_LAYER)
        if self._bottom_imgs[2] is None:
            self._bottom_imgs[2] = img.ImageBundle(spriteref.UI.hover_text_edges[7], 0, 0, scale=sc, layer=spriteref.ENTITY_LAYER)

        moved = self._update_position()

        if self.should_remove():
            world.remove(self)
            return

        if self._dirty or moved:

            if self.target_entity is not None:
                depth = self.target_entity.get_depth()
            else:
                depth = self.get_depth()

            text_size = self._text_img.size()
            text_x = self.center()[0] - text_size[0] * self.anchor_point[0] + self.offset[0]
            text_y = self.center()[1] - text_size[1] * self.anchor_point[1] + self.offset[1] + self.bob_height
            self._text_img = self._text_img.update(new_x=text_x, new_y=text_y, new_depth=depth)
            text_w, text_h = self._text_img.size()

            text_x -= self.inset
            text_y -= self.inset
            text_w += self.inset * 2
            text_h += self.inset * 2

            border_size = spriteref.UI.hover_text_edges[4].size()[0] * sc

            tl_pos = (text_x - border_size, text_y - border_size)

            if self._border_imgs[0] is not None:  # TL
                self._border_imgs[0] = self._border_imgs[0].update(new_x=tl_pos[0], new_y=tl_pos[1], new_depth=depth)

            if self._border_imgs[1] is not None:  # T
                self._border_imgs[1] = self._border_imgs[1].update(new_x=text_x, new_y=tl_pos[1],
                                                                   new_ratio=(text_w / border_size, 1),
                                                                   new_depth=depth)
            if self._border_imgs[2] is not None:  # TR,
                self._border_imgs[2] = self._border_imgs[2].update(new_x=text_x + text_w, new_y=tl_pos[1],
                                                                   new_depth=depth)

            if self._border_imgs[3] is not None:  # L,
                self._border_imgs[3] = self._border_imgs[3].update(new_x=tl_pos[0], new_y=text_y,
                                                                   new_ratio=(1, text_h / border_size),
                                                                   new_depth=depth)
            if self._border_imgs[4] is not None:  # C,
                ratio = (text_w / border_size, text_h / border_size)
                self._border_imgs[4] = self._border_imgs[4].update(new_x=text_x, new_y=text_y,
                                                                   new_ratio=ratio,
                                                                   new_depth=depth)
            if self._border_imgs[5] is not None:  # R,
                self._border_imgs[5] = self._border_imgs[5].update(new_x=text_x + text_w, new_y=text_y,
                                                                   new_ratio=(1, text_h / border_size),
                                                                   new_depth=depth)
            if self._border_imgs[6] is not None:  # BL
                self._border_imgs[6] = self._border_imgs[6].update(new_x=tl_pos[0], new_y=text_y + text_h,
                                                                   new_depth=depth)
            if self._border_imgs[8] is not None:  # BR
                self._border_imgs[8] = self._border_imgs[8].update(new_x=text_x + text_w, new_y=text_y + text_h,
                                                                   new_depth=depth)

            if self._bottom_imgs[1] is not None:  # Bottom Middle
                bm_w = self._bottom_imgs[1].width()
                bm_x = text_x + text_w / 2 - bm_w / 2
                self._bottom_imgs[1] = self._bottom_imgs[1].update(new_x=bm_x, new_y=text_y + text_h,
                                                                   new_depth=depth)
                if self._bottom_imgs[0] is not None:  # Bottom Left
                    ratio = ((bm_x - text_x) / border_size, 1)
                    self._bottom_imgs[0] = self._bottom_imgs[0].update(new_x=text_x, new_y=text_y + text_h,
                                                                       new_ratio=ratio, new_depth=depth)
                if self._bottom_imgs[2] is not None:  # Bottom Right
                    ratio = ((bm_x - text_x) / border_size, 1)
                    self._bottom_imgs[2] = self._bottom_imgs[2].update(new_x=bm_x + bm_w, new_y=text_y + text_h,
                                                                       new_ratio=ratio, new_depth=depth)

        self._dirty = False

    def set_target_entity(self, entity, offset=(0, 0)):
        self.target_entity = entity
        self.offset = offset
        self._dirty = True

    def set_text(self, text):
        if text != self.text:
            self._dirty = True
        self.text = text

    def all_bundles(self, extras=[]):
        for bun in Entity.all_bundles(self, extras=extras):
            yield bun

        for bun in self._border_imgs:
            if bun is not None:
                yield bun

        for bun in self._bottom_imgs:
            if bun is not None:
                yield bun

        if self._text_img is not None:
            for bun in self._text_img.all_bundles():
                yield bun

