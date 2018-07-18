from src.game import spriteref as spriteref
import src.items.item as item
from src.renderengine.img import ImageBundle
from src.ui.ui import TextImage, ItemImage
from src.game.stats import StatType
from src.game.actorstate import EnemyState
import src.game.enemies as enemies


class TooltipFactory:

    @staticmethod
    def build_tooltip(obj):
        if isinstance(obj, item.Item):
            return ItemInfoTooltip(obj)
        elif isinstance(obj, EnemyState):
            return EnemyInfoTooltip(obj)
        else:
            return None


class Tooltip:

    def __init__(self):
        self.layer = spriteref.UI_TOOLTIP_LAYER

    def all_bundles(self):
        return []

    def get_target(self):
        """
            returns: object that this tooltip is 'for'
        """
        return None


class TitleImageAndStatsTooltip(Tooltip):

    def __init__(self, title, level, stat_list):
        Tooltip.__init__(self)
        self.title = title
        self.level = level
        self.core_stats = [s for s in stat_list if s.stat_type in item.CORE_STATS]
        self.non_core_stats = [s for s in stat_list if s.stat_type not in item.CORE_STATS]

        self.top_panel = None
        self.mid_panels = []
        self.bot_panel = None
        self.title_text = None
        self.core_texts = []
        self.non_core_texts = []
        self.special_bundles = None

        self._build_images()

    def _build_images(self):
        sc = 2
        self.top_panel = ImageBundle(spriteref.item_panel_top, 0, 0, layer=self.layer, scale=sc)
        h = self.top_panel.height()
        for i in range(0, len(self.non_core_stats)):
            img = ImageBundle(spriteref.item_panel_middle, 0, h, layer=self.layer, scale=sc)
            h += img.height()
            self.mid_panels.append(img)

        if len(self.mid_panels) > 0:
            bot_sprite = spriteref.item_panel_bottom_0
        else:
            bot_sprite = spriteref.item_panel_bottom_1
            h -= bot_sprite.height() * sc  # covers up part of the top
        self.bot_panel = ImageBundle(bot_sprite, 0, h, layer=self.layer, scale=sc)

        self.title_text = TextImage(8 * sc, 6 * sc, self.title, self.layer, scale=sc)

        line_spacing = int(1.5 * sc)

        h = 16 * sc + line_spacing

        if self.level is not None:
            lvl_str = "LVL:{}".format(self.level)
            lvl_txt = TextImage(56 * sc, h, lvl_str, self.layer, scale=sc)
            self.core_texts.append(lvl_txt)
            h += lvl_txt.line_height()

        for stat in self.core_stats:
            h += line_spacing
            stat_txt = TextImage(56 * sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
            self.core_texts.append(stat_txt)
            h += stat_txt.line_height()

        h = 64 * sc
        for stat in self.non_core_stats:
            h += line_spacing
            stat_txt = TextImage(8 * sc, h, str(stat), self.layer, color=stat.color(), scale=sc)
            self.non_core_texts.append(stat_txt)
            h += stat_txt.line_height()

        special_img_rect = [8*sc, 16*sc, 40*sc, 40*sc]
        self.special_bundles = [x for x in self.get_special_image_bundles(special_img_rect, sc)]

    def get_special_image_bundles(self, rect, sc):
        return []

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

        for bun in self.special_bundles:
            yield bun


class ItemInfoTooltip(TitleImageAndStatsTooltip):

    def __init__(self, item):
        self.item = item
        TitleImageAndStatsTooltip.__init__(self, item.name, item.level, item.all_stats())

    def get_target(self):
        return self.item

    def get_special_image_bundles(self, rect, sc):
        item_img_sc = sc // 2
        item_img_size = ItemImage.calc_size(self.item, item_img_sc)
        item_img_x = rect[0] + rect[2] // 2 - item_img_size[0] // 2
        item_img_y = rect[1] + rect[3] // 2 - item_img_size[1] // 2
        return ItemImage(item_img_x, item_img_y, self.item, self.layer, item_img_sc).all_bundles()


class EnemyInfoTooltip(TitleImageAndStatsTooltip):

    def __init__(self, enemy_state):
        self.e_state = enemy_state
        stat_map = enemy_state.get_base_stats()
        stats = []
        for stat_type in stat_map:
            if not isinstance(stat_type, StatType):
                continue
            stat_val = stat_map[stat_type] - enemies.TRUE_BASE_STATS[stat_type]

            if stat_val != 0:
                stats.append(item.ItemStat(stat_type, stat_val))

        TitleImageAndStatsTooltip.__init__(self, enemy_state.name(), enemy_state.level(), stats)

    def get_target(self):
        return self.e_state

    def get_special_image_bundles(self, rect, sc):
        bun = ImageBundle.new_bundle(self.layer, sc)
        sprite = self.e_state.template.get_sprites()[0]
        color = self.e_state.base_color()
        x = rect[0] + rect[2] // 2 - sc * sprite.width() // 2
        y = rect[1] + rect[3] // 2 - sc * sprite.height() // 2
        return [bun.update(new_x=x, new_y=y, new_color=color, new_model=sprite)]
