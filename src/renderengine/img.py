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

    @staticmethod
    def new_bundle(layer_id, scale=1, depth=0):
        return ImageBundle(None, 0, 0, layer=layer_id, scale=scale, depth=depth)

    def __init__(self, model, x, y, layer=0, scale=1, depth=1, xflip=False, rotation=0, color=(1, 1, 1), ratio=(1, 1), uid=None):
        self._unique_id = gen_unique_id() if uid is None else uid
        self._model = model
        self._x = x
        self._y = y
        self._layer = layer  # Note: can't be changed once set
        self._scale = scale
        self._depth = depth
        self._xflip = xflip
        self._rotation = rotation
        self._color = color
        self._ratio = ratio

        self._is_destroyed = False
            
    def update(self, new_model=None, new_x=None, new_y=None, new_scale=None, new_depth=None,
               new_xflip=None, new_color=None, new_rotation=None, new_ratio=None):
                
        model = self.model() if new_model is None else new_model
        x = self.x() if new_x is None else new_x
        y = self.y() if new_y is None else new_y
        scale = self.scale() if new_scale is None else new_scale
        depth = self.depth() if new_depth is None else new_depth
        xflip = self.xflip() if new_xflip is None else new_xflip
        color = self.color() if new_color is None else new_color
        rotation = self.rotation() if new_rotation is None else new_rotation
        ratio = self.ratio() if new_ratio is None else new_ratio
        
        if (model == self.model() and 
                x == self.x() and 
                y == self.y() and
                scale == self.scale() and
                depth == self.depth() and 
                xflip == self.xflip() and
                color == self.color() and
                ratio == self.ratio() and
                rotation == self.rotation()):
            return self
        else:
            res = ImageBundle(model, x, y, scale=scale, depth=depth, xflip=xflip, rotation=rotation,
                              layer=self.layer(), color=color, ratio=ratio, uid=self.uid())
            res._is_destroyed = self._is_destroyed
            return res
        
    def model(self):
        return self._model
    
    def x(self):
        return self._x
        
    def y(self):
        return self._y
        
    def width(self):
        if self.model() is None:
            return 0
        elif self.rotation() % 2 == 0:
            return self.model().width() * self.scale() * self.ratio()[0]
        else:
            return self.model().height() * self.scale() * self.ratio()[1]
        
    def height(self):
        if self.model() is None:
            return 0
        elif self.rotation() % 2 == 0:
            return self.model().height() * self.scale() * self.ratio()[1]
        else:
            return self.model().width() * self.scale() * self.ratio()[0]

    def size(self):
        return (self.width(), self.height())

    def scale(self):
        return self._scale
        
    def depth(self):
        return self._depth

    def layer(self):
        return self._layer
        
    def xflip(self):
        return self._xflip

    def rotation(self):
        """returns: int: 0, 1, 2, or 3 representing a number of clockwise 90 degree rotations."""
        return self._rotation
        
    def color(self):
        return self._color

    def ratio(self):
        return self._ratio
        
    def uid(self):
        return self._unique_id

    def all_bundles(self):
        yield self

    def mark_for_removal(self):
        self._is_destroyed = True

    def is_destroyed(self):
        return self._is_destroyed
        
    def add_urself(self, i, vertices, texts, colors, indices):
        """
            i: sprite's "index", which determines where in the arrays its data is written.
        """
        x = self.x()
        y = self.y()

        model = self.model()
        if model is None:
            w = 0
            h = 0
        else:
            w = model.w * self.scale() * self.ratio()[0]
            h = model.h * self.scale() * self.ratio()[1]

        if self.rotation() == 1 or self._rotation == 3:
            temp_w = w
            w = h
            h = temp_w

        vertices[i*8 + 0] = x
        vertices[i*8 + 1] = y
        vertices[i*8 + 2] = x
        vertices[i*8 + 3] = y + h
        vertices[i*8 + 4] = x + w
        vertices[i*8 + 5] = y + h
        vertices[i*8 + 6] = x + w
        vertices[i*8 + 7] = y

        if colors is not None:
            rgb = self.color()
            for j in range(0, 12):
                colors[i * 12 + j] = rgb[j % 3]

        if model is not None:
            corners = [
                model.tx1, model.ty2,
                model.tx1, model.ty1,
                model.tx2, model.ty1,
                model.tx2, model.ty2
            ]

            if self.xflip():
                corners[0] = model.tx2
                corners[2] = model.tx2
                corners[4] = model.tx1
                corners[6] = model.tx1

            for _ in range(0, self.rotation()):
                corners = corners[2:] + corners[:2]

            for j in range(0, 8):
                texts[i * 8 + j] = corners[j]

        indices[6 * i + 0] = 4 * i
        indices[6 * i + 1] = 4 * i + 1
        indices[6 * i + 2] = 4 * i + 2
        indices[6 * i + 3] = 4 * i
        indices[6 * i + 4] = 4 * i + 2
        indices[6 * i + 5] = 4 * i + 3

    def __repr__(self):
        return "ImageBundle({}, {}, {}, {}, {}, {}, {}, {}, {}. {})".format(
                self.model(), self.x(), self.y(), self.layer(),
                self.scale(), self.depth(), self.xflip(), self.color(), self.ratio(), self.uid())


class ImageModel:

    def __init__(self, x, y, w, h):
        # sheet coords, origin top left corner
        self.x = x  
        self.y = y
        self.w = w
        self.h = h
        self._rect = (x, y, w, h)
        
        # texture coords, origin bottom left corner
        self.tx1 = 0
        self.ty1 = 0
        self.tx2 = 0
        self.ty2 = 0
        
    def rect(self):
        return self._rect
        
    def size(self):
        return (self.w, self.h)
        
    def width(self):
        return self.w
        
    def height(self):
        return self.h
        
    def set_sheet_size(self, size):
        self.tx1 = self.x
        self.tx2 = self.x + self.w
        self.ty1 = size[1] - (self.y + self.h)
        self.ty2 = size[1] - self.y
        
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
        
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glTexCoordPointer(2, GL_FLOAT, 0, text_crd)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        
        


