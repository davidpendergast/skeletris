

class GlobalState:
    def __init__(self):
        self.tick_counter = 0
        self.anim_tick = 0
        
    def update(self):
        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1
