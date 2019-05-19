
class Updateable:

    def update(self, world):
        pass


class Updater(Updateable):

    def __init__(self, update_lambda):
        self.update_lambda = update_lambda

    def update(self, world):
        self.update_lambda(world)