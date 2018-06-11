from OpenGL.GL import *
from OpenGL.GLU import *

import pygame

import spriteref
import world.entities as entities
import renderengine.img as img
from renderengine.engine import RenderEngine


SCREEN_SIZE = (800, 600)
   
    
def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode(SCREEN_SIZE, mods)
    
    render_eng = RenderEngine()
    render_eng.init(*SCREEN_SIZE)
    
    img_surface = pygame.image.load("src/image.png")
    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)
    
    img_model = spriteref.chest_open_1
    render_eng.add(img.ImageBundle(img_model, 200, 200, True, scale=4))
    
    clock = pygame.time.Clock()    
    
    running = True
    
    while running:
        render_eng.render_scene()
        pygame.display.flip()
        pygame.time.wait(100)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
                
if __name__ == "__main__":
    run()
    
