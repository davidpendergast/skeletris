import random

from src.items.item import ItemType, ItemTypes
from src.items.itemgen import ItemFactory
import src.game.debug as debug
import src.game.balance as balance


class LootFactory:

    @staticmethod
    def gen_chest_loot(level):
        """
            returns: list of items
        """
        n_items = balance.CHEST_MIN_NUM_ITEMS

        for _ in range(0, (balance.CHEST_MAX_NUM_ITEMS - n_items)):
            if random.random() < balance.CHEST_DROP_RATE:
                n_items += 1

        loot = []
        while len(loot) < n_items:
            if debug.ignore_loot_levels():
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
