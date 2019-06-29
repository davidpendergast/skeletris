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
            item = ItemFactory.gen_item(level)
            if item is not None:
                loot.append(item)
        return loot
