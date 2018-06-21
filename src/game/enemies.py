import random
import src.game.spriteref as spriteref
from src.items.item import StatType
from src.world.entities import Enemy
from src.game.inventory import ActorState


class EnemyState(ActorState):
    def __init__(self, name, level, stats):
        """
            stats: map StatType -> value
        """
        self.stats = stats
        ActorState.__init__(self, name, 0, stats)
        
    def stat_value(self, stat_type):
        derived = self._compute_derived_stat(stat_type)
        if derived is not None:
            return derived
     
        elif stat_type in self.stats:
            return self.stats[stat_type]
        else:
            return 0
     
     
class EnemyFactory:

    def gen_enemy(level):
        i = int(random.random() * len(spriteref.enemies_all))
        stats = {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10
        }
        state = EnemyState("enem1", level, stats)
        
        return Enemy(0, 0, state, spriteref.enemies_all[i])

