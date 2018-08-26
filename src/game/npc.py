
from enum import Enum
import src.game.spriteref as sr
import src.game.dialog as dialog
from src.game.dialog import NpcDialog, PlayerDialog


class NpcID(Enum):

    MAYOR = "MAYOR"
    MARY_SKELLY = "MARY_SKELLY"
    BEANSKULL = "BEANSKULL"
    GLORPLE = "GLORPLE"


class NpcTemplate:

    def __init__(self, npc_id, name, world_sprites, talking_sprites, shadow_sprite=sr.medium_shadow):
        self.npc_id = npc_id
        self.name = name
        self.world_sprites = world_sprites
        self.talking_sprites = talking_sprites
        self.shadow_sprite = shadow_sprite


TEMPLATES = {
    NpcID.MARY_SKELLY: NpcTemplate(NpcID.MARY_SKELLY, "Mary Skelly", sr.mary_skelly_all, sr.mary_skelly_faces),
    NpcID.MAYOR: NpcTemplate(NpcID.MAYOR, "Mayor Patches", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             shadow_sprite=sr.large_shadow),
    NpcID.BEANSKULL: NpcTemplate(NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces),
    NpcID.GLORPLE: NpcTemplate(NpcID.GLORPLE, "Glorple", sr.enemy_glorple_all, sr.glorple_faces)
}


def get_sprites(npc_id):
    return TEMPLATES[npc_id].talking_sprites


class NpcState:
    """
    Tracks the state of all active NPCs in the world
    """

    def update(self, npc_entity, world, gs, input_state, render_engine):
        npc_id = npc_entity.get_id()
        sprites = TEMPLATES[npc_id].world_sprites
        cur_sprite = sprites[(gs.anim_tick // 2) % len(sprites)]
        facing_left = True
        shadow_spr = TEMPLATES[npc_id].shadow_sprite

        npc_entity.update_images(cur_sprite, facing_left, shadow_sprite=shadow_spr)

    def interacted_with(self, npc_id, world, gs):
        chain = [
            NpcDialog("Have you ever tried bone stew before?", get_sprites(NpcID.MARY_SKELLY)),
            NpcDialog("i know a great recipe.. if you can spare a couple bones..", get_sprites(NpcID.MARY_SKELLY)),
            NpcDialog("Don't mind her - she has plenty of bones already!", get_sprites(NpcID.MAYOR)),
            NpcDialog("I need those! for.. stew purposes.. ", get_sprites(NpcID.MARY_SKELLY)),
            PlayerDialog("..."),
            PlayerDialog("Are there any other survivors?"),
            NpcDialog("Glorple survived!", get_sprites(NpcID.GLORPLE)),
            NpcDialog("I think my potatoes are ok.. but i can't say the same about my tomatoes.", get_sprites(NpcID.BEANSKULL)),
            NpcDialog("they were trampled during the attack.", get_sprites(NpcID.BEANSKULL)),
            PlayerDialog("I meant people."),
            NpcDialog("In that case.. I don't think so.", get_sprites(NpcID.BEANSKULL)),
            PlayerDialog("we need to keep moving."),
        ]

        d = dialog.link_em_up(chain)
        gs.dialog_manager().set_dialog(d)
        print("setting dialog to {}".format(d.get_text()))

