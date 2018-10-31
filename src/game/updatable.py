
class Updateable:

    def update(self, world, gs, input_state, render_engine):
        pass


class Updater(Updateable):

    def __init__(self, update_lambda):
        self.update_lambda = update_lambda

    def update(self, world, gs, input_state, render_engine):
        self.update_lambda(world, gs, input_state, render_engine)