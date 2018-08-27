from src.ui.menus import MenuManager
from src.game.npc import NpcState
from src.game.dialog import DialogManager


DEBUG_MODE = True


class GlobalState:

    def __init__(self, menu_id=MenuManager.START_MENU):
        self.screen_size = [800, 600]
        self.is_fullscreen = False
    
        self.tick_counter = 0
        self.anim_tick = 0

        self.dungeon_level = 0
        self.kill_count = 0
        
        self._world_camera_center = [0, 0]
        self._player_state = None

        self._needs_new_game = False

        self._needs_next_level = False
        self._needs_next_level_countdown = 0

        self._menu_manager = MenuManager(menu_id)

        self._npc_state = NpcState()
        self._dialog_manager = DialogManager()

        self._cinematics_queue = []

        self.needs_exit = False

    def get_menu_manager(self):
        return self._menu_manager

    def world_updates_paused(self):
        return self.dialog_manager().is_active()

    def dialog_manager(self):
        return self._dialog_manager

    def npc_state(self):
        return self._npc_state
        
    def set_player_state(self, state):
        self._player_state = state

    def get_cinematics_queue(self):
        return self._cinematics_queue
        
    def player_state(self):
        return self._player_state
    
    def set_world_camera_center(self, x, y):
        self._world_camera_center = (x, y)
    
    def get_world_camera(self, center=False):
        if center:
            return tuple(self._world_camera_center)
        else:
            offs_x = self._world_camera_center[0] - self.screen_size[0] // 2
            offs_y = self._world_camera_center[1] - self.screen_size[1] // 2
            return (offs_x, offs_y)

    def get_world_camera_size(self):
        return self.screen_size
        
    def screen_to_world_coords(self, point):
        cam = self.get_world_camera()
        return (cam[0] + point[0], cam[1] + point[1])
        
    def update(self):
        self.tick_counter += 1
        if self.tick_counter % 8 == 0:
            self.anim_tick += 1

        if self._needs_next_level_countdown > 0:
            self._needs_next_level_countdown -= 1
            if self._needs_next_level_countdown <= 0:
                self.next_level()

    def player_died(self):
        self.get_menu_manager().set_active_menu(MenuManager.DEATH_MENU)

    def new_game(self):
        self._needs_new_game = True

    def trigger_next_level_seq(self, pause_for=60):
        if self._needs_next_level_countdown <= 0:
            print("triggered next level")
            self._needs_next_level_countdown = pause_for

    def next_level(self):
        self.dungeon_level = min(self.dungeon_level + 10, 64)
        self._needs_next_level_countdown = 0
        self._needs_next_level = True

