

class GlobalState:

    def __init__(self):
        self.FLOOR_LAYER = 0
        self.SHADOW_LAYER = 5
        self.WALL_LAYER = 10
        self.ENTITY_LAYER = 15
        self.UI_0_LAYER = 20
        self.UI_1_LAYER = 25
    
        self.tick_counter = 0
        self.anim_tick = 0
        
    def update(self):
        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1
