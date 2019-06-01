
from enum import Enum
import random

import src.game.spriteref as sr
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.events as events
import src.game.globalstate as gs
import src.game.dialog as dialog


class NpcID(Enum):

    MAYOR = "MAYOR"
    MARY_SKELLY = "MARY_SKELLY"
    BEANSKULL = "BEANSKULL"
    GLORPLE = "GLORPLE"
    MACHINE = "MACHINE"


class NpcTemplate:

    def __init__(self, npc_id, name, world_sprites, talking_sprites, shadow_sprite=sr.medium_shadow):
        self.npc_id = npc_id
        self.name = name
        self.world_sprites = world_sprites
        self.talking_sprites = talking_sprites
        self.shadow_sprite = shadow_sprite


TEMPLATES = {
    NpcID.MARY_SKELLY: NpcTemplate(NpcID.MARY_SKELLY, "Mary Skelly", sr.mary_skelly_all, sr.mary_skelly_faces),
    NpcID.MAYOR: NpcTemplate(NpcID.MAYOR, "Mayor Patches", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces, shadow_sprite=sr.large_shadow),
    NpcID.BEANSKULL: NpcTemplate(NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces),
    NpcID.GLORPLE: NpcTemplate(NpcID.GLORPLE, "Glorple", sr.enemy_glorple_all, sr.glorple_faces),
    NpcID.MACHINE: NpcTemplate(NpcID.MACHINE, "Discouragement Machine", sr.save_stations, sr.save_station_faces)
}


def get_template(npc_id):
    return TEMPLATES[npc_id]


def get_sprites(npc_id):
    return TEMPLATES[npc_id].talking_sprites


def get_sample_dialog(npc_id):
    sprites = TEMPLATES[npc_id].talking_sprites
    if npc_id == NpcID.MACHINE:
        options = [
            [
                dialog.NpcDialog("Are you expecting to beat the game with that gear? Just curious.", sprites),
            ]
        ]
    else:
        options = [
            [
                dialog.NpcDialog("I hope you find a lot of stuff down here! That's what adventurers do, right? They look for stuff? ..to wear?", sprites),
                dialog.NpcDialog("I usually just go to the store, but to each their own!", sprites),
            ], [
                dialog.NpcDialog("Hi! I don't have anything important to say, but it's a pleasure to meet you.", sprites)
            ], [
                dialog.NpcDialog("You're doing a great job so far!", sprites)
            ]
        ]

    return dialog.Dialog.link_em_up(random.choice(options))


