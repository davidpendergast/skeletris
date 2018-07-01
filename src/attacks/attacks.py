import random

import src.world.entities as entities
from src.utils.util import Utils
from src.game.stats import PlayerStatType, StatType


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

            att_speed = 1.0 / self.current_attack.base_duration
            att_speed *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_SPEED))
            self.attack_dur = max(1, round(1.0 / att_speed))

            del_speed = 1.0 / self.current_attack.base_delay
            del_speed *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_SPEED))
            self.delay_dur = max(1, round(1.0 / del_speed))

    def update(self, entity, world, gs):
        if self.is_active():
            if self.attack_tick == self.attack_dur:
                if entity.is_player():
                    stat_lookup = gs.player_state()
                else:
                    stat_lookup = entity.state

                targets = self.current_attack.activate(gs, entity, world, stat_lookup)

                for target in targets:
                    t_ent, t_state = target
                    dmg = stat_lookup.stat_value(StatType.ATT)
                    dmg *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_DAMAGE))
                    dmg *= self.current_attack.base_damage

                    sub = Utils.sub(t_ent.center(), entity.center())
                    kb = Utils.set_length(sub, self.current_attack.knockback)
                    t_state.deal_damage(dmg, knockback=kb)

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
        self.base_duration = 15
        self.base_delay = 12
        self.base_radius = 64
        self.base_damage = 1.0
        self.knockback = 1

    def activate(self, gs, entity, world, stat_lookup):
        """
            returns: list of tuples (Entity, ActorState) hit by attack.
        """
        att_range = self.base_radius
        att_range *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_RADIUS))

        hit_entities = world.entities_in_circle(entity.center(), att_range)

        res = []

        for e in hit_entities:
            if entity.can_damage(e):
                e_state = gs.player_state() if e.is_player() else e.state
                res.append((e, e_state))

        return res


class GroundPoundAttack(Attack):
    def __init__(self):
        Attack.__init__(self, "Satan's Circle")
        self.base_duration = 35
        self.base_delay = 12
        self.base_radius = 64
        self.base_damage = 0.65
        self.knockback = 0.25

    def activate(self, gs, entity, world, stat_lookup):
        """
            returns: list of actor states that got hit
        """
        res = Attack.activate(self, gs, entity, world, stat_lookup)

        pos = entity.center()
        circle = entities.AttackCircleArt(*pos, 60)
        world.add(circle)

        return res


class TouchAttack(Attack):
    def __init__(self):
        Attack.__init__(self, "Evil Touch")
        self.base_duration = 15
        self.base_delay = 12
        self.base_radius = 42
        self.base_damage = 1.0
        self.knockback = 2


GROUND_POUND = GroundPoundAttack()
TOUCH_ATTACK = TouchAttack()


