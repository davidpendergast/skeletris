from OpenGL.GL import *
from OpenGL.GLU import *

import pygame

import spriteref

from world.worldstate import World
from world.entities import Player
import renderengine.img as img
from renderengine.engine import RenderEngine


SCREEN_SIZE = (800, 600)

def build_me_a_world(width, height):
    import random
    w = World(width, height)
    for x in range(0, width):
        for y in range(0, height):
            if random.random() < 0.33:
                w.set_geo(x, y, World.WALL)
            else:
                w.set_geo(x, y, World.FLOOR)
                
    return w
   
    
def run():
    pygame.init()
    mods = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode(SCREEN_SIZE, mods)
    
    render_eng = RenderEngine()
    render_eng.init(*SCREEN_SIZE)
    
    raw_sheet = pygame.image.load("src/image.png")
    img_surface = spriteref.build_spritesheet(raw_sheet)
    texture_data = pygame.image.tostring(img_surface, "RGBA", 1)
    width = img_surface.get_width()
    height = img_surface.get_height()
    render_eng.set_texture(texture_data, width, height)
    
    world = build_me_a_world(30, 20)
    
    for bun in world.get_all_bundles():
        render_eng.add(bun)
        #pass
        
    player = Player(32, 32)
    
    render_eng.add(player.get_updated_bundles()[0])
    
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
    
