
import random
import src.game.dialog as dialog
import src.game.spriteref as spriteref
import src.game.globalstate as gs
from src.utils.util import Utils


_ALL_DECORATION_TYPES = []


def _add_dec_type(val):
    _ALL_DECORATION_TYPES.append(val)
    return val


class DecorationType:

    BUCKET = _add_dec_type("BUCKET")
    PLANT = _add_dec_type("PLANT")
    RAKE = _add_dec_type("RAKE")
    BONES = _add_dec_type("BONES")
    MUSHROOM = _add_dec_type("MUSHROOM")


class DecorationFactory:

    @staticmethod
    def get_decoration(level):
        import src.world.entities as entities
        dec_type = random.choice(_ALL_DECORATION_TYPES)
        dec_sprite = DecorationFactory.get_sprite(dec_type, level)
        dec_ent = entities.DecorationEntity.wall_decoration([dec_sprite], 0, 0)

        dec_dialog = DecorationFactory.get_dialog(dec_type, level)
        if dec_dialog is not None:
            dec_ent.set_interact_dialog(dec_dialog)

        return dec_ent

    @staticmethod
    def get_sprite(dec_type, level, rand_seed=None):
        if rand_seed is None:
            rand_seed = random.random()

        if dec_type == DecorationType.BUCKET:
            return spriteref.wall_decoration_bucket
        elif dec_type == DecorationType.PLANT:
            idx = int(rand_seed * len(spriteref.wall_decoration_plants))
            return spriteref.wall_decoration_plants[idx]
        elif dec_type == DecorationType.RAKE:
            return spriteref.wall_decoration_rake
        elif dec_type == DecorationType.BONES:
            return spriteref.wall_decoration_bones
        elif dec_type == DecorationType.MUSHROOM:
            idx = int(rand_seed * len(spriteref.wall_decoration_mushrooms))
            return spriteref.wall_decoration_mushrooms[idx]
        else:
            raise ValueError("unknown decoration type: {}".format(dec_type))

    @staticmethod
    def get_dialog(dec_type, level, rand_seed=None):
        if dec_type == DecorationType.BUCKET:
            return dialog.Dialog("It's a bucket. No treasure inside.")
        elif dec_type == DecorationType.PLANT:
            return dialog.Dialog("It's a plant. It looks well-maintained.")
        elif dec_type == DecorationType.RAKE:
            return dialog.Dialog("It's a rake.")
        elif dec_type == DecorationType.BONES:
            return dialog.Dialog("It seems to be a decoration of some kind.")
        elif dec_type == DecorationType.MUSHROOM:
            return dialog.Dialog("It's a large cluster of mushrooms. They look delicious.")
        else:
            return None

    @staticmethod
    def get_sign_dialog(level):
        rotate_key = gs.get_instance().settings().rotate_cw_key()
        if isinstance(rotate_key, list):
            rotate_key = Utils.stringify_key(rotate_key[0])
        else:
            rotate_key = str(rotate_key)

        inv_key = gs.get_instance().settings().inventory_key()
        if isinstance(inv_key, list):
            inv_key = Utils.stringify_key(inv_key[0])
        else:
            inv_key = str(inv_key)

        esc_key = gs.get_instance().settings().exit_key()
        if isinstance(esc_key, list):
            esc_key = Utils.stringify_key(esc_key[0])
        else:
            esc_key = str(esc_key)

        how_to_play_text = [
            "You can rotate the item on your cursor! It's important! Just press [{}].".format(rotate_key),
            "Open your inventory by pressing [{}].".format(inv_key),
            "Resting enemies don't slap back! Look for the Zzz's!",
            "Death is permanent, so watch your step.",
            "You can customize the controls if you don't like them! Press [{}]".format(esc_key)]

        message = random.choice(how_to_play_text)
        return dialog.NpcDialog(message, spriteref.sign_faces)

    @staticmethod
    def get_sign(level):
        import src.world.entities as entities
        sign_ent = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_sign, 0, 0)
        sign_dialog = DecorationFactory.get_sign_dialog(level)
        sign_ent.set_interact_dialog(sign_dialog)

        return sign_ent
