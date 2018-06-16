from OpenGL.GL import *
from OpenGL.GLU import *

import random

UNIQUE_ID_CTR = 0
def gen_unique_id():
    """Note: this ain't threadsafe"""
    global UNIQUE_ID_CTR
    UNIQUE_ID_CTR += 1
    return UNIQUE_ID_CTR - 1
    

class ImageBundle:

    def __init__(self, model, x, y, scale=1, depth=1, xflip=False, color=(1, 1, 1), uid=None):
        self._unique_id = gen_unique_id() if uid is None else uid
        self._model = model
        self._x = x
        self._y = y
        self._scale = scale
        self._depth = depth
        self._xflip = xflip
        self._color = color
            
    def update(self, new_model=None, new_x=None, new_y=None, 
                new_scale=None, new_depth=None,
                new_xflip=None, new_color=None):
                
        model = self.model() if new_model is None else new_model
        x = self.x() if new_x is None else new_x
        y = self.y() if new_y is None else new_y
        scale = self.scale() if new_scale is None else new_scale
        depth = self.depth() if new_depth is None else new_depth
        xflip = self.xflip() if new_xflip is None else new_xflip
        color = self.color() if new_color is None else new_color
        
        if (model == self.model() and 
                x == self.x() and 
                y == self.y() and
                scale == self.scale() and
                depth == self.depth() and 
                xflip == self.xflip() and
                color == self.color()):
            return self
        else:
            return ImageBundle(model, x, y, scale=scale, 
                    depth=depth, xflip=xflip, color=color, uid=self.uid())
        
    def model(self):
        return self._model
    
    def x(self):
        return self._x
        
    def y(self):
        return self._y
        
    def width(self):
        return self.model().width() * self.scale()
        
    def height(self):
        return self.model().height() * self.scale()
        
    def scale(self):
        return self._scale
        
    def depth(self):
        return self._depth
        
    def xflip(self):
        return self._xflip
        
    def color(self):
        return self._color
        
    def uid(self):
        return self._unique_id
        
    def add_urself(self, vertices, texts, colors, indices):
        x = self.x()
        y = self.y()
        model = self.model()
        w = model.w * self.scale()
        h = model.h * self.scale()
        color = self.color()
        
        vertices.extend([
                x, y,
                x, y + h,
                x + w, y + h,
                x + w, y])
        
        if colors is not None:            
            colors.extend([
                    color, color, color, color   
            ])
        
        tx1 = model.tx1 if not self.xflip() else model.tx2
        tx2 = model.tx2 if not self.xflip() else model.tx1
        
        texts.extend([
                tx1, model.ty2,
                tx1, model.ty1,
                tx2, model.ty1,
                tx2, model.ty2])
        
        i = 0 if len(indices) == 0 else indices[-1] + 1
        indices.extend([i, i+1, i+2, i, i+2, i+3])


class ImageModel:

    def __init__(self, x, y, w, h):
        # sheet coords, origin top left corner
        self.x = x  
        self.y = y
        self.w = w
        self.h = h
        
        # texture coords, origin bottom left corner
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
        
        self.tx1 = 0
        self.ty1 = 0
        self.tx2 = 0
        self.ty2 = 0
        
    def size(self):
        return (self.w, self.h)
        
    def width(self):
        return self.w
        
    def height(self):
        return self.h
        
    def set_sheet_size(self, size):
        self.x1 = self.x
        self.x2 = self.x + self.w
        self.y1 = size[1] - (self.y + self.h)
        self.y2 = size[1] - self.y
        
        self.tx1 = self.x1 / size[0]
        self.ty1 = self.y1 / size[1]
        self.tx2 = self.x2 / size[0]
        self.ty2 = self.y2 / size[1]
        
    def __repr__(self):
        return "ImageModel({}, {}, {}, {})".format(self.x, self.y, self.w, self.h)
        
    def draw_instant(self, x_pos, y_pos, scale=1):
        glBegin(GL_QUADS)
    
        glTexCoord2f(self.tx1, self.ty2)
        glVertex2i(x_pos, y_pos)
        
        glTexCoord2f(self.tx1, self.ty1)
        glVertex2i(x_pos, y_pos + int(scale * self.h))
        
        glTexCoord2f(self.tx2, self.ty1)
        glVertex2i(x_pos + int(scale * self.w), y_pos + int(scale * self.h))
        
        glTexCoord2f(self.tx2, self.ty2)
        glVertex2i(x_pos + int(scale * self.w), y_pos)
        
        glEnd() 
        
    def draw_instant_tri(self, x_pos, y_pos, scale=1):
        vertices = [x_pos, y_pos,
                    x_pos, y_pos + scale * self.h,
                    x_pos + scale * self.w, y_pos + scale * self.h,
                    x_pos + scale * self.w, y_pos]
        
        text_crd = [self.tx1, self.ty2,
                    self.tx1, self.ty1,
                    self.tx2, self.ty1,
                    self.tx2, self.ty2]
                    
        indices = [0, 1, 2, 0, 2, 3]
        
        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_TEXTURE_COORD_ARRAY);
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glTexCoordPointer(2, GL_FLOAT, 0, text_crd)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY);
        
        


