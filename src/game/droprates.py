from src.utils.util import Utils


class EnemyDroprate:

    ITEM_CHANCES = 2
    RATE_PER_ITEM = 0.05

    ATT_ITEM_CHANCES = 1
    RATE_PER_ATT_ITEM = 0.15

    POTION_CHANCES = 2
    RATE_PER_POTION = 0.1


class ChestDroprate:

    ITEM_CHANCES = 3
    RATE_PER_ITEM = 0.333


class ItemRates:
    pass


class EnemyRates:

    @staticmethod
    def chance_to_have_attack(level):
        if level < 5:
            return 0
        else:
            return 0.75 * Utils.bound(level / 65, 0.0, 1.0)

    @staticmethod
    def max_pack_size(level):
        return 5 + 10 * Utils.bound(level / 20, 0.0, 1.0)

    @staticmethod
    def min_pack_size(level):
        return 0 + 5 * Utils.bound(level / 20, 0.0, 1.0)

