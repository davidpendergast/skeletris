from src.game import spriteref as spriteref
from src.renderengine.img import ImageBundle
from src.ui.ui import TextImage, ItemImage


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

        self.title_text = TextImage(8 * sc, 6 * sc, self.item.name, self.layer, scale=sc)

        line_spacing = int(1.5*sc)

        h = 16*sc + line_spacing
        lvl_txt = TextImage(56 * sc, h, self.item.level_string(), self.layer, scale=sc)
        self.core_texts.append(lvl_txt)
        h += lvl_txt.line_height()

        for stat in self.item.core_stats():
            h += line_spacing
            stat_txt = TextImage(56 * sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
            self.core_texts.append(stat_txt)
            h += stat_txt.line_height()

        h = 64*sc
        for stat in self.item.non_core_stats():
            h += line_spacing
            stat_txt = TextImage(8 * sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
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