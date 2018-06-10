from OpenGL.GL import *
from OpenGL.GLU import *

UNIQUE_ID_CTR = 0
def gen_unique_id():
    """Note: this ain't threadsafe"""
    global UNIQUE_ID_CTR
    UNIQUE_ID_CTR += 1
    return UNIQUE_ID_CTR - 1
    

class ImageBundle:
    def __init__(self, model, x, y, absolute=True, scale=1, depth=1, uid=None):
        self._unique_id = gen_unique_id() if uid is None else uid
        self._model = model
        self._x = x
        self._y = y
        self._absolute = absolute
        self._scale = scale
        self._depth = depth
        
    def update(self, new_model=None, new_x=None, new_y=None, 
                new_absolute=None, new_scale=None, new_depth=None):
        
        model = self.model() if new_model is None else new_model
        x = self.x() if new_x is None else new_x
        y = self.y() if new_y is None else new_y
        absolute = self.absolute() if new_absolute is None else new_absolute
        scale = self.scale() if new_scale is None else new_scale
        depth = self.depth() if new_depth is None else new_depth
        
        return ImageBundle(model, x, y, absolute=absolute, scale=scale, depth=depth, uid=self.unique_id)
        
    def model(self):
        return self._model
    
    def x(self):
        return self._x
        
    def y(self):
        return self._y
        
    def absolute(self):
        return self._absolute
        
    def scale(self):
        return self._scale
        
    def depth(self):
        return self._depth
        
    def uid(self):
        return self._unique_id

class ImageModel:
    def __init__(self, x, y, w, h, sheet_size=(480, 240)):
        self.x1 = x
        self.y1 = sheet_size[1] - (y + h)
        self.x2 = x + w
        self.y2 = sheet_size[1] - y
        self.w = w
        self.h = h
        
        self.tx1 = self.x1 / sheet_size[0]
        self.ty1 = self.y1 / sheet_size[1]
        self.tx2 = self.x2 / sheet_size[0]
        self.ty2 = self.y2 / sheet_size[1]
        
    def size(self):
        return (self.x2 - self.x1, self.y2 - self.y1)
        
    def draw_instant(self, x_pos, y_pos, scale=1):
        glBegin(GL_QUADS)
    
        glTexCoord2f(self.tx1, self.ty2)
        glVertex2i(x_pos, y_pos)
        
        glTexCoord2f(self.tx1, self.ty1)
        glVertex2i(x_pos, y_pos + scale * self.w)
        
        glTexCoord2f(self.tx2, self.ty1)
        glVertex2i(x_pos + scale * self.w, y_pos + scale * self.h)
        
        glTexCoord2f(self.tx2, self.ty2)
        glVertex2i(x_pos + scale * self.w, y_pos)
        glEnd() 
        
        
player_idle_0 = ImageModel(0, 0, 16, 32)
player_idle_1 = ImageModel(16, 0, 16, 32)

player_move_0 = ImageModel(32, 0, 16, 32)
player_move_1 = ImageModel(48, 0, 16, 32)
player_move_2 = ImageModel(64, 0, 16, 32)
player_move_3 = ImageModel(80, 0, 16, 32)
player_move_all = [player_move_0, player_move_1, player_move_2, player_move_3]

chest = ImageModel(0, 32, 16, 16)
chest_open_1 = ImageModel(16, 32, 16, 16)
chest_open_2 = ImageModel(32, 32, 16, 16)


