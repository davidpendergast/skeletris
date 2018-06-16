from src.renderengine.img import ImageBundle 
import src.game.spriteref as spriteref


class TextImage:
    def __init__(self, x, y, text, color=(1, 1, 1), scale=2):
        self.x = x
        self.y = y
        self.text = text.lower()
        self.color = color
        self.scale = scale
        self._letter_images = []
        self.kerning = 1
        
        self._build_images()
        
    def _build_images(self):
        if len(self._letter_images) < len(self.text):
            ypos = 0
            xpos = 0
            a_sprite = spriteref.alphabet["a"]
            for i in range(0, len(self.text)):
                c = self.text[i]
                if c == " ":
                    xpos += (self.kerning + a_sprite.width()) * self.scale
                elif c == "\n":
                    xpos = 0
                    ypos += (self.kerning + a_sprite.height()) * self.scale
                else:
                    sprite = spriteref.alphabet[c]
                    img = ImageBundle(sprite, self.x + xpos, self.y + ypos, 
                            absolute=False, scale=self.scale, color=self.color)
                    self._letter_images.append(img)  
                    xpos += (self.kerning + a_sprite.width()) * self.scale
                    
    def all_bundles(self):
        for b in self._letter_images:
            if b is not None:
                yield b
        

class ItemImage:
    def __init__(self, item, scale):
        self.item = item
        self.scale = scale
        self._cube_images = []

class ItemInfoPane:
    def __item__(self, item):
        self.item_image = ItemImage(item, 2)
        self.x = 0
        self.y = 0
        self.title_text
        self.lines_of_text
    
    

