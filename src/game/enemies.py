import random
import src.game.spriteref as spriteref
from src.items.item import ItemFactory
from src.world.entities import Enemy, ItemEntity, PotionEntity
from src.game.actorstate import EnemyState
from src.game.stats import StatType


class LootFactory:

    @staticmethod
    def gen_loot(pos, player_lvl, dungeon_level):
        loot = []
        for _ in range(0, 3):
            if random.random() < 0.05:
                loot.append(ItemEntity(ItemFactory.gen_item(random.randint(0, 64)), *pos))
        return loot


class EnemyFactory:

    @staticmethod
    def gen_enemy(level):
        i = int(random.random() * len(spriteref.enemies_all))
        stats = {
            StatType.ATT: 10,
            StatType.DEF: 10,
            StatType.VIT: 10
        }
        state = EnemyState("enem1", spriteref.enemies_all[i], level, stats)
        
        return Enemy(0, 0, state)

    @staticmethod
    def gen_enemies(level, n=None):
        if n is None:
            n = int(1 + random.random()*4)

        first = EnemyFactory.gen_enemy(level)
        res = [first]
        for _ in range(1, n):
            res.append(Enemy(0, 0, first.state.duplicate()))

        return res

