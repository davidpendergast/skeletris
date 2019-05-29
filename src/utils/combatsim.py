import random
from src.utils.util import Utils

ATTACK_RANGE = [1, 2, 3, 4, 5, 6]
DEFEND_RANGE = [1, 2, 3, 4, 5, 6]


class _Combatant:

    def __init__(self, name, ATT, DEF, HP, SPEED):
        self.name = name
        self.ATT = ATT
        self.DEF = DEF
        self.HP = HP
        self.SPEED = SPEED

        self.energy = 0
        self.max_energy = 8

    def copy(self):
        return _Combatant(self.name, self.ATT, self.DEF, self.HP, self.SPEED)


class _Fight:

    def __init__(self, player, fight_seq=None):
        self.player = player

        # a sequence of group-fights for player
        # a list of lists of combatants
        self.fight_seq = []

        if fight_seq is not None:
            for f in Utils.listify(fight_seq):
                self.add(f)

    def add(self, enemy_group):
        self.fight_seq.append(Utils.listify(enemy_group))
        return self

    def copy(self):
        res = _Fight(self.player.copy(), None)
        for group in self.fight_seq:
            new_group = [c.copy() for c in group]
            res.add(new_group)
        return res

    def active_enemies(self):
        for enemy_group in self.fight_seq:
            alive = [e for e in enemy_group if e.HP > 0]
            if len(alive) > 0:
                return alive
        return []

    def all_enemies(self, alive_only=False):
        for enemy_group in self.fight_seq:
            for e in enemy_group:
                if not alive_only or e.HP > 0:
                    yield e


def do_attack(attacker, defender, turn_num, silent=False):
    atts = [random.choice(ATTACK_RANGE) for _ in range(0, attacker.ATT)]
    defs = [random.choice(DEFEND_RANGE) for _ in range(0, defender.DEF)]
    atts.sort(reverse=True)

    for d in defs:
        for i in range(0, len(atts)):
            if atts[i] <= d:
                atts.pop(i)
                break

    att_value = len(atts)
    defender.HP -= att_value
    if not silent:
        print("{}: {} dealt {} damage to {}, bringing it's health to {}".format(
              turn_num, attacker.name, att_value, defender.name, defender.HP))


def do_fight(fight, silent=False):
    i = 0
    player = fight.player
    while True:
        active_enemies = fight.active_enemies()
        if len(active_enemies) == 0:
            return i

        player.energy += player.SPEED
        if player.energy >= player.max_energy:
            to_attack = active_enemies[0]
            player.energy = player.energy % player.max_energy
            do_attack(player, to_attack, i, silent=silent)

        for enemy in active_enemies:
            enemy.energy += enemy.SPEED
            if enemy.energy >= enemy.max_energy:
                enemy.energy = enemy.energy % enemy.max_energy
                do_attack(enemy, player, i, silent=silent)

        i += 1


def do_many_fights(fight, n):
    # stats for when player wins
    player_wins = 0
    player_hp_total = 0

    # stats for when enemies win
    enemies_remaining_total = 0
    enemy_hp_total = 0

    for _ in range(0, n):
        fight_copy = fight.copy()
        do_fight(fight_copy, silent=True)
        if fight_copy.player.HP > 0:
            player_wins += 1
            player_hp_total += fight_copy.player.HP
        else:
            for alive_enemy in fight_copy.all_enemies(alive_only=True):
                enemies_remaining_total += 1
                enemy_hp_total += alive_enemy.HP

    pcnt_player_win = player_wins / n
    avg_player_hp = 0 if player_wins == 0 else player_hp_total / player_wins
    avg_enemy_hp = 0 if player_wins == n else enemy_hp_total / (n - player_wins)
    avg_enemies_remaining = 0 if player_wins == n else enemies_remaining_total / (n - player_wins)

    print("Results of {} fights:".format(n))
    print("  Player won {:.1f}% of fights with an average {:.1f} HP remaining.".format(
        pcnt_player_win*100, avg_player_hp
    ))
    print("  Enemies won {:.1f}% of fights with an average of {} remaining and {:.1f} total HP remaining.\n".format(
        (1-pcnt_player_win)*100, avg_enemies_remaining, avg_enemy_hp
    ))

    return pcnt_player_win


BASE_PLAYER = _Combatant("Player", 3, 1, 20, 4)
ENEMY_1 = _Combatant("Enemy", 2, 2, 6, 2)

if __name__ == "__main__":

    fight = _Fight(BASE_PLAYER.copy(), fight_seq=[[ENEMY_1.copy(), ENEMY_1.copy(), ENEMY_1.copy()]])

    do_many_fights(fight, 100)
