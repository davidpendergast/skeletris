from src.utils.util import Utils


class EnemyDroprate:

    @staticmethod
    def item_chances(level):
        return 2 + int(level / 10)

    @staticmethod
    def rate_per_item(level):
        return 0.05

    @staticmethod
    def guaranteed_items(level):
        return 0

    @staticmethod
    def potion_chances(level):
        return 1

    @staticmethod
    def rate_per_potion(level):
        return 0.1


class ChestDroprate:

    @staticmethod
    def item_chances(level):
        return 3

    @staticmethod
    def rate_per_item(level):
        return 0.333

    @staticmethod
    def guaranteed_items(level):
        return 0


class ItemRates:
    pass


class EnemyRates:

    @staticmethod
    def chance_to_be_rare(level):
        if level < 5:
            return 0
        else:
            return 0.333 * Utils.bound(level / 65, 0.0, 1.0)

    @staticmethod
    def max_pack_size(level):
        return 5 + 10 * Utils.bound(level / 20, 0.0, 1.0)

    @staticmethod
    def min_pack_size(level):
        return 0 + 5 * Utils.bound(level / 20, 0.0, 1.0)

