import random

from src.items.item import ItemType, ItemTypes
from src.items.itemgen import ItemFactory, StatCubesItemFactory
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
            item_type_choices = ItemTypes.all_types(level)
            if len(item_type_choices) == 0:
                print("WARN: no valid item types to drop as loot at level: {}".format(level))
                return []
            else:
                item = ItemFactory.gen_item(level, random.choice(item_type_choices))
                if item is not None:
                    loot.append(item)
        return loot

    @staticmethod
    def gen_loot(level):
        """
            returns: list of items
        """
        n_items = EnemyDroprate.guaranteed_items(level)
        for _ in range(0, EnemyDroprate.item_chances(level)):
            if random.random() < EnemyDroprate.rate_per_item(level):
                n_items += 1

        loot = []
        for _ in range(0, n_items):
            loot.append(StatCubesItemFactory.gen_item(level))
        return loot

    @staticmethod
    def gen_num_potions_to_drop(level):
        num = 0
        for i in range(EnemyDroprate.potion_chances(level)):
            if random.random() < EnemyDroprate.rate_per_potion(level):
                num += 1
        return num
