

_INSTANCE = None


class ItemGenConsts:

    def __init__(self):
        pass


class BalanceConsts:
    """All the constants that control difficulty / RNG in the game"""

    @staticmethod
    def create_instance(bal=None):
        if bal is not None:
            _INSTANCE = bal
        else:
            _INSTANCE = BalanceConsts()

    @staticmethod
    def get_instance():
        return _INSTANCE

    def __init__(self):
        self.itemgen = ItemGenConsts()
        self.enemygen = EnemyGenConsts()
