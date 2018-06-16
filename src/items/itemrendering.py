from src.renderengine.img import ImageBundle 
import src.items.item as items
import src.game.spriteref as spriteref



class TextImage:
    def __init__(self, x, y, text, color=(1, 1, 1), scale=2, center_w=None):
        self.x = x
        self.center_w = center_w
        self.y = y
        self.text = text.lower()
        self.color = color
        self.scale = scale
        self._letter_images = []
        self.kerning = 1
        
        self._build_images()
        
    def _calc_width(self):
        max_line_w = 0
        cur_line_w = 0
        char_w = (spriteref.alphabet["a"].width() + self.kerning) * self.scale
        for c in self.text:
            if c == "\n":
                cur_line_w = 0
            else:
                cur_line_w += char_w
                max_line_w = max(max_line_w, cur_line_w)
        return max_line_w
        
    def line_height(self):
        return (spriteref.alphabet["a"].height() + self.kerning) * self.scale
        
    def _build_images(self):
        ypos = 0
        
        x_shift = 0
        if self.center_w is not None:
            true_width = self._calc_width()
            x_shift = self.x + self.center_w // 2 - true_width // 2     
            
        xpos = x_shift
            
        a_sprite = spriteref.alphabet["a"]
        for i in range(0, len(self.text)):
            c = self.text[i]
            if c == " ":
                xpos += (self.kerning + a_sprite.width()) * self.scale
            elif c == "\n":
                xpos = x_shift
                ypos += (self.kerning + a_sprite.height()) * self.scale
            else:
                sprite = spriteref.alphabet[c]
                img = ImageBundle(sprite, self.x + xpos, self.y + ypos, 
                        scale=self.scale, color=self.color)
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
    def __init__(self, item):
        self.item = item
        self.x = 0
        self.y = 0
        
        self.top_panel = None
        self.mid_panels = []
        self.bot_panel = None
        self.item_image = None
        self.title_text = None
        self.core_texts = []
        self.non_core_texts = []
        
        self._build_images()
        
        
    def _build_images(self):
        sc = 1
        self.top_panel = ImageBundle(spriteref.item_panel_top, 0, 0, scale=sc)
        h = self.top_panel.height()
        for i in range(0, len(self.item.non_core_stats())):
            img = ImageBundle(spriteref.item_panel_middle, 0, h, scale=sc)
            h += img.height()
            self.mid_panels.append(img)
        
        if len(self.mid_panels) > 0:
            bot_sprite = spriteref.item_panel_bottom_0
        else:
            bot_sprite = spriteref.item_panel_bottom_1
        self.bot_panel = ImageBundle(bot_sprite, 0, h, scale=sc)
        
        self.title_text = TextImage(16*sc, 12*sc, self.item.name, scale=2*sc)
        
        line_spacing = 3*sc
        
        h = 32*sc + line_spacing
        lvl_txt = TextImage((1 + 112)*sc, h, self.item.level_string(), scale=2*sc)
        self.core_texts.append(lvl_txt)
        h += lvl_txt.line_height()

        for stat in self.item.core_stats():
            h += line_spacing
            stat_txt = TextImage(112*sc, h, str(stat), color=stat.color(), scale=2*sc)
            self.core_texts.append(stat_txt)
            h += stat_txt.line_height()   
         
        h = 128*sc    
        for stat in self.item.non_core_stats():
            h += line_spacing
            stat_txt = TextImage(16*sc, h, str(stat), color=stat.color(), scale=2*sc)
            self.non_core_texts.append(stat_txt)
            h += stat_txt.line_height()         
                    
    def all_bundles(self):
        yield self.top_panel
        for bun in self.mid_panels:
            yield bun
        yield self.bot_panel
        for bun in self.title_text.all_bundles():
            yield bun
            
        for text in self.core_texts:
            for bun in text.all_bundles():
                yield bun
                
        for text in self.non_core_texts:
            for bun in text.all_bundles():
                yield bun
        
        
        
        
    
    

