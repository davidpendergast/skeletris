
from enum import Enum
import src.game.spriteref as sr
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.events as events


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
        if npc_entity.get_vel()[0] < 0:
            facing_left = True
        elif npc_entity.get_vel()[0] > 0:
            facing_left = False
        elif npc_entity.facing_player:
            p = world.get_player()
            if p is not None:
                facing_left = p.center()[0] <= npc_entity.center()[0]

        shadow_spr = TEMPLATES[npc_id].shadow_sprite

        npc_entity.update_images(cur_sprite, facing_left, shadow_sprite=shadow_spr)

        interacted_with_me = gs.event_queue().has_event(types=events.EventType.NPC_INTERACT,
                                                        predicate=lambda e: e.get_npc_id() == npc_id)
        if interacted_with_me:
            self.interacted_with(npc_id, world, gs)

    def interacted_with(self, npc_id, world, gs):
        pass
