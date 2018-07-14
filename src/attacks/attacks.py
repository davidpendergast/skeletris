import random

import src.world.entities as entities
from src.utils.util import Utils
from src.game.stats import StatType


class AttackState:
    def __init__(self):
        self.attack_tick = 0

        self.attack_dur = 1
        self.delay_dur = 1

        self.current_attack = None
        self._next_att = None

        self._delayed_attacks_this_tick = []  # list of tuples (position, target_entity, attack)

    def set_attack(self, attack):
        if self.is_attacking():
            self._next_att = attack
        else:
            self.current_attack = attack

    def can_attack(self):
        return not self.is_active() and self.current_attack is not None

    def start_attack(self, stat_lookup):
        if not self.can_attack():
            return False
        else:
            self.attack_tick = 1

            self.attack_dur = self.get_attack_dur(stat_lookup)

            self.delay_dur = self.get_delay_dur(stat_lookup)

    def get_attack_dur(self, stat_lookup):
        att_speed = 1.0 / self.current_attack.base_duration
        att_speed *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_SPEED))
        return max(1, round(1.0 / att_speed))

    def get_delay_dur(self, stat_lookup):
        del_speed = 1.0 / self.current_attack.base_delay
        del_speed *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_SPEED))
        return max(1, round(1.0 / del_speed))

    def update(self, entity, world, gs):
        stat_lookup = entity.get_actorstate(gs)

        num_hit = 0
        dmg_dealt = 0

        if len(self._delayed_attacks_this_tick) > 0:
            for del_att in self._delayed_attacks_this_tick:
                pos, t_entity, attack = del_att
                t_state = t_entity.get_actorstate(gs)

                successful, dmg = self._resolve_attack(attack, stat_lookup, pos,
                                                       t_state, t_entity)
                if successful:
                    num_hit += 1
                    dmg_dealt += dmg

            self._delayed_attacks_this_tick.clear()

        if self.is_active():
            if self.attack_tick == self.attack_dur:
                targets = self.current_attack.activate(gs, entity, world, stat_lookup)

                for target in targets:
                    t_ent = target
                    t_state = t_ent.get_actorstate(gs)

                    successful, dmg = self._resolve_attack(self.current_attack, stat_lookup,
                                                           entity.center(), t_state, t_ent)

                    if successful:
                        num_hit += 1
                        dmg_dealt += dmg

            elif self.attack_tick >= self.attack_dur + self.delay_dur:
                self._finish_attack()

            if self.is_active():
                self.attack_tick += 1

        if num_hit > 0:
            healing = stat_lookup.stat_value(StatType.LIFE_ON_HIT) * num_hit
            healing += stat_lookup.stat_value(StatType.LIFE_LEECH) * 0.01 * dmg_dealt
            stat_lookup.do_heal(healing)

    def _resolve_attack(self, attack, stat_lookup, source_pos, t_state, t_ent):
        """
            returns (bool: hit, dmg_dealt)
        """
        att_defense = stat_lookup.stat_value(StatType.DEF) + stat_lookup.stat_value(StatType.ACCURACY)
        defend_defense = t_state.stat_value(StatType.DEF) + t_state.stat_value(StatType.DODGE)

        chance_to_hit = Utils.bound(2 * att_defense / (att_defense + defend_defense), 0.10, 1.0)

        if random.random() <= chance_to_hit:
            dmg = self.get_dmg(stat_lookup, attack=attack)
            spread = 0.25
            dmg_actual = dmg * (1 + spread * 2 * (0.5 - random.random()))
            sub = Utils.sub(t_ent.center(), source_pos)
            kb = Utils.set_length(sub, self.current_attack.knockback)
            dmg_color = self.current_attack.dmg_color
            t_state.deal_damage(dmg_actual, knockback=kb, color=dmg_color)
            return (True, dmg_actual)
        else:
            t_state.was_missed()
            return (False, 0)

    def delayed_attack_landed(self, pos, target_entity, attack):
        self._delayed_attacks_this_tick.append((pos, target_entity, attack))

    def get_dps(self, stat_lookup):
        if self.current_attack is None:
            return 0.0

        total_dur = self.get_delay_dur(stat_lookup) + self.get_attack_dur(stat_lookup)
        total_dmg = self.get_dmg(stat_lookup)

        return total_dmg / (total_dur / 60.0)

    def get_dmg(self, stat_lookup, attack=None):
        att = self.current_attack if attack is None else attack
        dmg = stat_lookup.stat_value(StatType.ATT)
        dmg *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_DAMAGE))
        return dmg * att.base_damage

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


class Attack:
    def __init__(self, name):
        self.name = name
        self.base_duration = 15
        self.base_delay = 12
        self.base_radius = 64
        self.base_damage = 1.0
        self.knockback = 1
        self.dmg_color = (1, 0, 0)

    def activate(self, gs, entity, world, stat_lookup):
        """
            returns: list of Entities hit by attack.
        """
        att_range = self.base_radius
        att_range *= (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_RADIUS))

        hit_entities = world.entities_in_circle(entity.center(), att_range)

        res = []

        for e in hit_entities:
            if entity.can_damage(e):
                res.append(e)

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
        res = Attack.activate(self, gs, entity, world, stat_lookup)
        radius = self.base_radius * (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_RADIUS))
        pos = entity.center()
        circle = entities.AttackCircleArt(*pos, radius, 60, color=(1, 0, 0), color_end=(0, 0, 0))
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


class SpawnMinionAttack(Attack):
    def __init__(self):
        Attack.__init__(self, "Minion Launcher")
        self.base_duration = 35
        self.base_delay = 12
        self.base_radius = 64
        self.base_damage = 0.6
        self.knockback = 0.25
        self.projectile_range = 300
        self.num_shots = 2
        self.dmg_color = (1, 0, 1)

    def activate(self, gs, entity, world, stat_lookup):
        res = Attack.activate(self, gs, entity, world, stat_lookup)
        pos = entity.center()
        radius = self.base_radius * (1 + 0.01 * stat_lookup.stat_value(StatType.ATTACK_RADIUS))
        circle = entities.AttackCircleArt(*pos, radius, 60, color=(1, 0, 1), color_end=(0.25, 0, 0.25))
        world.add(circle)

        if len(res) > 0:
            entities_in_range = world.entities_in_circle(pos, self.projectile_range)
            random.shuffle(entities_in_range)

            n = 0
            src_state = entity.get_actorstate(gs)
            for e in entities_in_range:
                if n >= self.num_shots:
                    break
                if entity.can_damage(e) and (e not in res) and (not world.get_hidden_at(*e.center())):
                    proj = entities.MinionProjectile(pos[0], pos[1], entity, e, 150, (1, 0, 1), src_state, self)
                    world.add(proj)
                    n += 1

        return res


GROUND_POUND = GroundPoundAttack()
MINION_LAUNCH_ATTACK = SpawnMinionAttack()
TOUCH_ATTACK = TouchAttack()


