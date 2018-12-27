from enum import Enum
import random

from src.world.worldstate import World
from src.world.entities import Player
from src.game.actorstate import EnemyState, PathfindingType
import src.game.spriteref as spriteref
import src.attacks.attacks as attacks

from src.utils.util import Utils


class BossID(Enum):

    CAVE_HORROR = "CAVE_HORROR"


class BossFightController:

    def __init__(self, boss_id):
        self._boss_id = boss_id

    def get_boss_id(self):
        return self._boss_id

    def build_world(self):
        return None

    def get_opening_cinematic(self):
        return []

    def get_ending_cinematic(self):
        return []

    def update(self, world, gs, input_state, render_engine):
        pass


class CaveHorrorController(BossFightController):

    def __init__(self):
        BossFightController.__init__(self, BossID.CAVE_HORROR)

    def build_world(self):
        w = World(7, 7)
        for x in range(0, 7):
            for y in range(0, 7):
                if x == 0 or x == 6 or y == 0 or y == 6:
                    w.set_geo(x, y, World.WALL)
                else:
                    w.set_geo(x, y, World.FLOOR)
        w.add(Player(0, 0), gridcell=(2, 2))

        return w


def get_boss_controller(boss_id):
    if boss_id == BossID.CAVE_HORROR:
        return CaveHorrorController()
    else:
        return None


class FrogBossState(EnemyState):

    MODE_RESTING = 1
    MODE_CHASE = 2
    MODE_PRE_LEAP = 3
    MODE_LEAPING = 4

    def __init__(self, template, level, stats):
        EnemyState.__init__(self, template, level, stats)
        self._current_mode = FrogBossState.MODE_RESTING
        self._current_mode_ticks = 0

        self._jump_max_height = 64
        self._z = 0  # distance off ground

        self._leap_end = None       # (int, int)
        self._leap_start = None     # (int, int)
        self._leap_duration = None  # int

    def duplicate(self):
        return FrogBossState(self.template, self.level(), dict(self.stats))

    def _get_sprite(self, entity, world, gs):
        speed = 2
        if self._current_mode == FrogBossState.MODE_LEAPING:
            if self._z > 0:
                # rise for first half of mode, then fall
                if self._current_mode_ticks < self._leap_duration / 2:
                    sprites = spriteref.Bosses.frog_airborn_rising
                else:
                    sprites = spriteref.Bosses.frog_airborn_falling
            else:
                sprites = spriteref.Bosses.frog_idle_down
        elif self._current_mode == FrogBossState.MODE_PRE_LEAP:
            sprites = spriteref.Bosses.frog_idle_down
        elif self._current_mode == FrogBossState.MODE_RESTING:
            sprites = spriteref.Bosses.frog_idle_1
        elif Utils.mag(entity.get_vel()) > 0:
            speed = 1
            sprites = spriteref.Bosses.frog_idle_mouth
        else:
            sprites = spriteref.Bosses.frog_idle_2

        return sprites[(gs.anim_tick // speed) % len(sprites)]

    def _get_sprite_offset(self):
        return (0, 10*2 - self._z)

    def get_pathfinding(self):
        if self._current_mode in (FrogBossState.MODE_RESTING, FrogBossState.MODE_PRE_LEAP, FrogBossState.MODE_LEAPING):
            return PathfindingType.STOPPED
        else:
            return PathfindingType.BASIC_CHASE

    def _get_leap_delay(self):
        return 45

    def _get_leap_duration(self):
        return 30

    def _should_attack(self, entity, world):
        if self._current_mode == FrogBossState.MODE_LEAPING:
            # can't attack while airborne
            return False
        else:
            return EnemyState._should_attack(self, entity, world)

    def update(self, entity, world, gs, input_state):

        player = world.get_player()
        if not gs.world_updates_paused() and player is not None:
            self._current_mode_ticks += 1

            if self._current_mode == FrogBossState.MODE_PRE_LEAP:
                if self._current_mode_ticks > self._get_leap_delay():
                    self._current_mode = FrogBossState.MODE_LEAPING
                    self._current_mode_ticks = 0

                    self._leap_duration = self._get_leap_duration()
                    self._leap_start = entity.center()
                    self._leap_end = player.center()

                    if self._leap_start[0] < self._leap_end[0]:
                        self.facing_left = False
                    elif self._leap_start[0] > self._leap_end[0]:
                        self.facing_left = True

            if self._current_mode == FrogBossState.MODE_LEAPING:
                if self._current_mode_ticks >= self._leap_duration:
                    self.attack_state.set_attack(attacks.FROG_ATTACK)
                    self.attack_state.start_attack(self)
                    gs.add_screenshake(15, 41, freq=4)

                    if random.random() < 0.66:
                        self._current_mode = FrogBossState.MODE_PRE_LEAP
                    else:
                        self._current_mode = FrogBossState.MODE_RESTING
                    self._current_mode_ticks = 0
                else:
                    prog = Utils.bound(self._current_mode_ticks / self._leap_duration, 0.0, 1.0)
                    pos = Utils.linear_interp(self._leap_start, self._leap_end, prog)
                    entity.set_center(pos[0], pos[1])

                    #  mmm delicious math
                    a = -4 * self._jump_max_height
                    b = 4 * self._jump_max_height
                    self._z = (a * prog * prog) + (b * prog)
            else:
                self.attack_state.set_attack(attacks.TOUCH_ATTACK)

            if self._current_mode_ticks > 45 and self._current_mode in (FrogBossState.MODE_RESTING, FrogBossState.MODE_CHASE):
                if random.random() < 0.005 * (self._current_mode_ticks - 45):
                    if self._current_mode != FrogBossState.MODE_RESTING:
                        next_choices = [FrogBossState.MODE_RESTING, FrogBossState.MODE_CHASE, FrogBossState.MODE_PRE_LEAP]
                    else:
                        next_choices = [FrogBossState.MODE_CHASE, FrogBossState.MODE_PRE_LEAP]
                    self._current_mode = random.choice(next_choices)
                    self._current_mode_ticks = 0

        EnemyState.update(self, entity, world, gs, input_state)

