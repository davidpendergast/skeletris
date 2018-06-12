from OpenGL.GL import *
from OpenGL.GLU import *


class RenderEngine:
    def __init__(self):
        self.image_bundles = {} # (int) id -> bundle
        self.camera_pos = [0, 0]

    def resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 1, -1);
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();


    def init(self, w, h):
        self.resize(w, h)
        # glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)
        glClearColor(1.0, 0.0, 0.0, 0.0);
        #glClearColor(1.0, 0.65, 1.0, 0.2)


    def set_texture(self, img_data, width, height):
        """
            img_data: image data in string RGBA format.
        """
        bgImgGL = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, bgImgGL)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glEnable(GL_TEXTURE_2D)    
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        
    def set_camera_pos(self, x, y):
        self.camera_pos[0] = x
        self.camera_pos[1] = y
        
    def add(self, img_bundle):
        uid = img_bundle.uid()
        if uid in self.image_bundles:
            raise ValueError("Image bundle is already in engine: uid=" + str(uid))
        self.image_bundles[img_bundle.uid()] = img_bundle
        
    def remove(self, img_bundle):
        uid = img_bundle.uid()
        if uid in self.image_bundles:
            del self.image_bundles[img_bundle.uid()]
        
    def update(self, img_bundle):
        self.remove(img_bundle)
        self.add(img_bundle)
        
    def __contains__(self, key):
        try:
            return key.uid() in self.image_bundles
        except ValueError:
            return False
        
    def render_scene(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        to_draw = list(self.image_bundles.values())
        to_draw.sort(key=lambda x: -x.depth())
        
        for bundle in to_draw:
            x_pos = bundle.x() - (0 if bundle.absolute() else self.camera_pos[0])
            y_pos = bundle.y() - (0 if bundle.absolute() else self.camera_pos[1])
            bundle.model().draw_instant(x_pos, y_pos, scale=bundle.scale())
    
