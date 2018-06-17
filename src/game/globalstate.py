

class GlobalState:

    def __init__(self):
        self.FLOOR_LAYER = 0
        self.SHADOW_LAYER = 5
        self.WALL_LAYER = 10
        self.ENTITY_LAYER = 15
        self.UI_0_LAYER = 20
        self.UI_TOOLTIP_LAYER = 25
        
        self.screen_size = [800, 600]
        
        """Layers that follow the player"""
        self.world_layers = (self.FLOOR_LAYER, self.SHADOW_LAYER, 
                self.WALL_LAYER, self.ENTITY_LAYER)
    
        self.tick_counter = 0
        self.anim_tick = 0
        
        self._world_camera_center = [0, 0]
    
    def set_world_camera_center(self, x, y):
        self._world_camera_center = (x, y)
    
    def get_world_camera(self):
        offs_x = self._world_camera_center[0] - self.screen_size[0] // 2 
        offs_y = self._world_camera_center[1] - self.screen_size[1] // 2 
        return (offs_x, offs_y)
        
    def screen_to_world_coords(self, point):
        cam = self.get_world_camera()
        return (cam[0] + point[0], cam[1] + point[1])
        
    def update(self):
        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1
