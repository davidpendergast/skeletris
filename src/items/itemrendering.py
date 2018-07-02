from src.renderengine.img import ImageBundle 
import src.items.item as items
import src.game.spriteref as spriteref


class TextImage:
    def __init__(self, x, y, text, layer, color=(1, 1, 1), scale=2, center_w=None):
        self.x = x
        self.center_w = center_w
        self.y = y
        self.text = text.lower()
        self.layer = layer
        self.color = color
        self.scale = scale
        self._letter_images = []
        self.x_kerning = 1
        self.y_kerning = 1

        self._build_images()

        self.actual_size = self._recalc_size()

    def _recalc_size(self):
        x_range = [None, None]
        y_range = [None, None]
        for img in self.all_bundles():
            x_range[0] = img.x() if x_range[0] is None else min(x_range[0], img.x())
            x_range[1] = img.x() + img.width() if x_range[1] is None else max(x_range[0], img.x() + img.width())
            y_range[0] = img.y() if y_range[0] is None else min(y_range[0], img.y())
            y_range[1] = img.y() + img.height() if y_range[1] is None else max(y_range[1], img.y() + img.height())
        return (x_range[1] - x_range[0], y_range[1] - y_range[0])

    def _calc_width(self):
        max_line_w = 0
        cur_line_w = 0
        char_w = (spriteref.alphabet["a"].width() + self.x_kerning) * self.scale
        for c in self.text:
            if c == "\n":
                cur_line_w = 0
            else:
                cur_line_w += char_w
                max_line_w = max(max_line_w, cur_line_w)
        return max_line_w

    def size(self):
        return self.actual_size
        
    def line_height(self):
        return (spriteref.alphabet["a"].height() + self.y_kerning) * self.scale
        
    def _build_images(self):
        ypos = self.y_kerning

        if self.center_w is not None:
            true_width = self._calc_width()
            x_shift = self.x + self.center_w // 2 - true_width // 2     
        else:
            x_shift = self.x_kerning
            
        xpos = x_shift
            
        a_sprite = spriteref.alphabet["a"]
        for i in range(0, len(self.text)):
            c = self.text[i]
            if c == " ":
                xpos += (self.x_kerning + a_sprite.width()) * self.scale
            elif c == "\n":
                xpos = x_shift
                ypos += (self.y_kerning + a_sprite.height()) * self.scale
            else:
                sprite = spriteref.alphabet[c]
                img = ImageBundle(sprite, self.x + xpos, self.y + ypos, layer=self.layer,
                        scale=self.scale, color=self.color)
                self._letter_images.append(img)  
                xpos += (self.x_kerning + a_sprite.width()) * self.scale

    def update(self, new_x=None, new_y=None, new_depth=None, new_color=None):
        dx = 0 if new_x is None else new_x - self.x
        dy = 0 if new_y is None else new_y - self.y
        new_imgs = []
        for letter in self._letter_images:
            letter_new_x = letter.x() + dx
            letter_new_y = letter.y() + dy
            new_imgs.append(letter.update(new_x=letter_new_x, new_y=letter_new_y,
                                          new_depth=new_depth, new_color=new_color))

        self._letter_images = new_imgs
        self.x = new_x if new_x is not None else self.x
        self.y = new_y if new_y is not None else self.y
        self.color = new_color if new_color is not None else self.color
        self.actual_size = self._recalc_size()

    def all_bundles(self):
        for b in self._letter_images:
            if b is not None:
                yield b
        

class ItemImage:
    
    def __init__(self, x, y, item, layer, scale):
        self.x = x
        self.y = y
        self.item = item
        self.scale = scale
        self._cube_images = []
        self.layer = layer
        
        self._build_images()
        
    def _build_images(self):
        for cube in self.item.cubes:
            art = 0 if cube not in self.item.cube_art else self.item.cube_art[cube]
            sprite = spriteref.item_piece_bigs[art]
            xpos = self.x + sprite.width()*self.scale*cube[0]
            ypos = self.y + sprite.height()*self.scale*cube[1]
            img = ImageBundle(sprite, xpos, ypos, layer=self.layer, scale=self.scale, color=self.item.color)
            self._cube_images.append(img)
            
    def all_bundles(self):
        for b in self._cube_images:
            yield b

    @staticmethod
    def calc_size(item, scale):
        sprite = spriteref.item_piece_bigs[0]
        return (scale*sprite.width()*item.w(), scale*sprite.height()*item.h())
        

class ItemInfoPane:
    
    def __init__(self, item):
        self.item = item        
        self.layer = spriteref.UI_TOOLTIP_LAYER

        self.top_panel = None
        self.mid_panels = []
        self.bot_panel = None
        self.item_image = None
        self.title_text = None
        self.core_texts = []
        self.non_core_texts = []
        self.item_image = None
        
        self._build_images()

    def _build_images(self):
        sc = 2
        self.top_panel = ImageBundle(spriteref.item_panel_top, 0, 0, layer=self.layer, scale=sc)
        h = self.top_panel.height()
        for i in range(0, len(self.item.non_core_stats())):
            img = ImageBundle(spriteref.item_panel_middle, 0, h, layer=self.layer, scale=sc)
            h += img.height()
            self.mid_panels.append(img)
        
        if len(self.mid_panels) > 0:
            bot_sprite = spriteref.item_panel_bottom_0
        else:
            bot_sprite = spriteref.item_panel_bottom_1
            h -= bot_sprite.height() * sc  # covers up part of the top
        self.bot_panel = ImageBundle(bot_sprite, 0, h, layer=self.layer, scale=sc)
        
        self.title_text = TextImage(8*sc, 6*sc, self.item.name, self.layer, scale=sc)
        
        line_spacing = int(1.5*sc)
        
        h = 16*sc + line_spacing
        lvl_txt = TextImage(56*sc, h, self.item.level_string(), self.layer, scale=sc)
        self.core_texts.append(lvl_txt)
        h += lvl_txt.line_height()

        for stat in self.item.core_stats():
            h += line_spacing
            stat_txt = TextImage(56*sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
            self.core_texts.append(stat_txt)
            h += stat_txt.line_height()   
         
        h = 64*sc
        for stat in self.item.non_core_stats():
            h += line_spacing
            stat_txt = TextImage(8*sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
            self.non_core_texts.append(stat_txt)
            h += stat_txt.line_height()   
        
        item_img_sc = sc // 2
        item_img_size = ItemImage.calc_size(self.item, item_img_sc)
        item_img_x = 8*sc + 40*sc // 2 - item_img_size[0] // 2
        item_img_y = 16*sc + 40*sc // 2 - item_img_size[1] // 2
        self.item_image = ItemImage(item_img_x, item_img_y, self.item, self.layer, item_img_sc)
                    
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
                
        for bun in self.item_image.all_bundles():
            yield bun
        
        
        
        
    
    

