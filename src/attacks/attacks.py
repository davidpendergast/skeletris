import random

import src.game.stats
import src.world.entities as entities
from src.utils.util import Utils
from src.game.stats import PlayerStatType


class AttackState:
    def __init__(self):
        self.attack_tick = 0

        self.attack_dur = 1
        self.delay_dur = 1

        self.current_attack = None
        self._next_att = None

    def can_attack(self):
        return not self.is_active() and self.current_attack is not None

    def start_attack(self, stat_lookup):
        if not self.can_attack():
            return False
        else:
            print("starting attack: " + str(self.current_attack.name))
            self.attack_tick = 1
            self.attack_dur = stat_lookup.stat_value(PlayerStatType.TICKS_PER_ATTACK)
            self.delay_dur = 12

    def update(self, entity, world, gs):
        if self.is_active():
            if self.attack_tick == self.attack_dur:
                if entity.is_player():
                    stat_lookup = gs.player_state()
                else:
                    stat_lookup = entity.state

                targets = self.current_attack.activate(gs, entity, world, stat_lookup)

                for t in targets:
                    t.deal_damage(15)

            elif self.attack_tick >= self.attack_dur + self.delay_dur:
                self._finish_attack()

            if self.is_active():
                self.attack_tick += 1

    def is_active(self):
        return self.attack_tick > 0

    def is_attacking(self):
        return 0 < self.attack_tick <= self.attack_dur

    def is_delaying(self):
        return self.attack_tick - self.attack_dur > 0

    def total_progress(self):
        return Utils.bound(self.attack_tick / (self.attack_dur + self.delay_dur), 0.0, 0.999)

    def attack_progress(self):
        return Utils.bound(self.attack_tick / self.attack_dur, 0.0, 0.999)

    def delay_progress(self):
        return Utils.bound((self.attack_tick - self.attack_dur) / self.delay_dur, 0.0, 0.999)

    def _finish_attack(self):
        self.attack_tick = 0
        if self._next_att is not None:
            self.current_attack = self._next_att
            self._next_att = None

    def set_attack(self, attack):
        if self.is_attacking():
            self._next_att = attack
        else:
            self.current_attack = attack


class Attack:
    def __init__(self, name):
        self.name = name
        self.base_windup = 0
        self.base_duration = 15
        self.base_delay = 12
        self.base_radius = 64
        self.base_damage = 20
        self.base_range = 128

    def activate(self, gs, entity, world, stat_lookup):
        pass

    def deliver_damage(self, state_from, state_to):
        pass


class GroundPoundAttack(Attack):
    def __init__(self):
        Attack.__init__(self, "Satan's Circle")

    def activate(self, gs, entity, world, stat_lookup):
        """
            returns: list of actor states that got hit
        """
        pos = entity.center()
        circle = entities.AttackCircleArt(*pos, 60)
        world.add(circle)
        att_range = stat_lookup.stat_value(PlayerStatType.ATTACK_RADIUS)

        hit_entities = world.entities_in_circle(pos, att_range)

        res = []

        for e in hit_entities:
            if entity.can_damage(e):
                e_state = gs.player_state() if e.is_player() else e.state
                res.append(e_state)

        return res

GROUND_POUND = GroundPoundAttack()


