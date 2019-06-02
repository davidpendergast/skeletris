import random

from src.items.item import ItemType, ItemTypes
from src.items.itemgen import ItemFactory, StatCubesItemFactory
from src.game.droprates import EnemyDroprate, ChestDroprate
import src.game.debug as debug


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
            if debug.ignore_level_restrictions_on_chest_drops():
                item_type_choices = ItemTypes.all_types()
            else:
                item_type_choices = ItemTypes.all_types(at_level=level)

            if len(item_type_choices) == 0:
                print("WARN: no valid item types to drop as loot at level: {}".format(level))
                return []
            else:
                item = ItemFactory.gen_item(level, random.choice(item_type_choices))
                if item is not None:
                    loot.append(item)
        return loot

    @staticmethod
    def gen_num_potions_to_drop(level):
        num = 0
        for i in range(EnemyDroprate.potion_chances(level)):
            if random.random() < EnemyDroprate.rate_per_potion(level):
                num += 1
        return num
