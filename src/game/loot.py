import random

from src.items.item import ItemFactory


class LootFactory:

    @staticmethod
    def gen_chest_loot(level):
        """
            returns: list of items
        """
        loot = []
        for i in range(0, 3):
            if i == 0 or random.random() < 0.66:
                loot.append(ItemFactory.gen_item(level))
        return loot

    @staticmethod
    def gen_loot(level):
        """
            returns: list of items
        """
        loot = []
        for _ in range(0, 3):
            if random.random() < 0.05:
                loot.append(ItemFactory.gen_item(level))
        return loot

    @staticmethod
    def gen_num_potions_to_drop(level):
        rng = random.random()
        if rng < 0.125:
            return 2
        elif random.random() < 0.25:
            return 1
        else:
            return 0

    @staticmethod
    def should_drop_attack(level):
        if random.random() < 0.05:
            return True
        else:
            return False