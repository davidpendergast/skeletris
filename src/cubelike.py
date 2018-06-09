from OpenGL.GL import *
from OpenGL.GLU import *

import pygame

SCREEN_SIZE = (800, 600)
TEXTURE_SIZE = None

def resize(width, height):
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, 0, width, height)
    # glOrtho(0.0, width, height, 0.0, 0.0, 1.0); 
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glOrtho(0, width, 0, height, 1, -1);


def init():
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_FLAT)
    glClearColor(1.0, 0.65, 1.0, 0.2)
    
    
def loadScene():
    img = pygame.image.load("image.png")
    textureData = pygame.image.tostring(img, "RGBA", 1)
    width = img.get_width()
    height = img.get_height()
    global TEXTURE_SIZE
    TEXTURE_SIZE = (width, height)
    bgImgGL = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, bgImgGL)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)
    glEnable(GL_TEXTURE_2D)    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    
def placeScene():
    glLoadIdentity()
    glTranslatef(0, 0, 0)
    
    glBegin(GL_QUADS)
    
    w = 2 * TEXTURE_SIZE[0] / SCREEN_SIZE[0]
    h = 2 * TEXTURE_SIZE[1] / SCREEN_SIZE[1]
    glTexCoord2f(0,0)
    glVertex2f(-1,-1)
    
    glTexCoord2f(0,1)
    glVertex2f(-1, -1 + h)
    
    glTexCoord2f(1,1)
    glVertex2f(-1 + w,-1 + h)
    
    glTexCoord2f(1,0)
    glVertex2f(-1 + w,-1)
    glEnd()    
    
    
def run():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.HWSURFACE|pygame.OPENGL|pygame.DOUBLEBUF)
    
    resize(*SCREEN_SIZE)
    init()
    
    loadScene()
    
    clock = pygame.time.Clock()    
    
    running = True
    
    while running:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        placeScene()
        pygame.display.flip()
        pygame.time.wait(100)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
                
if __name__ == "__main__":
    run()
    
