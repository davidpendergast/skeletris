
class Updateable:

    def update(self, world, input_state):
        pass


class Updater(Updateable):

    def __init__(self, update_lambda):
        self.update_lambda = update_lambda

    def update(self, world, input_state):
        self.update_lambda(world, input_state)