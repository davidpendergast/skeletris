import random

from src.items.item import ItemFactory
from src.game.droprates import EnemyDroprate, ChestDroprate


class LootFactory:

    @staticmethod
    def gen_chest_loot(level):
        """
            returns: list of items
        """
        loot = []
        for i in range(0, ChestDroprate.ITEM_CHANCES):
            if i == 0 or random.random() < ChestDroprate.RATE_PER_ITEM:
                loot.append(ItemFactory.gen_item(level))
        return loot

    @staticmethod
    def gen_loot(level, potential_attack=None):
        """
            returns: list of items
        """
        loot = []
        for _ in range(0, EnemyDroprate.ITEM_CHANCES):
            if random.random() < EnemyDroprate.RATE_PER_ITEM:
                loot.append(ItemFactory.gen_item(level))

        if potential_attack is not None:
            for _ in range(0, EnemyDroprate.ATT_ITEM_CHANCES):
                if random.random() < EnemyDroprate.RATE_PER_ATT_ITEM:
                    loot.append(ItemFactory.gen_item(level, attack=potential_attack))

        return loot

    @staticmethod
    def gen_num_potions_to_drop(level):
        num = 0
        for i in range(EnemyDroprate.POTION_CHANCES):
            if random.random() < EnemyDroprate.RATE_PER_POTION:
                num += 1
        return num
        rng = random.random()
