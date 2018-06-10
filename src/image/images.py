
class ImageModel:
    def __init__(x, y, w, h, sheet_size=(480, 240)):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        
        self.tx1 = self.x1 / sheet_size[0]
        self.ty1 = self.y1 / sheet_size[1]
        self.tx2 = self.x2 / sheet_size[0]
        self.ty2 = self.y2 / sheet_size[1]
        
    def size(self):
        return (self.x2 - self.x1, self.y2 - self.y1)
        
    def draw_instant(self, x_offs, y_offs):
        pass
        
player_idle_0 = ImageModel(0, 0, 16, 32)
player_idle_1 = ImageModel(16, 0, 16, 32)

player_move_0 = ImageModel(32, 0, 16, 32)
player_move_1 = ImageModel(48, 0, 16, 32)
player_move_2 = ImageModel(64, 0, 16, 32)
player_move_3 = ImageModel(80, 0, 16, 32)

chest = ImageModel(0, 32, 16, 16)
chest_open_1 = ImageModel(16, 32, 16, 16)
chest_open_2 = ImageModel(32, 32, 16, 16)


