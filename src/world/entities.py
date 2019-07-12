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
import src.game.soundref as soundref
from src.renderengine.engine import RenderEngine
import src.utils.colors as colors
import src.game.stats as stats

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

    def __str__(self):
        typename = type(self).__name__
        c_x = self.center()[0] // 64
        c_y = self.center()[1] // 64
        return "{}{}({}, {})".format(typename, self.get_uid(), c_x, c_y)
        
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

    def is_visible_in_world(self, world):
        grid_xy = world.to_grid_coords(*self.center())
        if world.get_hidden(grid_xy[0], grid_xy[1]):
            return False
        elif self.visible_in_darkness():
            return True
        else:
            return world.get_visible(grid_xy[0], grid_xy[1])

    def visible_in_darkness(self):
        return True

    def get_light_level(self):
        return 0
        
    def center(self):
        return self.rect.center

    def get_render_center(self):
        return self.center()

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

    def move_to(self, cx, cy, world=None, and_search=False):
        cur_center = self.center()
        dx = cx - cur_center[0]
        dy = cy - cur_center[1]
        self.move(dx, dy, world=world, and_search=and_search)

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
        
    def update(self, world):
        pass

    def alive(self):
        """whether the entity is in a World"""
        return self._alive
        
    def cleanup(self):
        render_eng = RenderEngine.get_instance()
        for bundle in self.all_bundles():
            render_eng.remove(bundle)

    def update_images(self):
        sh_model = self.get_shadow_sprite()
        if sh_model is not None:
            if self._shadow is None:
                self._shadow = img.ImageBundle.new_bundle(spriteref.SHADOW_LAYER)
            sh_scale = 2
            sh_x = self.get_render_center()[0] - (sh_model.width() * sh_scale) // 2 + self.get_shadow_offset()[0]
            sh_y = self.get_render_center()[1] - (sh_model.height() * sh_scale) // 2 + self.get_shadow_offset()[1]
            self._shadow = self._shadow.update(new_model=sh_model, new_x=sh_x, new_y=sh_y, new_scale=sh_scale)
        else:
            if self._shadow is not None:
                RenderEngine.get_instance().remove(self._shadow)
                self._shadow = None

    def get_shadow_sprite(self):
        return None

    def get_shadow_offset(self):
        return (0, 0)

    def get_depth(self):
        return -self.get_render_center()[1]
    
    def is_player(self):
        return False

    def is_actor(self):
        return False
        
    def is_item(self):
        return False
        
    def is_chest(self):
        return False
        
    def is_enemy(self):
        return False

    def is_pickup(self):
        return False

    def is_save_station(self):
        return False

    def is_npc(self):
        return False

    def is_exit(self):
        return False

    def is_door(self):
        return False

    def is_interactable(self, world):
        return False

    def interact(self, world):
        pass

    def is_solid(self, world):
        """returns: whether this entity prevents the movement of Actors."""
        return self.is_npc() or self.is_actor() or self.is_interactable(world)

    def is_pushable(self):
        return isinstance(self, Pushable)

    def can_damage(self, other):
        return ((self.is_player() and other.is_enemy()) or
                (self.is_enemy() and other.is_player()))

    def __eq__(self, other):
        return other is not None and self._uid == other._uid

    def __hash__(self):
        return self._uid

    def get_uid(self):
        return self._uid

    def all_bundles(self):
        if self._shadow is not None:
            yield self._shadow
        if self._img is not None:
            yield self._img


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


class AnimationEntity(Entity):

        LOOP_ON_FINISH = 1
        FREEZE_ON_FINISH = 2
        DELETE_ON_FINISH = 3

        def __init__(self, cx, cy, sprites, duration, layer_id, scale=2):
            Entity.__init__(self, cx - 2, cy - 2, 4, 4)
            self.duration = duration
            self.tick_count = 0
            self.sprites = sprites
            self.layer_id = layer_id
            self.scale = scale
            self._img = None
            self.xflipped = False
            self.sprite_offset = (0, 0)
            self.on_finish_mode = AnimationEntity.DELETE_ON_FINISH
            self._color = (1, 1, 1)
            self.shadow_sprite = None
            self.rotation = 0

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

        def set_color(self, color):
            self._color = color

        def set_shadow_sprite(self, sprite):
            self.shadow_sprite = sprite

        def set_rotation(self, val):
            self.rotation = val

        def get_shadow_sprite(self):
            return self.shadow_sprite

        def set_sprites(self, new_sprites):
            self.sprites = new_sprites

        def get_current_sprite(self):
            idx = int(self.get_progress() * len(self.sprites))
            return self.sprites[idx]

        def visible_in_darkness(self):
            return False

        def update_attributes(self):
            pass

        def update_images(self):
            sprite = self.get_current_sprite()

            if sprite is None:
                if self._img is not None:
                    RenderEngine.get_instance().remove(self._img)
                    self._img = None
                return
            else:
                cx = self.get_render_center()[0]
                cy = self.get_render_center()[1]

                spr_w = sprite.width() * self.scale if self.rotation % 2 == 0 else sprite.height() * self.scale
                spr_h = sprite.height() * self.scale if self.rotation % 2 == 0 else sprite.width() * self.scale

                x = cx - spr_w // 2 + self.sprite_offset[0]
                y = cy - spr_h + self.sprite_offset[1]

                if self._img is None:
                    self._img = img.ImageBundle.new_bundle(self.layer_id)

                self._img = self._img.update(new_model=sprite, new_x=x, new_y=y,
                                             new_xflip=self.xflipped, new_depth=self.get_depth(),
                                             new_color=self._color, new_scale=self.scale, new_rotation=self.rotation)

                super().update_images()  # updating shadow

        def get_progress(self):
            return Utils.bound(self.tick_count / self.duration, 0.0, 0.999)

        def update(self, world):
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

            self.update_images()
            self.tick_count += 1


