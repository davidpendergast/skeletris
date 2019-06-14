
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
    DOCTOR = "DOCTOR"


class NpcTemplate:

    def __init__(self, npc_id, name, world_sprites, talking_sprites, shadow_sprite=sr.medium_shadow):
        self.npc_id = npc_id
        self.name = name
        self.world_sprites = world_sprites
        self.talking_sprites = talking_sprites
        self.shadow_sprite = shadow_sprite

    def get_dialog_as_list(self, seed, interact_count):
        text = "Hi! I don't have anything important to say, but it's a pleasure to meet you."
        if interact_count == 1:
            text = "It was nice meeting you! Have a nice day!"
        elif interact_count >= 2:
            text = "I think you should get going!"

        return [dialog.NpcDialog(text, self.talking_sprites)]

    def handle_interact(self, entity, world, seed, interact_count):
        dialog_list = self.get_dialog_as_list(seed, interact_count)
        if dialog_list is not None and len(dialog_list) > 0:
            dia = dialog.Dialog.link_em_up(dialog_list)
            gs.get_instance().dialog_manager().set_dialog(dia)


class MarySkellyTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MARY_SKELLY, "Mary Skelly", sr.mary_skelly_all, sr.mary_skelly_faces)

    def get_dialog_as_list(self, seed, interact_count):
        text = [
            "I hope you find a lot of stuff down here! That's what adventurers do, right? They look for stuff? ..to wear?",
            "I usually just go to the store, but to each their own!"
        ]

        return [dialog.NpcDialog(text[i], self.talking_sprites) for i in range(0, len(text))]


class MayorPatchesTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MAYOR, "Mayor Patches", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             shadow_sprite=sr.large_shadow)


class BeanskullTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces)


class GlorpleTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.GLORPLE, "Glorple", sr.enemy_glorple_all, sr.glorple_faces)

    def get_dialog_as_list(self, seed, interact_count):
        return [dialog.NpcDialog("You're doing a great job so far!", self.talking_sprites)]


class MachineTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MACHINE, "Discouragement Machine", sr.save_stations, sr.save_station_faces)

    def get_dialog_as_list(self, seed, interact_count):
        # TODO - tailor these to the player's actual progress
        discouragements = [
            ["Are you expecting to beat the game with that gear? Just curious."],
            ["Have you beaten the game yet? Oh, I just saw your playtime so I figured... no that's totally fine."],
            ["I saw that fight back there. Ouch.", "But hey, as long as you're having fun, I can't judge."],
            ["Be careful, my sensors are detecting some bad RNG ahead."],
            ["Isn't it usually better to avoid taking damage?"]
        ]

        choice = discouragements[int(seed * len(discouragements))]
        return [dialog.NpcDialog(choice[i], self.talking_sprites) for i in range(0, len(choice))]


class DoctorTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.DOCTOR, "Doc", sr.doctor_all, sr.doctor_faces)


TEMPLATES = {
    NpcID.MARY_SKELLY: MarySkellyTemplate(),
    NpcID.MAYOR: MayorPatchesTemplate(),
    NpcID.BEANSKULL: BeanskullTemplate(),
    NpcID.GLORPLE: GlorpleTemplate(),
    NpcID.MACHINE: MachineTemplate(),
    NpcID.DOCTOR: DoctorTemplate()
}


def get_template(npc_id):
    return TEMPLATES[npc_id]


def get_sprites(npc_id):
    return TEMPLATES[npc_id].talking_sprites


class NpcFactory:

    @staticmethod
    def get_npcs(level, n):
        res = []

        import src.world.entities as entities

        # eventually this'll be more complicated
        npc_ids_for_level = list(TEMPLATES.keys())

        while len(res) < n and len(npc_ids_for_level) > 0:
            # npc_id = npc_ids_for_level.pop(-1)
            npc_id = random.choice(npc_ids_for_level)
            template = TEMPLATES[npc_id]
            res.append(entities.NpcEntity(0, 0, template, npc_seed=random.random()))

        return res


