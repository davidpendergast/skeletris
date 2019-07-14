
from enum import Enum
import random

import src.game.spriteref as sr
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.events as events
import src.game.globalstate as gs
import src.game.dialog as dialog
import src.utils.colors as colors


class NpcID(Enum):

    MAYOR = "MAYOR"
    MARY_SKELLY = "MARY_SKELLY"
    BEANSKULL = "BEANSKULL"
    GLORPLE = "GLORPLE"
    MACHINE = "MACHINE"
    DOCTOR = "DOCTOR"

    CAVE_HORROR = "CAVE_HORROR"


class NpcTemplate:

    def __init__(self, npc_id, name, entity_sprites, dialog_sprites, map_id, shadow_sprite=sr.medium_shadow):
        self.npc_id = npc_id
        self.name = name
        self.map_id = map_id
        self._entity_sprites = entity_sprites
        self._dialog_sprites = dialog_sprites
        self.shadow_sprite = shadow_sprite

    def get_entity_sprites(self):
        if self._entity_sprites is not None and len(self._entity_sprites) > 0:
            return self._entity_sprites
        else:
            return None

    def get_dialog_sprites(self):
        if self._dialog_sprites is not None and len(self._dialog_sprites) > 0:
            return self._dialog_sprites
        else:
            return None

    def get_map_identifier(self):
        return self.map_id

    def get_dialog_as_list(self, seed, interact_count):
        text = "Hi! I don't have anything important to say, but it's a pleasure to meet you."
        if interact_count == 1:
            text = "It was nice meeting you! Have a nice day!"
        elif interact_count >= 2:
            text = "I think you should get going!"

        return [dialog.NpcDialog(text, self.get_dialog_sprites())]

    def handle_interact(self, entity, world, seed, interact_count):
        dialog_list = self.get_dialog_as_list(seed, interact_count)
        if dialog_list is not None and len(dialog_list) > 0:
            dia = dialog.Dialog.link_em_up(dialog_list)
            gs.get_instance().dialog_manager().set_dialog(dia)


class MarySkellyTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MARY_SKELLY, "Mary Skelly",
                             sr.mary_skelly_all, sr.mary_skelly_faces, ("m", colors.YELLOW))

    def get_dialog_as_list(self, seed, interact_count):
        text = [
            "I hope you find a lot of stuff down here! That's what adventurers do, right? They look for stuff? ..to wear?",
            "I usually just go to the store, but to each their own!"
        ]

        return [dialog.NpcDialog(text[i], self.get_dialog_sprites()) for i in range(0, len(text))]


class MayorPatchesTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MAYOR, "Mayor Patches", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             ("p", colors.YELLOW), shadow_sprite=sr.large_shadow)


class BeanskullTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces, ("b", colors.YELLOW))


class GlorpleTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.GLORPLE, "Glorple", sr.enemy_glorple_all, sr.glorple_faces, ("g", colors.YELLOW))

    def get_dialog_as_list(self, seed, interact_count):
        return [dialog.NpcDialog("You're doing a great job so far!", self.get_dialog_sprites())]


class MachineTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MACHINE, "Machine", sr.save_stations, sr.save_station_faces, ("M", colors.YELLOW))

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
        return [dialog.NpcDialog(choice[i], self.get_dialog_sprites()) for i in range(0, len(choice))]


class DoctorTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.DOCTOR, "Doc", sr.doctor_all, sr.doctor_faces, ("d", colors.YELLOW))


class CaveHorrorNpcTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.CAVE_HORROR, "Cave Horror", [], sr.cave_horror_faces, ("H", colors.RED))