class AttackCircleArt(AnimationEntity):

    def __init__(self, cx, cy, radius, duration, color=(1, 0, 1), color_end=(0, 0, 0)):
        sprites = spriteref.get_attack_circles(radius * 2 // 2)
        AnimationEntity.__init__(self, cx, cy, sprites, duration, spriteref.SHADOW_LAYER)
        self._start_color = color
        self._end_color = color_end

    def update_attributes(self):
        prog = self.get_progress()
        if self._end_color is not None:
            color = Utils.linear_interp(self._start_color, self._end_color, prog)
        else:
            color = self._start_color
        self.set_color(color)


class PlayerCorpseAnimation(AnimationEntity):

    def __init__(self, cx, cy, duration):
        AnimationEntity.__init__(self, cx, cy, spriteref.player_death_seq, duration, spriteref.ENTITY_LAYER)

    def is_interactable(self, world):
        # XXX just to make it so enemies can't step on you
        return True

    def visible_in_darkness(self):
        return False


class LightEmitterAnimation(AnimationEntity):

    def __init__(self, cx, cy, duration, start_light_level, end_light_level):
        AnimationEntity.__init__(self, cx, cy, [], duration, spriteref.ENTITY_LAYER)
        self.start_light = start_light_level
        self.end_light = end_light_level

    def get_current_sprite(self):
        return None

    def get_light_level(self):
        l_range = self.end_light - self.start_light
        return int(self.start_light + self.get_progress() * l_range)


class FloatingTextEntity(Entity):

    def __init__(self, cx, cy, text, duration, color, anchor=None, scale=2, start_offs=(0, 0), end_offs=(0, 0), fadeout=True):
        Entity.__init__(self, cx-4, cy-4, 8, 8)
        self.text = text
        self.color = color
        self.scale = scale
        self.anchor = anchor
        self.start_offs = start_offs
        self.end_offs = end_offs
        self.fadeout = fadeout

        self.duration = duration
        self.tick_count = 0
        self._text_img = None

    def get_progress(self):
        return Utils.bound(self.tick_count / self.duration, 0.0, 1.0)

    def _build_text_img(self):
        return TextImage(0, 0, self.text, spriteref.ENTITY_LAYER, color=self.color, scale=self.scale)

    def update_images(self):
        if self._text_img is None:
            self._text_img = self._build_text_img()

        prog = self.get_progress()
        offs_x = self.start_offs[0] * (1 - prog) + self.end_offs[0] * prog
        offs_y = self.start_offs[1] * (1 - prog) + self.end_offs[1] * prog

        x = self.center()[0] + offs_x - self._text_img.w() // 2
        y = self.center()[1] + offs_y - self._text_img.h()

        self._text_img = self._text_img.update(new_x=x, new_y=y, new_depth=self.get_depth())

    def update(self, world):
        # these keep updating even when updates are paused
        if self.tick_count >= self.duration:
            world.remove(self)
        else:
            if self.anchor is not None:
                size = self._text_img.size()
                self.set_x(self.anchor.center()[0] - size[0] // 2)
                self.set_y(self.anchor.center()[1] - size[1] // 2)

            self.update_images()
            self.tick_count += 1

    def all_bundles(self):
        if self._text_img is not None:
            for bun in self._text_img.all_bundles():
                yield bun


class ActorEntity(Entity):

    def __init__(self, idle_sprites, sprite_offset=(0, 0), shadow_offset=(0, 0)):
        Entity.__init__(self, 0, 0, 24, 24)

        self.executing_action = None
        self.executing_action_duration = 1
        self.executing_action_ticks = 0

        self.idle_sprites = Utils.listify(idle_sprites)
        self._facing_right = random.random() > 0.5
        self.base_color = (1, 1, 1)

        self._img = None
        self._shadow_sprite = spriteref.medium_shadow

        # used to apply a 'bouncy' effect to the actor
        self._perturb_points = []

        # used to apply a color for a short duration
        self._perturb_color = [0, 0, 0]
        self._perturb_color_duration = 1
        self._perturb_color_ticks = 1

        # used to jump a little bit (z-axis)
        self._z_perturb_points = []

        # used to compensate for off-center sprites
        self._sprite_offset = sprite_offset

        # used to adjust shadow's draw position
        self._shadow_offset = shadow_offset

        # used to (temporarily) visually move the actor without actually moving them
        self._draw_offset = (0, 0)

        self._was_moving = 60  # how long it's been since the actor was moving

    def get_shadow_sprite(self):
        return self._shadow_sprite

    def get_shadow_offset(self):
        return self._shadow_offset

    def get_damage_sound(self):
        return soundref.rand_damage_hit_small()

    def get_death_sound(self):
        return soundref.rand_explosion_short()

    def get_light_level(self):
        return self.get_actor_state().light_level()

    def set_vel(self, vel):
        """this doesn't move the actor or anything. just sets self._last_vel to whatever"""
        self._last_vel = vel

    def is_moving(self):
        return Utils.mag(self.get_vel()) >= 0.05

    def was_moving_recently(self, this_recently=5):
        return self._was_moving <= this_recently

    def visible_in_darkness(self):
        return False

    def handle_death(self, world):
        pos = self.get_render_center(ignore_perturbs=True)
        for item in self.get_actor_state().inventory().all_items():
            world.add_item_as_entity(item, pos, direction=None)

        sound_effects.play_sound(self.get_death_sound())
        world.show_explosion(pos[0], pos[1], 40, color=(0, 0, 0), offs=(0, 0), scale=4)
        world.remove(self)

    def animate_damage_taken(self, world):
        self.perturb_color(colors.R_TEXT_COLOR, 25)
        self.perturb(20, 18)
        sound_effects.play_sound(self.get_damage_sound())

    def cleanup(self):
        super().cleanup()
        for bun in self.all_bundles():
            RenderEngine.get_instance().remove(bun)

    def get_actor_state(self):
        pass

    def get_controller(self):
        pass

    def request_next_action(self, world):
        return self.get_controller().get_next_action(self, world)

    def is_actor(self):
        return True

    def set_and_start_action(self, action, duration, world):
        if self.executing_action is not None and action is not None:
            msg = "error setting action {}, actor already has action: {}".format(action, self.executing_action)
            raise ValueError(msg)

        self.executing_action = action
        self.executing_action_duration = duration
        self.executing_action_ticks = 0

        if self.executing_action is not None:
            if not self.executing_action.is_possible(world):
                raise ValueError("set an impossible action {} on actor {}".format(action, self))

            self.executing_action.pre_start(world)
            self.executing_action.start(world)

    def set_visually_held_item_override(self, val):
        pass

    def is_performing_action(self):
        return self.executing_action is not None

    def update_perturbations(self):
        if len(self._perturb_points) > 0:
            self._perturb_points.pop()

        if self._perturb_color_ticks < self._perturb_color_duration:
            self._perturb_color_ticks += 1

        if len(self._z_perturb_points) > 0:
            self._z_perturb_points.pop()

    def get_perturbed_xy(self):
        if len(self._perturb_points) == 0:
            return (0, 0)
        else:
            x, y = self._perturb_points[-1]
            return (round(x), round(y))

    def get_perturbed_z(self):
        if len(self._z_perturb_points) == 0:
            return 0
        else:
            return round(self._z_perturb_points[-1])

    def get_draw_offset(self):
        return self._draw_offset

    def set_draw_offset(self, dx, dy):
        self._draw_offset = (dx, dy)

    def get_render_center(self, ignore_perturbs=False):
        """returns: the center point (x, y) of where the actor should be drawn."""

        x = self.center()[0] + self.get_draw_offset()[0] + self._sprite_offset[0]
        y = self.center()[1] + self.get_draw_offset()[1] + self._sprite_offset[1] + 12

        if not ignore_perturbs:
            x += self.get_perturbed_xy()[0]
            y += self.get_perturbed_xy()[1]

        return (round(x), round(y))

    def get_depth(self):
        return -(self.get_render_center(ignore_perturbs=True)[1] - self._sprite_offset[1])

    def get_perturbed_color(self):
        if self._perturb_color_ticks >= self._perturb_color_duration:
            return self.base_color
        else:
            prog = self._perturb_color_ticks / self._perturb_color_duration
            return Utils.linear_interp(self._perturb_color, self.base_color, prog)

    def update_action(self, world, force_finalize=False):
        if self.executing_action is not None:
            self.executing_action_ticks += 1
            if force_finalize or self.executing_action_ticks >= self.executing_action_duration:
                self.executing_action.finalize(world)

                self.executing_action = None
                self.executing_action_duration = 1
                self.executing_action_ticks = 0

                a_state = self.get_actor_state()

                if a_state.is_alive():
                    a_state.countdown_status_effects()
                    self._apply_status_effects(world)
            else:
                prog = Utils.bound(self.executing_action_ticks / self.executing_action_duration, 0.0, 1.0)
                self.executing_action.animate_in_world(prog, world)

    def _apply_status_effects(self, world):
        a_state = self.get_actor_state()
        old_hp = a_state.hp()

        pulse_color = None

        hp_change = 0
        for eff in a_state.all_status_effects():
            hp_change += eff.stat_value(stats.StatTypes.HP_REGEN)
            hp_change -= eff.stat_value(stats.StatTypes.POISON)

            if hp_change > 0:
                pulse_color = stats.StatTypes.HP_REGEN.get_color()
            elif hp_change < 0:
                pulse_color = stats.StatTypes.POISON.get_color()

        a_state.set_hp(old_hp + hp_change)
        new_hp = a_state.hp()

        if new_hp != old_hp and pulse_color is not None:
            self.perturb_color(pulse_color, 30)

        if new_hp > old_hp:
            world.show_floating_text("+{}".format(abs(new_hp - old_hp)), colors.G_TEXT_COLOR, 3, self)
        elif new_hp < old_hp:
            world.show_floating_text("-{}".format(abs(new_hp - old_hp)), colors.R_TEXT_COLOR, 3, self)

    def update(self, world):
        Entity.update(self, world)
        if not gs.get_instance().world_updates_paused():
            if self.is_performing_action():
                self.update_action(world)

            if self.get_vel()[0] < -1.5:
                self.set_facing_right(False)
            elif self.get_vel()[0] > 1.5:
                self.set_facing_right(True)

            if self.is_moving():
                self._was_moving = 0
            else:
                self._was_moving = Utils.bound(self._was_moving + 1, 0, 60)

        self.update_perturbations()
        self.update_images()

    def get_sprite(self):
        tick = gs.get_instance().anim_tick
        anim_rate = 2 if self.was_moving_recently() else 4
        return self.idle_sprites[(tick // anim_rate) % len(self.idle_sprites)]

    def set_facing_right(self, facing_right):
        self._facing_right = facing_right

    def facing_right(self):
        return self._facing_right

    def should_xflip(self):
        return self.facing_right()

    def set_color(self, color=(1.0, 1.0, 1.0)):
        self.base_color = color

    def perturb(self, max_offset, duration):
        self._perturb_points.clear()
        self._perturb_points.extend(Utils.get_shake_points(max_offset, duration, freq=4, falloff=3))

    def perturb_color(self, new_color, duration):
        self._perturb_color[0] = new_color[0]
        self._perturb_color[1] = new_color[1]
        self._perturb_color[2] = new_color[2]
        self._perturb_color_duration = duration
        self._perturb_color_ticks = 0

    def perturb_z(self, jump_height=16, jump_duration=20):
        self._z_perturb_points.clear()
        for i in range(0, jump_duration+1):
            # at start and end of jump, x = 0, at middle x = 1
            if i <= jump_duration / 2:
                x = i / (jump_duration / 2)
            else:
                x = 2 - i / (jump_duration / 2)
            self._z_perturb_points.append(-jump_height * math.sqrt(x))

    def update_images(self):
        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=2, depth=self.get_depth())

        sprite = self.get_sprite()

        x = self.get_render_center()[0] - (sprite.width() * self._img.scale()) // 2
        y = self.get_render_center()[1] - (sprite.height() * self._img.scale()) + self.get_perturbed_z()

        depth = self.get_depth()
        xflip = self.should_xflip()
        color = self.get_perturbed_color()
        self._img = self._img.update(new_model=sprite, new_color=color, new_x=x, new_y=y,
                                     new_depth=depth, new_xflip=xflip)

        super().update_images()  # get the shadow


class Player(ActorEntity):

    def __init__(self, x, y):
        ActorEntity.__init__(self, spriteref.player_idle_all)
        self.set_x(x)
        self.set_y(y)

        self._held_item_img = None

        self._visually_held_item_override = None

        self._targeting_animation_imgs = []

    def get_actor_state(self):
        return gs.get_instance().player_state()

    def get_controller(self):
        return gs.get_instance().player_controller()

    def get_sprite(self):
        anim_tick = gs.get_instance().anim_tick
        anim_rate = 2 if self.was_moving_recently() else 4
        holding_item = self.get_visually_held_item() is not None
        player_sprites = spriteref.get_player_sprites(self.was_moving_recently(), holding_item)

        return player_sprites[(anim_tick // anim_rate) % len(player_sprites)]

    def get_death_sound(self):
        return soundref.rand_deathscream_human()

    def get_depth(self):
        # XXX want to beat other actors
        return super().get_depth() - 1

    def set_visually_held_item_override(self, val):
        """
        meant to be used by Actions pretty much exclusively.
        callers had better eventually unset it too~

        val: None (unset), an Item, or False to indicate no item.
        """
        self._visually_held_item_override = val

    def get_visually_held_item(self):
        if self._visually_held_item_override is False:
            return None
        elif self._visually_held_item_override is not None:
            return self._visually_held_item_override

        if self.executing_action is not None:
            if self.executing_action.get_item() is not None:
                return self.executing_action.get_item()

        action_prov = gs.get_instance().get_targeting_action_provider()
        if action_prov is not None and action_prov.get_item() is not None:
           return action_prov.get_item()

        return self.get_actor_state().held_item

    def perturb(self, max_offset, duration):
        shake_pts = gs.get_instance().add_screenshake(max_offset, duration, falloff=3, freq=4)

        self._perturb_points.clear()
        self._perturb_points.extend(shake_pts)

    def update_held_item_image(self):
        held_item = self.get_visually_held_item()
        scale = 2
        if self._held_item_img is not None and held_item is None:
            RenderEngine.get_instance().remove(self._held_item_img)
            self._held_item_img = None
        elif held_item is not None and self._held_item_img is None:
            self._held_item_img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=scale)

        if self._held_item_img is not None:
            x_center = self.get_render_center()[0]
            y_center = self.get_render_center()[1]

            my_height = self.get_sprite().height() * scale
            item_sprite = held_item.get_entity_sprite()
            sprite_rot = held_item.sprite_rotation()
            sprite_w = item_sprite.width() if sprite_rot % 2 == 0 else item_sprite.height()
            sprite_h = item_sprite.height() if sprite_rot % 2 == 0 else item_sprite.width()

            draw_x = x_center - scale * (int(sprite_w / 2) + (1 if self.should_xflip() else -1))

            if not self.is_moving():
                bobs = (0, 1)
                bob_offset = bobs[(gs.get_instance().anim_tick // 4) % 2]
            else:
                bobs = (0, 1, 2, 1)  # these numbers are solely dependant on how the sprites are drawn..
                bob_offset = bobs[(gs.get_instance().anim_tick // 2) % 4]

            draw_y = y_center - my_height - scale * (1 + sprite_h - bob_offset) + self.get_perturbed_z()

            self._held_item_img = self._held_item_img.update(new_model=item_sprite,
                                                             new_rotation=sprite_rot,
                                                             new_x=draw_x, new_y=draw_y,
                                                             new_color=held_item.color,
                                                             new_scale=scale,
                                                             new_depth=self.get_depth())

    def update_targeting_entities(self, world):
        positions = []  # list of (x, y, color)

        target_coords = gs.get_instance().get_targetable_coords_in_world()
        for xy in target_coords:
            positions.append((xy[0], xy[1], target_coords[xy]))
        positions.sort()

        while len(self._targeting_animation_imgs) > len(positions):
            t_img = self._targeting_animation_imgs.pop()
            RenderEngine.get_instance().remove(t_img)

        while len(positions) > len(self._targeting_animation_imgs):
            t_img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=4, depth=float("inf"))
            self._targeting_animation_imgs.append(t_img)

        sprite = spriteref.UI.world_cursors[(gs.get_instance().anim_tick // 2) % len(spriteref.UI.world_cursors)]
        for i in range(0, len(positions)):
            x = positions[i][0] * world.cellsize()
            y = positions[i][1] * world.cellsize()
            color = positions[i][2]
            t_img = self._targeting_animation_imgs[i].update(new_model=sprite, new_x=x, new_y=y, new_color=color)
            self._targeting_animation_imgs[i] = t_img

    def visible_in_darkness(self):
        return True
            
    def update(self, world):
        ActorEntity.update(self, world)
        self.update_held_item_image()
        self.update_targeting_entities(world)

    def request_next_action(self, world):
        return ActorEntity.request_next_action(self, world)
        
    def is_player(self):
        return True

    def handle_death(self, world):
        pos = self.get_render_center(ignore_perturbs=True)

        corpse_anim = PlayerCorpseAnimation(pos[0], pos[1], 32)
        corpse_anim.set_finish_behavior(AnimationEntity.FREEZE_ON_FINISH)
        corpse_anim.set_xflipped(self.should_xflip())
        world.add(corpse_anim)

        light_emitter = LightEmitterAnimation(pos[0], pos[1], 90, self.get_light_level(), 0)
        world.add(light_emitter)

        sound_effects.play_sound(self.get_death_sound())

        gs.get_instance().event_queue().add(events.PlayerDiedEvent(), delay=240)
        world.remove(self)

    def should_xflip(self):
        return not self.facing_right()

    def valid_to_stand_on(self, world, x, y):
        return (Entity.valid_to_stand_on(self, world, x, y) and
                not world.get_hidden_at(x, y))

    def all_bundles(self):
        for b in super().all_bundles():
            yield b
        if self._held_item_img is not None:
            yield self._held_item_img
        for b in self._targeting_animation_imgs:
            yield b
 
 
class Enemy(ActorEntity):

    def __init__(self, x, y, state, sprites, controller, shadow_sprite=None, sprite_offset=(0, 0), shadow_offset=(0, 0)):
        ActorEntity.__init__(self, sprites, sprite_offset=sprite_offset, shadow_offset=shadow_offset)
        self._enemy_state = state
        self._enemy_controller = controller
        self.set_x(x)
        self.set_y(y)
        self.state = state
        self.sprites = sprites
        self._shadow_sprite = shadow_sprite
        self._bar_imgs = []

        # floating z's above enemy while waiting for player
        self._zee_img_idx_offset = 0
        self._zee_img = None

    def get_actor_state(self):
        return self._enemy_state

    def get_controller(self):
        return self._enemy_controller

    def _update_bar_imgs(self, bars):
        """bars: list of (float: percent, tuple: color)"""

        while len(self._bar_imgs) > len(bars):
            bar_img = self._bar_imgs.pop()
            RenderEngine.get_instance().remove(bar_img)

        while len(self._bar_imgs) < len(bars):
            self._bar_imgs.append(img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2))

        cx = self.get_render_center(ignore_perturbs=True)[0]
        cy = self.get_render_center(ignore_perturbs=True)[1] + 4

        for i in range(0, len(bars)):
            pcnt, color = bars[i]
            pcnt = Utils.bound(pcnt, 0.0, 1.0)

            n = len(spriteref.progress_spinner)
            bar_sprite = spriteref.progress_spinner[int(min(0.99, pcnt) * n)]

            bar_img = self._bar_imgs[i]

            bar_x = cx - (0.5 * bar_img.scale() * bar_sprite.width())
            bar_y = cy + bar_img.scale() * (bar_sprite.height() - 1) * i

            self._bar_imgs[i] = bar_img.update(new_model=bar_sprite,
                                               new_x=bar_x,
                                               new_y=bar_y,
                                               new_color=color,
                                               new_depth=self.get_depth())

    def _update_z_img(self, should_show):
        if not should_show or self._img is None:
            if self._zee_img is not None:
                RenderEngine.get_instance().remove(self._zee_img)
                self._zee_img = None
        else:
            anim_tick = gs.get_instance().anim_tick
            if self._zee_img is None:
                # want the z's to start on the first frame of the animation
                self._zee_img_idx_offset = (-anim_tick) % len(spriteref.sleeping_zees)
                self._zee_img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER)

            z_idx = (self._zee_img_idx_offset + anim_tick) % len(spriteref.sleeping_zees)
            sprite = spriteref.sleeping_zees[z_idx]
            cx = self.get_render_center()[0]
            y_bottom = self.get_render_center()[1] - self.get_sprite().height() * self._img.scale() // 2
            scale = 2
            self._zee_img = self._zee_img.update(new_model=sprite,
                                                 new_x=cx - (sprite.width() * scale) // 2,
                                                 new_y=y_bottom - sprite.height() * scale,
                                                 new_scale=scale,
                                                 new_depth=self.get_depth())

    def all_bundles(self):
        for bun in super().all_bundles():
            yield bun
        for bar_img in self._bar_imgs:
            yield bar_img
        if self._zee_img is not None:
            yield self._zee_img
        
    def update(self, world):
        super().update(world)

        bars = []
        a_state = self.get_actor_state()
        if 0 < a_state.hp() < a_state.max_hp():
            bars.append((a_state.hp() / a_state.max_hp(), (1, 0, 0)))

        self._update_bar_imgs(bars)

        # figuring out whether we're "asleep" or not
        ps = gs.get_instance().player_state()
        es = self.get_actor_state()

        show_zees = False

        if not self.is_performing_action() and not es.ready_to_act() and ps.ready_to_act():
            my_turns_til_act = es.turns_until_next_activation()
            p_turns_til_next_act = ps.turns_until_next_activation()

            show_zees = my_turns_til_act >= p_turns_til_next_act

        self._update_z_img(show_zees)
        
    def is_enemy(self):
        return True
        

class ChestEntity(Entity):

    def __init__(self, grid_x, grid_y):
        Entity.__init__(self, 0, 0, 24, 24)
        self.set_center((grid_x + 0.5) * 64, (grid_y + 0.5) * 64)
        self._is_open = False
        self._left_side = random.random() > 0.5
        
    def is_chest(self):
        return True
    
    def get_shadow_sprite(self):
        return spriteref.chest_shadow

    def visible_in_darkness(self):
        return False

    def get_depth(self):
        return super().get_depth() + 1  # XXX need these to lose ties, basically
        
    def update_images(self):
        if self.is_open():
            model = spriteref.chest_open_1
        else:
            model = spriteref.chest_closed

        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER)

        x = self.get_render_center()[0] - (model.width() * self._img.scale()) // 2
        y = self.get_render_center()[1] - (model.height() * self._img.scale())
        depth = self.get_depth()
        self._img = self._img.update(new_model=model, new_scale=2, new_x=x, new_y=y, new_depth=depth)
        
        super().update_images()
        sh_x = self._shadow.x()
        sh_y = self._shadow.y()
        sh_s = self._shadow.scale()
        self._shadow = self._shadow.update(new_x=(sh_x + 9*sh_s), new_y=(sh_y - 2*sh_s))

    def is_open(self):
        return self._is_open
            
    def update(self, world):
        self.update_images()

    def is_interactable(self, world):
        return not self.is_open()

    def interact(self, world):
        if self._is_open:
            return
        else:
            self._is_open = True
            level = gs.get_instance().get_zone_level()
            loot = LootFactory.gen_chest_loot(level)

            sound_effects.play_sound(soundref.chest_open)

            for item in loot:
                world.add(ItemEntity(item, *self.center()))


class PickupEntity(Entity):
    """An entity that slides across the floor and can be "picked up" by actors."""

    @staticmethod
    def rand_vel(speed=None, direction=None):
        speed = speed if speed is not None else 2 + random.random() * 3
        if direction is None:
            direction = (0, 0)  # becomes random
        direction = Utils.set_length(direction, 1.0)
        return [speed * direction[0], speed * direction[1]]

    def __init__(self, cx, cy, sprites, sprite_rotation=0, vel=None):
        x = cx - 8
        y = cy - 8
        Entity.__init__(self, x, y, 16, 16)
        self.sprites = sprites
        self.sprite_rotation = sprite_rotation
        self.vel = [vel[0], vel[1]] if vel is not None else ItemEntity.rand_vel()
        self.fric = 0.95
        self.bounce_offset = int(random.random() * 100)

        self.pickup_delay = 45
        self.time_touched = 0

        # for moving away from other stuff
        self.push_radius = 20

    def get_pickup_progress(self):
        return Utils.bound(self.time_touched / self.pickup_delay, 0, 1.0)

    def get_shadow_sprite(self):
        return spriteref.small_shadow

    def visible_in_darkness(self):
        return False

    def get_color(self):
        return (1, 1, 1)

    def get_sprite(self):
        return self.sprites[gs.get_instance().anim_tick % len(self.sprites)]

    def get_sprite_offset(self):
        return (0, 0)

    def update_images(self):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        anim_tick = gs.get_instance().anim_tick
        bounce = round(2*math.cos((anim_tick + self.bounce_offset) // 2))

        cur_sprite = self.get_sprite()

        offs = self.get_sprite_offset()

        spr_w = 2 * cur_sprite.width() if self.sprite_rotation % 2 == 0 else 2 * cur_sprite.height()
        spr_h = 2 * cur_sprite.height() if self.sprite_rotation % 2 == 0 else 2 * cur_sprite.width()

        x = self.get_render_center()[0] - spr_w // 2 + offs[0]
        y = self.get_render_center()[1] - spr_h - bounce + offs[1]
        depth = self.get_depth()

        self._img = self._img.update(new_x=x, new_y=y, new_color=self.get_color(),
                                     new_model=cur_sprite, new_depth=depth, new_rotation=self.sprite_rotation)

        super().update_images()

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

    def update(self, world):
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

        self.update_images()

    def is_pickup(self):
        return True

    def can_pickup(self, world, actor):
        return True


class ItemEntity(PickupEntity):
    def __init__(self, item, cx, cy, vel=None):
        self.item = item
        sprite = item.get_entity_sprite()
        PickupEntity.__init__(self, cx, cy, [sprite], sprite_rotation=item.sprite_rotation(), vel=vel)

    def get_color(self):
        return self.get_item().color

    def get_item(self):
        return self.item
        
    def is_item(self):
        return True

    def can_pickup(self, world, actor):
        if actor.is_player():
            return self.is_visible_in_world(world)
        else:
            return True


class DoorEntity(Entity):

    def __init__(self, grid_x, grid_y):
        Entity.__init__(self, grid_x*64, grid_y*64, 64, 64)
        self._is_horz = None
        self.sprites = None
        self.open_prog = 0

    def update_images(self):
        if self._is_horz is None or self.sprites is None:
            print("tried to update door image before _is_horz was calculated...")
            return

        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=4)

        prog = Utils.bound(self.open_prog, 0, 0.99)
        sprite = self.sprites[int(prog * len(self.sprites))]

        x = self.x()
        y = self.y() - (sprite.height() * self._img.scale() - self.h())
        depth = float('inf')  # should render behind all other entities
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, new_depth=depth)

    def set_open_progress_for_render(self, prog):
        self.open_prog = prog

    def remove_self_from_world(self, world):
        grid_xy = world.to_grid_coords(*self.center())
        world.set_geo(*grid_xy, World.FLOOR)
        world.door_opened(*grid_xy)
        world.remove(self)
        gs.get_instance().event_queue().add(events.DoorOpenEvent(self.get_uid(), *grid_xy))

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
        print("WARN: door is neither horizontal nor vertical: {}".format(self))
        return random.random() < 0.5

    def get_sprites(self, world):
        if self.can_open(world):
            return spriteref.door_h if self._is_horz else spriteref.door_v
        else:
            return spriteref.door_h_locked if self._is_horz else spriteref.door_v_locked

    def update(self, world):
        if self._is_horz is None:
            self._is_horz = self._calc_is_horz(world)

        self.sprites = self.get_sprites(world)
        self.update_images()

    def is_door(self):
        return True

    def can_open(self, world):
        return True

    def is_interactable(self, world):
        return not self.can_open(world) and self.get_locked_message(world) is not None

    def interact(self, world):
        if self.is_interactable(world):
            dia = Dialog(self.get_locked_message(world))
            gs.get_instance().dialog_manager().set_dialog(dia)
        else:
            print("WARN: interacted with non-interactable door..?")

    def get_locked_message(self, world):
        return "It's locked."


class SensorDoorEntity(DoorEntity):

    def __init__(self, grid_x, grid_y, sensor_range=8):
        DoorEntity.__init__(self, grid_x, grid_y)
        self.sensor_range = sensor_range

    def _get_blocking_enemies(self, world):
        return world.entities_in_circle(
            self.center(),
            self.sensor_range * world.cellsize(),
            onscreen=True,
            cond=lambda e: e.is_enemy() and e.is_visible_in_world(world))

    def can_open(self, world):
        return len(self._get_blocking_enemies(world)) == 0

    def get_locked_message(self, world):
        num_blocking = len(self._get_blocking_enemies(world))
        return "Access denied. Hostile entities nearby: {}".format(num_blocking)


class ExitEntity(Entity):

    def __init__(self, grid_x, grid_y, next_zone_id):
        Entity.__init__(self, grid_x * 64, (grid_y - 1) * 64, 64, 64)

        self.next_zone_id = next_zone_id
        self._is_opening = False
        self.count = 0

        self._animation_duration = 80
        self._door_animation_range = (0, 0.7)
        self._fade_animation_range = (0.5, 1.0)

    def get_sprite(self):
        start_open_tick = int(self._animation_duration * self._door_animation_range[0])
        end_open_tick = int(self._animation_duration * self._door_animation_range[1])
        if self.count < start_open_tick:
            return self.idle_sprites()[(gs.get_instance().anim_tick // 2) % 2]
        else:
            open_spr = self.opening_sprites()
            open_prog = Utils.bound((self.count - start_open_tick) / (end_open_tick - start_open_tick), 0, 0.999)
            idx = int(open_prog * len(open_spr))
            return open_spr[idx]

    def get_zone(self):
        return self.next_zone_id

    def idle_sprites(self):
        return spriteref.normal_door_idle

    def opening_sprites(self):
        return spriteref.normal_door_opening

    def sprite_offset(self, sprite, scale):
        return (0, 64 - sprite.height() * scale)

    def visible_in_darkness(self):
        return True

    def update_images(self):
        if self._img is None:
            self._img = img.ImageBundle(None, 0, 0, layer=spriteref.ENTITY_LAYER, scale=4)

        sprite = self.get_sprite()
        offs = self.sprite_offset(sprite, 4)

        x = self.x() + offs[0]
        y = self.y() + offs[1]
        self._img = self._img.update(new_x=x, new_y=y, new_model=sprite, new_depth=self.get_depth())

    def get_progress(self):
        return Utils.bound(self.count / self._animation_duration, 0.0, 1.0)

    def is_exit(self):
        return True

    def update(self, world):
        if self._is_opening:
            # pause game while door is opening
            gs.get_instance().pause_world_updates(2)

            if self.count < self._animation_duration:
                self.count += 1

                start_fade_tick = int(self._animation_duration * self._fade_animation_range[0])
                end_fade_tick = int(self._animation_duration * self._fade_animation_range[1])
                if self.count == start_fade_tick:
                    gs.get_instance().do_fade_sequence(0, 1, end_fade_tick - start_fade_tick + 1)

            else:
                new_zone_event = self.make_new_zone_event()
                gs.get_instance().event_queue().add(new_zone_event)

        self.update_images()

    def make_new_zone_event(self):
        return events.NewZoneEvent(self.next_zone_id, gs.get_instance().get_zone_id())

    def is_interactable(self, world):
        return True

    def interact(self, world):
        if self.next_zone_id is not None:
            self._is_opening = True
            sound_effects.play_sound(soundref.exit_door_open)
        else:
            dia = Dialog("This path doesn't lead anywhere...")
            gs.get_instance().dialog_manager().set_dialog(dia)


class ReturnExitEntity(ExitEntity):

    def __init__(self, grid_x, grid_y, next_zone_id):
        ExitEntity.__init__(self, grid_x, grid_y, next_zone_id)
        self.set_y((grid_y + 1) * 64)

    def make_new_zone_event(self):
        if self.next_zone_id is not None:
            return events.NewZoneEvent(self.next_zone_id, gs.get_instance().get_zone_id())
        else:
            return None

    def get_sprite(self):
        sprites = spriteref.return_door_smoke
        anim_tick = gs.get_instance().anim_tick
        return sprites[anim_tick % len(sprites)]

    def sprite_offset(self, sprite, scale):
        return (0, -64)

    def is_exit(self):
        # maybe one day, but not now~
        return False


class BossExitEntity(ExitEntity):

    def idle_sprites(self):
        return spriteref.boss_door_idle

    def opening_sprites(self):
        return spriteref.boss_door_opening


class DecorationEntity(Entity):

    def __init__(self, sprite, grid_x, grid_y, scale=2, draw_offset=(0, 0), interact_dialog=None):
        """
        sprite: ImageModel or a list of ImageModels
        interact_dialog: Dialog
        """
        Entity.__init__(self, int((grid_x + 0.5) * 64), int((grid_y + 0.5) * 64), 1, 0)

        self._interact_dialog = interact_dialog
        self._draw_offset = draw_offset
        self._sprites = Utils.listify(sprite)
        self._scale = scale

    def get_render_center(self):
        if self._img is None:
            return super().center()
        return (self.x() + self._draw_offset[0], self.y() + self._draw_offset[1])

    def update(self, world):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=self._scale)

        sprite = self._sprites[gs.get_instance().anim_tick // 2 % len(self._sprites)]
        x = self.get_render_center()[0] - (sprite.width() * self._img.scale()) // 2
        y = self.get_render_center()[1] - (sprite.height() * self._img.scale())
        depth = self.get_depth()

        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y, new_depth=depth)

    def all_bundles(self):
        for bun in Entity.all_bundles(self):
            yield bun
        if self._img is not None:
            yield self._img

    def set_interact_dialog(self, dialog):
        self._interact_dialog = dialog

    @staticmethod
    def wall_decoration(sprites, grid_x, grid_y, scale=2, interact_dialog=None):
        """
        sprite: ImageModel or a list of ImageModels
        interact_dialog: Dialog
        """
        sprites = Utils.listify(sprites)
        CELLSIZE = 64  # this better never change~
        offset = (0, 8 * scale + CELLSIZE // 2)
        return DecorationEntity(sprites, grid_x, grid_y - 1, scale=scale, draw_offset=offset,
                                interact_dialog=interact_dialog)

    @staticmethod
    def sign_decoration(grid_x, grid_y, dialog_text):
        sprite = spriteref.standalone_sign_decoration
        CELLSIZE = 64  # this better never change~
        scale = 2
        x_center = (grid_x + 0.5) * CELLSIZE
        y_bottom = (grid_y + 0.5) * CELLSIZE
        offset = (0, -(sprite.height() - 1) * scale)

        return DecorationEntity(sprite, x_center, y_bottom, scale=scale, draw_offset=offset,
                                interact_dialog=PlayerDialog(dialog_text))

    def is_visible_in_world(self, world):
        grid_xy = world.to_grid_coords(*self.get_render_center())
        if world.get_hidden(grid_xy[0], grid_xy[1]):
            return False
        elif self.visible_in_darkness():
            return True
        else:
            return world.get_visible(grid_xy[0], grid_xy[1])

    def visible_in_darkness(self):
        return False

    def is_interactable(self, world):
        return self._interact_dialog is not None

    def interact(self, world):
        if self._interact_dialog is not None:
            gs.get_instance().dialog_manager().set_dialog(self._interact_dialog)


class NpcEntity(Entity):

    def __init__(self, grid_x, grid_y, npc_template, conversation, color=(1, 1, 1)):
        Entity.__init__(self, 0, 0, 24, 24)
        self.set_center((grid_x + 0.5) * 64, (grid_y + 0.5) * 64)

        self.npc_template = npc_template
        self.conv = conversation
        self.npc_interact_count = 0

        self.color = color
        self._facing_right = True

    def get_shadow_sprite(self):
        return self.get_npc_template().shadow_sprite

    def get_npc_template(self):
        return self.npc_template

    def get_sprite(self):
        anim_tick = gs.get_instance().anim_tick
        sprites = self.get_npc_template().get_entity_sprites()
        if sprites is not None and len(sprites) > 0:
            return sprites[(anim_tick // 4) % len(sprites)]
        else:
            return None

    def get_render_center(self):
        xy = super().get_render_center()
        return (xy[0], xy[1] + 12)

    def visible_in_darkness(self):
        return False

    def update_images(self):
        if self._img is None:
            self._img = img.ImageBundle.new_bundle(spriteref.ENTITY_LAYER, scale=2)

        sprite = self.get_sprite()
        x = self.get_render_center()[0] - (sprite.width() * self._img.scale()) // 2
        y = self.get_render_center()[1] - (sprite.height() * self._img.scale())
        depth = self.get_depth()
        xflip = self._facing_right
        self._img = self._img.update(new_model=sprite, new_x=x, new_y=y,
                                     new_depth=depth, new_xflip=xflip, new_color=self.color)

        super().update_images()  # just updating shadow

    def update(self, world):
        p = world.get_player()
        if p is not None:
            p_x = p.center()[0]
            if p_x < self.center()[0] - 32:
                self._facing_right = False
            elif p_x > self.center()[0] + 32:
                self._facing_right = True

        self.update_images()

    def is_npc(self):
        return True

    def is_interactable(self, world):
        return True

    def interact(self, world):
        if self.conv is not None:
            import src.game.npc as npc
            dia = npc.ConversationFactory.get_dialog(self.conv, self.npc_interact_count)
            if dia is not None:
                gs.get_instance().dialog_manager().set_dialog(dia)
            gs.get_instance().set_story_var(self.conv.get_id(), True)

        self.npc_interact_count += 1


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

    def update(self, world):
        if gs.get_instance().world_updates_paused() and not self.ignore_updates_paused:
            return

        p = world.get_player()
        inside = p is not None and Utils.rect_contains(self.rect, p.center())
        if self.player_inside != inside:
            if inside:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_enter_event(self.box_id))
                self.player_entered(p, world)
            else:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_exit_event(self.box_id))
                self.player_left(p, world)
            self.player_inside = inside
            self.player_in_range_count = 0

        if self.player_inside:
            if not self.no_more_firings and self.player_in_range_count == self.delay:
                gs.get_instance().event_queue().add(events.TriggerBoxEvent.new_trigger_event(self.box_id))
                self.fire_action(p, world)
                if self.just_once:
                    self.no_more_firings = True

            self.player_in_range_count += 1

    def player_entered(self, player, world, render_action):
        pass

    def fire_action(self, player, world, render_action):
        pass

    def player_left(self, player, world, render_action):
        pass


class DialogTriggerBox(TriggerBox):

    def __init__(self, dialog, grid_pos, grid_size=(1, 1), just_once=False, delay=0, ignore_updates_paused=False, box_id=None):
        TriggerBox.__init__(self, grid_pos, grid_size=grid_size, just_once=just_once, delay=delay,
                            ignore_updates_paused=ignore_updates_paused, box_id=box_id)
        self.dialog = dialog

    def fire_action(self, player, world, render_action):
        gs.get_instance().dialog_manager().set_dialog(self.dialog)


class MessageTriggerBox(TriggerBox):

    def __init__(self, text, grid_pos, grid_size=(1, 1), just_once=False, delay=0, ignore_updates_paused=False, box_id=None):
        TriggerBox.__init__(self, grid_pos, grid_size=grid_size, just_once=just_once, delay=delay,
                            ignore_updates_paused=ignore_updates_paused, box_id=box_id)
        self.text = text
        self._hover_text = None

    def fire_action(self, player, world, render_action):
        self._hover_text = HoverTextEntity(self.text, player, offset=(0, -90), bounds=self.rect)
        world.add(self._hover_text)

    def player_left(self, player, world, render_action):
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

    def update(self, world):
        if self._dirty:
            if self._text_img is not None:
                render_eng = RenderEngine.get_instance()
                for bun in self._text_img.all_bundles():
                    render_eng.remove(bun)
                self._text_img = None

        sc = 2
        text_sc = 1

        if self._text_img is None:
            self._text_img = TextImage(0, 0, self.text, spriteref.ENTITY_LAYER, scale=text_sc)

        for i in range(0, len(self._border_imgs)):
            if i == 7:
                continue  # bottom border is more complicated
            if self._border_imgs[i] is None:
                self._border_imgs[i] = img.ImageBundle(spriteref.UI.hover_text_edges[i], 0, 0, scale=sc,
                                                       layer=spriteref.ENTITY_LAYER)

        if self._bottom_imgs[0] is None:
            self._bottom_imgs[0] = img.ImageBundle(spriteref.UI.hover_text_edges[7], 0, 0, scale=sc,
                                                   layer=spriteref.ENTITY_LAYER)
        if self._bottom_imgs[1] is None:
            self._bottom_imgs[1] = img.ImageBundle(spriteref.UI.hover_text_bottom_arrow, 0, 0, scale=sc,
                                                   layer=spriteref.ENTITY_LAYER)
        if self._bottom_imgs[2] is None:
            self._bottom_imgs[2] = img.ImageBundle(spriteref.UI.hover_text_edges[7], 0, 0, scale=sc,
                                                   layer=spriteref.ENTITY_LAYER)

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

    def all_bundles(self):
        for bun in Entity.all_bundles(self):
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

