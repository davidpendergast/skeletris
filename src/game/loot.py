import random

from src.items.item import ItemFactory, ItemType, ItemTypes
from src.game.droprates import EnemyDroprate, ChestDroprate


class LootFactory:

    @staticmethod
    def gen_chest_loot(level):
        """
            returns: list of items
        """
        n_items = ChestDroprate.guaranteed_items(level)

        for _ in range(0, ChestDroprate.item_chances(level)):
            if random.random() < ChestDroprate.rate_per_item(level):
                n_items += 1

        loot = []
        while len(loot) < n_items:
            item_type = random.choice([e for e in ItemTypes.all_types()])
            item = ItemFactory.gen_item(level, item_type)
            if item is not None:
                loot.append(item)
        return loot

    @staticmethod
    def gen_loot(level, is_rare):
        """
            returns: list of items
        """
        n_items = EnemyDroprate.guaranteed_items(level, is_rare)
        for _ in range(0, EnemyDroprate.item_chances(level, is_rare)):
            if random.random() < EnemyDroprate.rate_per_item(level, is_rare):
                n_items += 1

        loot = []
        for _ in range(0, n_items):
            loot.append(StatCubesItemFactory.gen_item(level))
        return loot

    @staticmethod
    def gen_num_potions_to_drop(level, is_rare):
        num = 0
        for i in range(EnemyDroprate.potion_chances(level, is_rare)):
            if random.random() < EnemyDroprate.rate_per_potion(level, is_rare):
                num += 1
        return num
