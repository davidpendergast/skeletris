
import random
import src.game.dialog as dialog
import src.game.spriteref as spriteref
import src.game.globalstate as gs
from src.utils.util import Utils


_ALL_DECORATION_TYPES = []
_ALL_RAND_SPAWN_DEC_TYPES = []


def _add_dec_type(val, rand_spawn=True):
    _ALL_DECORATION_TYPES.append(val)
    if rand_spawn:
        _ALL_RAND_SPAWN_DEC_TYPES.append(val)
    return val


class DecorationType:

    BUCKET = _add_dec_type("BUCKET")
    PLANT = _add_dec_type("PLANT")
    RAKE = _add_dec_type("RAKE")
    BONES = _add_dec_type("BONES")
    MUSHROOM = _add_dec_type("MUSHROOM")
    WORKBENCH = _add_dec_type("WORKBENCH", rand_spawn=False)


class DecorationFactory:

    @staticmethod
    def get_decoration(level, dec_type=None, with_dialog=None):
        """
        :param level: level of the zone in which the decoration will appear.
        :param dec_type: the type of the decoration. If None, a random one will be used.
        :param with_dialog: A string. The dialog text. If empty, the decoration will have no dialog and
            will not be interactable. If None, the decoration type's default dialog text will be used.
        """
        if dec_type is None:
            dec_type = random.choice(_ALL_RAND_SPAWN_DEC_TYPES)

        dec_sprite = DecorationFactory.get_sprite(dec_type, level)

        import src.world.entities as entities
        dec_ent = entities.DecorationEntity.wall_decoration([dec_sprite], 0, 0)

        if with_dialog is None:
            dec_dialog = DecorationFactory.get_dialog(dec_type, level)
        elif with_dialog is not None:
            dec_dialog = dialog.Dialog(with_dialog)
        else:
            dec_dialog = None

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
        elif dec_type == DecorationType.WORKBENCH:
            return spriteref.wall_decoration_workbench
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
            return dialog.Dialog("It's a large cluster of mushrooms.")
        elif dec_type == DecorationType.WORKBENCH:
            return dialog.Dialog("It's a workbench. It looks well-used.")
        else:
            return None

    @staticmethod
    def get_sign_dialog(level):
        rotate_keys = gs.get_instance().settings().rotate_cw_key()
        if len(rotate_keys) > 0:
            rotate_key = Utils.stringify_key(rotate_keys[0])
        else:
            rotate_key = "None"

        inv_keys = gs.get_instance().settings().inventory_key()
        if len(inv_keys) > 0:
            inv_key = Utils.stringify_key(inv_keys[0])
        else:
            inv_key = "None"

        esc_keys = gs.get_instance().settings().exit_key()
        if len(esc_keys) > 0:
            esc_key = Utils.stringify_key(esc_keys[0])
        else:
            esc_key = "None"

        how_to_play_text = [
            "You can rotate the item on your cursor! It's important! Just press [{}].".format(rotate_key),
            "Open your inventory by pressing [{}].".format(inv_key),
            "Resting enemies don't slap back! Look for the Zzz's!",
            "Death is permanent, so watch your step.",
            "You can customize the controls if you don't like them! Press [{}]".format(esc_key)]

        message = random.choice(how_to_play_text)
        return dialog.NpcDialog(message, spriteref.sign_faces)

    @staticmethod
    def get_sign(level, sign_text=None):
        import src.world.entities as entities
        sign_ent = entities.DecorationEntity.wall_decoration(spriteref.wall_decoration_sign, 0, 0)

        if sign_text is None:
            sign_dialog = DecorationFactory.get_sign_dialog(level)
        else:
            sign_text = Utils.listify(sign_text)
            sign_dialog = dialog.Dialog.link_em_up([dialog.NpcDialog(x, spriteref.sign_faces) for x in sign_text])

        sign_ent.set_interact_dialog(sign_dialog)

        return sign_ent
