import src.game.spriteref as spriteref

class GlobalState:

    def __init__(self):
        self.screen_size = [800, 600]
    
        self.tick_counter = 0
        self.anim_tick = 0
        
        self._world_camera_center = [0, 0]
        self._player_state = None
        
    def set_player_state(self, state):
        self._player_state = state
        
    def player_state(self):
        return self._player_state
    
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
            
            
        
