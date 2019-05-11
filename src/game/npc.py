
from enum import Enum
import src.game.spriteref as sr
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.events as events
import src.game.globalstate as gs


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