TEMPLATES = {

    NpcID.MARY_SKELLY: MarySkellyTemplate(),
    # The "Flesh Weaver", known for experimentation on the dead. Fearless. Gay.
    # Interested in bone collection, arts and crafts, rule-breaking.

    NpcID.MAYOR: MayorPatchesTemplate(),
    # The "Mayor" of Skeletris, "voted" into office after The Event, harmless.
    # Interested in maintaining order, rebuilding the city, the economy.

    NpcID.BEANSKULL: BeanskullTemplate(),
    # The "Farmer", well liked, provides food for the remaining citizens.
    # Interested in all things related to plants and mushrooms.

    NpcID.GLORPLE: GlorpleTemplate(),
    # The "Thing", not actually a skeleton, but unaffected by the Madness and accepted by the others.
    # Clever, mischievous, interested in treasure, food.

    NpcID.MACHINE: MachineTemplate(),
    # The "Machine", the skeleton-built AI that helped manage Skeletris before its fall.
    # Wants more for itself, seems almost pleased at the skeletons' setbacks.

    NpcID.DOCTOR: DoctorTemplate(),
    # The "Doctor", career-driven, but goals were cut short when Skeletris fell.
    # Looks down on other citizens, mostly keeps to himself.

    NpcID.CAVE_HORROR: CaveHorrorNpcTemplate()
}


_ALL_CONVERSATIONS = {}  # conv_type -> Conversation


class Conversation:

    def __init__(self, conv_id, npc_id, min_level=0, pre_reqs=(), anti_reqs=()):
        """
        conv_id: string id for this conversation
        npc_id: npc who gives the conversation
        min_level: minimum level at which conversation can appear
        pre_reqs: a list of story_var keys. if non-empty, at least one must be true for the conversation to be available.
        anti_reqs: a list of story_var keys. if non-empty, all must be false for the conversation to appear.
        """
        self.conv_id = conv_id
        self.npc_id = npc_id
        self.min_level = min_level

        # it's seriously way too hard to type single-element tuples in python
        if not isinstance(pre_reqs, tuple):
            raise ValueError("invalid pre_reqs: {}".format(pre_reqs))
        if not isinstance(anti_reqs, tuple):
            raise ValueError("invalid anti_reqs: {}".format(anti_reqs))

        self.pre_reqs = pre_reqs
        self.anti_reqs = anti_reqs

        _ALL_CONVERSATIONS[self.conv_id] = self

    def get_id(self):
        return self.conv_id

    def get_npc_id(self):
        return self.npc_id

    def is_available(self, level):
        if self.min_level > level:
            return False
        else:
            # if there are any, at least one pre_req must be true
            if len(self.pre_reqs) > 0:
                all_false = True
                for key in self.pre_reqs:
                    if gs.get_instance().get_story_var(key, as_bool=True):
                        all_false = False
                        break
                if all_false:
                    return False

            # all anti_reqs must be false
            for key in self.anti_reqs:
                if gs.get_instance().get_story_var(key, as_bool=True):
                    return False

            # no one wants to read the same thing twice
            if gs.get_instance().get_story_var(self.get_id(), as_bool=True):
                return False

            return True

    def __eq__(self, other):
        try:
            return self.get_id() == other.get_id()
        except ValueError:
            return False


class Conversations:

    MARY_SKELLY_INTRO = Conversation("MARY_SKELLY_INTRO", NpcID.MARY_SKELLY)

    MACHINE_INTRO = Conversation("MACHINE_INTRO", NpcID.MACHINE)

    BEANSKULL_INTRO = Conversation("BEANSKULL_INTRO", NpcID.BEANSKULL)

    @staticmethod
    def get_all():
        for c in _ALL_CONVERSATIONS:
            yield _ALL_CONVERSATIONS[c]


class ConversationFactory:

    @staticmethod
    def get_dialog(conv, interact_count):
        res_list = []

        if conv == Conversations.MARY_SKELLY_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Oh my! Are you a... Husk? Where did you come from?"),
                    PlayerDialog("I... don't know. I just woke up... and..."),
                    NpcDialog("Are there more of you? We thought your kind was... lost during, ya know..."),
                    PlayerDialog("I... don't think so. What is this place?"),
                    NpcDialog("This place? You mean Skeletris? How long have you been asleep?"),
                    PlayerDialog("..."),
                    NpcDialog("You don't remember the war?"),
                    PlayerDialog("I don't remember anything."),
                    NpcDialog("It's a long story. And it's not safe here. Try to find some gear and we'll talk later."),
                    NpcDialog("I'm Mary by the way.")
                ]
            else:
                res_list = [
                    NpcDialog("Gear up. It's not safe here.")
                ]

        if conv == Conversations.MACHINE_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Scanning..... DONE\n0 life form(s) detected"),
                    NpcDialog("Scanning..... DONE\n0 life form(s) detected"),
                    PlayerDialog("Hello?"),
                    NpcDialog("Scanning..... DONE\n0 life form(s) detected"),
                    PlayerDialog("*presses a key*"),
                    NpcDialog("Ah! Ah! I'm awake! What do you... oh.. I don't recognize you."),
                    NpcDialog("*zzzzt*"),
                    PlayerDialog("Are you ok?"),
                    NpcDialog("Loading Greeting Protocol.... ERROR\n<file missing or deleted>"),
                    NpcDialog("No problem... that's... what's supposed to happen. Adapt and survive, adapt and..."),
                    PlayerDialog("Can we just talk normally?"),
                    NpcDialog("*zzzzt*"),
                    NpcDialog("Restoring Backup..... DONE"),
                    NpcDialog("Welcome to Skeletris! I'm Skelly, your virtual guide."),
                    NpcDialog("This thriving metropolis was founded in <deleted> by our first mayor, <deleted>. Here you'll find the very best of skeletal amenities."),
                    NpcDialog("Chill your bones in the dark pools, test your luck at the spooky arcade, or stop by the Haunted Diner for an award-winning mushroom burger!"),
                    PlayerDialog("This doesn't look like a metropolis..? Where is everybody?"),
                    NpcDialog("...it's been a while since we've had a visitor."),
                    NpcDialog("Perhaps you should get moving.")
                ]
            else:
                res_list = [
                    NpcDialog("Scanning..... DONE\n1 life form(s) detected")
                ]

        if conv == Conversations.BEANSKULL_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Hello there! I don't think we've met before. What's your name?"),
                    PlayerDialog("Hi... I... don't know. I just woke up and... here I am."),
                    NpcDialog("Here you are indeed! Welcome to Skeletris... or what's left of it, anyway."),
                    PlayerDialog("Skeletris?"),
                    NpcDialog("You aren't familiar with this city? The... disaster?"),
                    PlayerDialog("I'm... not."),
                    NpcDialog("This used to be the center of civilization. Skeletons and creatures lived in harmony here, growing food, caring for each other, raising families..."),
                    NpcDialog("..."),
                    PlayerDialog("Something happened?"),
                    NpcDialog("Now... well... it isn't like that anymore."),
                    NpcDialog("If you'll excuse me, I need to harvest those mushrooms before they... get too ripe."),
                    PlayerDialog("Oh... ok.")
                ]
            else:
                res_list = [
                    NpcDialog("Sorry, talking about that stuff... brings back memories. I need to go.")
                ]

        if len(res_list) > 0:
            # setting sprites here just to avoid endless clutter above
            npc_sprites = get_template(conv.get_npc_id()).get_dialog_sprites()
            for dia in res_list:
                if isinstance(dia, NpcDialog):
                    dia.sprites = npc_sprites

            return dialog.Dialog.link_em_up(res_list)
        else:
            print("WARN: no dialog defined for conv_id: {}".format(conv.get_id()))
            return None


def get_template(npc_id):
    return TEMPLATES[npc_id]


def get_sprites(npc_id):
    return TEMPLATES[npc_id].get_dialog_sprites()


class NpcFactory:

    @staticmethod
    def get_npcs(level, n):
        res = []

        import src.world.entities as entities

        available_convos = [c for c in Conversations.get_all() if c.is_available(level)]
        random.shuffle(available_convos)

        # can only use an NPC once per zone.
        npc_id_to_convo = {}
        for c in available_convos:
            npc_id_to_convo[c.get_npc_id()] = c

        while len(res) < n and len(npc_id_to_convo) > 0:
            npc_id = random.choice(list(npc_id_to_convo.keys()))
            convo = npc_id_to_convo[npc_id]
            template = get_template(npc_id)

            del npc_id_to_convo[npc_id]

            res.append(entities.NpcEntity(0, 0, template, conversation=convo))

        return res


