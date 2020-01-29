
from enum import Enum
import random

import src.game.spriteref as sr
from src.game.dialog import NpcDialog, PlayerDialog
import src.game.globalstate as gs
import src.game.dialog as dialog
import src.utils.colors as colors
from src.utils.util import Utils
import src.game.balance as balance
import src.items.cubeutils as cubeutils


class NpcID(Enum):

    MAYOR = "MAYOR"
    BEANSKULL = "BEANSKULL"
    GROK = "GROK"
    MACHINE = "MACHINE"
    DOCTOR = "DOCTOR"
    SKELEKID = "SKELEKID"
    HEAD = "HEAD"
    ROBO = "ROBO"

    MARY_SKELLY = "MARY_SKELLY"
    MARY_SKELLY_WITH_HEAD = "MARY_WITH_HEAD"

    MATHILDA = "MATHILDA"
    MATHILDA_INCOMPLETE = "MATHILDA_INCOMPLETE"

    WANDERER = "WANDERER"
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

    def get_trade_protocol(self, level):
        return None

    def get_dialog_sprites(self):
        if self._dialog_sprites is not None and len(self._dialog_sprites) > 0:
            return self._dialog_sprites
        else:
            return None

    def get_map_identifier(self):
        return self.map_id


class MarySkellyTemplate(NpcTemplate):

    def __init__(self, with_head=False):
        NpcTemplate.__init__(self,
                             NpcID.MARY_SKELLY if not with_head else NpcID.MARY_SKELLY_WITH_HEAD,
                             "Mary Skelly",
                             sr.mary_skelly_all if not with_head else sr.mary_holding_mathilda_all,
                             sr.mary_skelly_faces, ("m", colors.YELLOW))


class MayorPatchesTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MAYOR, "Mayor", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             ("p", colors.YELLOW), shadow_sprite=sr.large_shadow)

    def get_trade_protocol(self, level):
        if level >= 12:  # first meet in town, but he only starts showing up in the catacombs
            return NpcTradeProtocols.REROLL_ART


class BeanskullTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces, ("b", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 4:  # first meet in town
            return NpcTradeProtocols.REROLL_STATS


class GrokTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.GROK, "Grok", sr.grok_all, sr.grok_faces, ("g", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 10:  # first meet at the vents
            return NpcTradeProtocols.MIRROR_TRADE


class MachineTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MACHINE, "PrintBot", sr.print_bot_all, sr.print_bot_faces, ("P", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 8:  # city only
            return NpcTradeProtocols.ITEM_THAT_FITS


class DoctorTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.DOCTOR, "Doctor", sr.doctor_all, sr.doctor_faces, ("d", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 4:  # unexplained, first meet at swamps
            return NpcTradeProtocols.POTION_EXCHANGE


class SkelekidTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.SKELEKID, "Skelekid", sr.skelekid_all, sr.skelekid_faces, ("s", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 10:  # first meet at vents
            return NpcTradeProtocols.REROLL_CUBES


class HeadTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.HEAD, "Disembodied Head", sr.skull_head_all, sr.skull_head_faces, ("h", colors.YELLOW))


class RoboTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.ROBO, "B.O.S.S.", sr.wall_decoration_robo_console_skull, sr.robo_faces, ("B", colors.YELLOW))


class ScorpionTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.WANDERER, "Wanderer", sr.enemy_scorpion_all, sr.scorpion_faces, ("s", colors.YELLOW))


class MathildaTemplate(NpcTemplate):

    def __init__(self, incomplete=False):
        NpcTemplate.__init__(self,
                             NpcID.MATHILDA if not incomplete else NpcID.MATHILDA_INCOMPLETE,
                             "Mathilda Skelly",
                             sr.mathilda_all if not incomplete else sr.mathilda_incomplete_all,
                             sr.mathilda_faces,
                             ("m", colors.YELLOW))


# TODO - delete? not ever used as an NPC, feels like it shouldn't talk?
class CaveHorrorNpcTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.CAVE_HORROR, "Cave Horror", [], sr.cave_horror_faces, ("H", colors.RED))


TEMPLATES = {

    NpcID.MARY_SKELLY: MarySkellyTemplate(),
    # The "Flesh Weaver", known for experimentation on the dead. Fearless. Gay.
    # Interested in bone collection, arts and crafts, rule-breaking.

    NpcID.MARY_SKELLY_WITH_HEAD: MarySkellyTemplate(with_head=True),

    NpcID.MATHILDA: MathildaTemplate(),
    # Mary's wife. Missing for most of the story.

    NpcID.MATHILDA_INCOMPLETE: MathildaTemplate(incomplete=True),

    NpcID.MAYOR: MayorPatchesTemplate(),
    # The "Mayor" of Skeletris, "voted" into office after The Event, harmless.
    # Interested in maintaining order, rebuilding the city, the economy.

    NpcID.BEANSKULL: BeanskullTemplate(),
    # The "Farmer", well liked, provides food and equipment for the remaining citizens.
    # Interested in all things related to plants.

    NpcID.GROK: GrokTemplate(),
    # The "Thing", not actually a skeleton, but unaffected by the Madness and accepted by the others.
    # Clever, mischievous, interested in treasure, food.

    NpcID.MACHINE: MachineTemplate(),
    # The "Machine", a skeleton-built AI that helped perform printing services in Skeletris
    # before its fall.

    NpcID.DOCTOR: DoctorTemplate(),
    # The "Doctor", career-driven, but goals were cut short when Skeletris fell.
    # Looks down on other citizens, mostly keeps to himself.

    NpcID.SKELEKID: SkelekidTemplate(),

    NpcID.HEAD: HeadTemplate(),

    NpcID.CAVE_HORROR: CaveHorrorNpcTemplate(),  # TODO - not used, it's stupid to have them talk

    NpcID.ROBO: RoboTemplate(),

    NpcID.WANDERER: ScorpionTemplate(),

}


def all_templates():
    for npc_id in TEMPLATES:
        if npc_id != NpcID.CAVE_HORROR:
            yield TEMPLATES[npc_id]


_ALL_CONVERSATIONS = {}  # conv_type -> Conversation


class Conversation:

    def __init__(self, conv_id, npc_id, pre_reqs=(), anti_reqs=()):
        """
        conv_id: string id for this conversation
        npc_id: npc who gives the conversation
        pre_reqs: a list of story_var keys. if non-empty, at least one must be true for the conversation to be available.
        anti_reqs: a list of story_var keys. if non-empty, all must be false for the conversation to appear.
        """
        self.conv_id = conv_id
        self.npc_id = npc_id

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

    def is_available(self):
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
        except Exception:
            return False


class Conversations:

    MARY_SKELLY_PRE_SPIDER_FIGHT = Conversation("MARY_SKELLY_PRE_SPIDER_FIGHT", NpcID.MARY_SKELLY)

    BEANSKULL_INTRO = Conversation("BEANSKULL_INTRO", NpcID.BEANSKULL)

    MAYOR_INTRO = Conversation("MAYOR_INTRO", NpcID.MAYOR)

    MARY_SKELLY_POST_SPIDER_FIGHT = Conversation("MARY_SKELLY_POST_SPIDER_FIGHT", NpcID.MARY_SKELLY)

    MARY_CLONING_EXPLANATION = Conversation("MARY_CLONING_EXPLANATION", NpcID.MARY_SKELLY)

    MARY_POST_CLONING_NO_DEATHS_YET = Conversation("MARY_POST_CLONING_NO_DEATHS_YET", NpcID.MARY_SKELLY)

    MARY_POST_CLONING_WITH_DEATHS = Conversation("MARY_POST_CLONING_WITH_DEATHS", NpcID.MARY_SKELLY)

    MARY_SKELLY_PRE_FROG_FIGHT = Conversation("MARY_SKELLY_PRE_FROG_FIGHT", NpcID.MARY_SKELLY)

    MARY_SKELLY_POST_FROG_FIGHT = Conversation("MARY_SKELLY_POST_FROG_FIGHT", NpcID.MARY_SKELLY)

    MARY_SKELLY_SWAMPS = Conversation("MARY_SKELLY_SWAMPS", NpcID.MARY_SKELLY)

    MARY_AND_HEAD_AT_GATE = Conversation("MARY_AND_HEAD_AT_GATE", NpcID.HEAD)

    MARY_AT_GATE_AFTER_LOAD = Conversation("MARY_AT_GATE_AFTER_LOAD", NpcID.MARY_SKELLY)

    HEAD_AT_GATE_AFTER_LOAD = Conversation("HEAD_AT_GATE_AFTER_LOAD", NpcID.HEAD)

    SKELEKID_GROK_AND_MARY_AT_VENTS = Conversation("SKELEKID_GROK_AND_MARY_AT_VENTS", NpcID.SKELEKID)

    MARY_AT_VENTS_AFTER_LOAD = Conversation("MARY_AT_VENTS_AFTER_LOAD", NpcID.MARY_SKELLY)

    PRE_ROBO_FIGHT = Conversation("MARY_PRE_ROBO_FIGHT", NpcID.MARY_SKELLY)

    POST_ROBO_FIGHT = Conversation("MARY_POST_ROBO_FIGHT", NpcID.MACHINE)

    MARY_AND_GROK_AT_SERVER_AFTER_LOAD = Conversation("MARY_AND_GROK_AT_SERVER_AFTER_LOAD", NpcID.MARY_SKELLY)

    MARY_SKELLY_CATACOMBS = Conversation("MARY_SKELLY_CATACOMBS", NpcID.MARY_SKELLY)

    MARY_PRE_CAVE_HORROR = Conversation("MARY_PRE_CAVE_HORROR", NpcID.MARY_SKELLY)

    MARY_DOCTOR_POST_CAVE_HORROR = Conversation("MARY_DOCTOR_POST_CAVE_HORROR", NpcID.MARY_SKELLY)

    MARY_AT_VAULT_AFTER_LOAD = Conversation("MARY_AT_VAULT_AFTER_LOAD", NpcID.MARY_SKELLY)

    DOCTOR_PRE_MEDUSA = Conversation("DOCTOR_PRE_MEDUSA", NpcID.DOCTOR)

    DOCTOR_SCORP_EPILOGUE = Conversation("DOCTOR_SCORP_EPILOGUE", NpcID.DOCTOR)

    SCORP_EPILOGUE = Conversation("SCORP_EPILOGUE", NpcID.WANDERER)

    MARY_MATHILDA_EPILOGUE = Conversation("MARY_MATHILDA_EPILOGUE", NpcID.MARY_SKELLY)

    # TODO - these have been cut
    MARY_SKELLY_INTRO = Conversation("MARY_SKELLY_INTRO", NpcID.MARY_SKELLY)

    MACHINE_INTRO = Conversation("MACHINE_INTRO", NpcID.MACHINE)

    @staticmethod
    def get_all():
        for c in _ALL_CONVERSATIONS:
            yield _ALL_CONVERSATIONS[c]


class ConversationFactory:

    @staticmethod
    def get_dialog(conv, interact_count):
        res_list = []

        # TODO - Not used
        if conv == Conversations.MARY_SKELLY_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Oh my! Are you a... Husk? Where did you come from?"),
                    PlayerDialog("I... don't know."),
                    NpcDialog("Are there more of you? We thought your kind was... lost during, ya know..."),
                    PlayerDialog("I... don't think so. What is this place?"),
                    NpcDialog("This used to be an outpost between the Swamps the Caves, but we call it Tombtown now."),
                    NpcDialog("We've been... surviving here since Skeletris fell."),
                    PlayerDialog("..."),
                    NpcDialog("You don't remember the war?"),
                    PlayerDialog("I don't remember anything."),
                    NpcDialog("Well, it's a long story. I'm Mary by the way."),
                ]
            else:
                res_list = [
                    NpcDialog("It's nice to see a new face. It's been dreadfully boring here.")
                ]

        if conv == Conversations.MARY_SKELLY_PRE_SPIDER_FIGHT:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Oh, hello! Are you alone? Did you... come from the city? Do you know what happened? What path did you take? Is..."),
                    NpcDialog("Sorry, sorry... I'm bombarding you."),
                    NpcDialog("On any other day I'd welcome you into our outpost but... there's a little... problem right now."),
                    NpcDialog("Well maybe not that little. Sort of medium. Maybe medium-big. Anyway..."),
                    NpcDialog("A huge spider found its way in and none of us can safely fight it."),
                    NpcDialog("We've trapped it in the central chamber, waiting for it to get weak from hunger."),
                    NpcDialog("But that could take a half-cycle or longer depending on when it last fed..."),
                    NpcDialog("And meanwhile I'm stuck out here, hoping nothing worse comes out of the caves and dismantles me."),
                    NpcDialog("Do you... think you could help? You must be tough as nails, coming all the way here by yourself."),
                    NpcDialog("It's strong, but not very fast. The best way to fight it is to attack while it's resting and step away while it's active."),
                    NpcDialog("That way, you can deal damage without being counterattacked, and it will waste its energy chasing you."),
                    NpcDialog("Does that make sense? You'll know it's resting when you see Zzz's above its head."),
                    NpcDialog("It's right through that door. Thank you, survivor.")
                ]
            else:
                res_list = [
                    NpcDialog("Remember, hit and step away. It's the best way to fight slower creatures.")
                ]

        if conv == Conversations.MARY_SKELLY_POST_SPIDER_FIGHT:
            if interact_count == 0:
                res_list = [
                    NpcDialog("You're quite a fighter! Thank you so much! You aren't hurt, are you?"),
                    NpcDialog("Did you meet the others? Not everyone is here to thank you but you've done a great service for us today."),
                    NpcDialog("And... I... wonder if you could help with something else too..."),
                    NpcDialog("The animals... they weren't always like this, you know."),
                    NpcDialog("They became aggressive 4 cycles ago, around the same time we lost contact with Skeletris."),
                    NpcDialog("And since then, we haven't received a single message or traveler from the city."),
                    NpcDialog("There's a path, through the swamps to the north, but it's too dangerous for any of us."),
                    NpcDialog("We've already... lost someone, trying to pass through..."),
                    NpcDialog("If we can't reconnect, we'll eventually run out of supplies here and go dormant."),
                    NpcDialog("Would you help guide us to the city? We'll follow behind and assist you on the journey."),
                    NpcDialog("What do you say?")
                ]
            else:
                res_list = [
                    NpcDialog("The path is just north of here, through the swamps."),
                    NpcDialog("You're our only hope, survivor.")
                ]

        if conv == Conversations.MARY_CLONING_EXPLANATION:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Oh, and feel free to use our cloning machine if you like."),
                    NpcDialog("Just in case... well, ya know."),
                    NpcDialog("No pressure.")
                ]
            else:
                res_list = [
                    NpcDialog("It's ok if you don't want to.")
                ]

        if conv == Conversations.MARY_POST_CLONING_NO_DEATHS_YET:
            if interact_count == 0:
                res_list = [
                    NpcDialog("That wasn't so bad, was it?"),
                    NpcDialog("I hope it goes without saying, but if anything goes wrong on this adventure..."),
                    NpcDialog("I'll do everything I can to bring you back, ok?")
                ]
            else:
                res_list = [
                    NpcDialog("We should probably get moving.")
                ]

        if conv == Conversations.MARY_POST_CLONING_WITH_DEATHS:

            res_list = [
                NpcDialog("Welcome back. Do you still remember me?"),
                NpcDialog("You... took such a beating back there. I'm sorry for putting you up to this."),
                NpcDialog("I made sure to collect all your gear... and limbs, though."),
                NpcDialog("I'm glad to have you back.")
            ]

        if conv == Conversations.MARY_SKELLY_SWAMPS:
            if interact_count == 0:
                res_list = [
                    NpcDialog("You wouldn't be able to tell now, but these swamps used to be a popular place for picnics and hikes."),
                    NpcDialog("City skeletons would come through here all the time, and it was our job at the outpost to make sure none of them accidentally wandered into the caves."),
                    NpcDialog("Getting lost was the biggest danger back then. Not like now. It's so violent now.")
                ]
            else:
                res_list = [
                    NpcDialog("Anyways, we should get moving.")
                ]

        if conv == Conversations.MARY_SKELLY_PRE_FROG_FIGHT:
            if interact_count == 0:
                res_list = [
                    NpcDialog("The gate to the city is behind this chamber."),
                    NpcDialog("The monster behind this door... it dismantled... someone important to me."),
                    NpcDialog("If you see any stray bones in there... well just be careful with them, ok?"),
                    NpcDialog("Good luck, survivor.")
                ]
            else:
                res_list = [
                    NpcDialog("Good luck, survivor.")
                ]

        if conv == Conversations.MARY_SKELLY_POST_FROG_FIGHT:
            res_list = [
                NpcDialog("No bones, no weapons, not a trace of her. It doesn't add up."),
                NpcDialog("But thank you. You're a true warrior, and you've given us hope."),
                NpcDialog("The city gate is up ahead. I don't know what we'll find on the other side."),
            ]

        if conv == Conversations.MARY_AND_HEAD_AT_GATE:
            if interact_count == 0:
                res_list = [
                    NpcDialog("AHH! HELP! They took my BONES! MY BONES.", npc_id=NpcID.HEAD),
                    NpcDialog("Who did this? Where are the guards?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("I'm so NUMB. So UNFEELING. So EMPTY. My BONES...", npc_id=NpcID.HEAD),
                    NpcDialog("What happened to your bones?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Those ungrateful CREATURES. Attacked the city. Systems failed. Bones, STOLEN. Discarded. DISMANTLED", npc_id=NpcID.HEAD),
                    NpcDialog("The animals did this to you?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Animals, the UNDEAD. And some... other BEASTS. Never seen before. Overwhelmed us. Took my BONES, took their SKULLS...", npc_id=NpcID.HEAD),
                    NpcDialog("The whole city fell? How could that.. even happen?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Need my bones... Where are my BONES...?", npc_id=NpcID.HEAD),
                    NpcDialog("We're going to try to find your bones, ok? We're going to fix this.", npc_id=NpcID.MARY_SKELLY)
                ]
            else:
                res_list = [
                    NpcDialog("Where are my BONES? My precious bones...", npc_id=NpcID.HEAD),
                    NpcDialog("We should get moving. There's nothing we can do for him here.", npc_id=NpcID.MARY_SKELLY)
                ]

        if conv == Conversations.MARY_AT_GATE_AFTER_LOAD:
            res_list = [
                NpcDialog("Glad to have you back, survivor.")
            ]

        if conv == Conversations.HEAD_AT_GATE_AFTER_LOAD:
            res_list = [
                NpcDialog("Where are my BONES? My precious bones...", npc_id=NpcID.HEAD)
            ]

        if conv == Conversations.MARY_AT_VENTS_AFTER_LOAD:
            res_list = [
                NpcDialog("Whew, that one looked painful.", npc_id=NpcID.MARY_SKELLY)
            ]

        if conv == Conversations.SKELEKID_GROK_AND_MARY_AT_VENTS:
            if interact_count == 0:
                res_list = [
                    NpcDialog("K-keep your voice down... sound carries through the vents.", npc_id=NpcID.SKELEKID),
                    NpcDialog("We're from Outpost 53. What happened to the city? Where is everybody?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("We were hoping you could tell us. We've been hiding since the violence started.", npc_id=NpcID.GROK),
                    NpcDialog("We know what this was - it was a rebellion. An uprising against the Skeletons, we heard the whole thing.", npc_id=NpcID.SKELEKID),
                    NpcDialog("It was a coordinated attack. They moved from sector to sector, dismantling us like insects.", npc_id=NpcID.SKELEKID),
                    NpcDialog("The animals and the lesser undeads, they wanted the city for themselves so they took it. Somehow.", npc_id=NpcID.SKELEKID),
                    NpcDialog("We don't know who organized this. The animals were crazed - you could see it in their eyes.", npc_id=NpcID.GROK),
                    NpcDialog("The wildlife in the swamp were the same way. Aggressive, all of the sudden.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Well - whoever it was, they managed to hack the B.O.S.S. mainframe and turn it against us.", npc_id=NpcID.SKELEKID),
                    NpcDialog("The doors, weapons, communication systems - it was all locked down. Until the enemy needed to use them.", npc_id=NpcID.SKELEKID),
                    NpcDialog("We should find the mainframe. Maybe there will be more clues there.", npc_id=NpcID.MARY_SKELLY)
                ]
            else:
                res_list = [
                    NpcDialog("We should find the mainframe.", npc_id=NpcID.MARY_SKELLY)
                ]

        if conv == Conversations.PRE_ROBO_FIGHT:
            if interact_count == 0:
                res_list = [
                    NpcDialog("This is the place, right?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("The mainframe is right through there. Be careful though - we have no idea what's been done to it.", npc_id=NpcID.GROK),
                    NpcDialog("We just need to access the server logs and get out. Then we'll know who was behind this and how to fight back.", npc_id=NpcID.SKELEKID),
                    NpcDialog("And hey, it might not even be that dangerous. It's just a computer after all.", npc_id=NpcID.GROK),
                    NpcDialog("Well, there's only one way to find out.", npc_id=NpcID.MARY_SKELLY),
                ]
            else:
                res_list = [
                    NpcDialog("Good luck, survivor. We're all counting on you.", npc_id=NpcID.MARY_SKELLY),
                ]

        if conv == Conversations.POST_ROBO_FIGHT:
            robo_version = Utils.python_version_string()  # lol

            if interact_count == 0:
                res_list = [
                    NpcDialog("Wow - that thing would have crushed me with one step. Nice moves back there.", npc_id=NpcID.GROK),
                    NpcDialog("You said it was just a computer! What the hell was that?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog(">> B.O.S.S. DEFENSE FORM\n>> Version {}".format(robo_version), npc_id=NpcID.ROBO),
                    NpcDialog("It's still online?! It's listening to us?", npc_id=NpcID.SKELEKID),
                    NpcDialog("Who hacked you? Who attacked the city? Why didn't you protect us?", npc_id=NpcID.SKELEKID),
                    NpcDialog(">> Running Security Checks....\n" +
                              ">> Result: 59/59 PASSED\n" +
                              ">> No illicit activity detected.", npc_id=NpcID.ROBO),
                    NpcDialog("Then why didn't you PROTECT us?", npc_id=NpcID.SKELEKID),
                    NpcDialog(">> Scanning...\n" +
                              ">> 96.2% of citizens are protected.", npc_id=NpcID.ROBO),
                    NpcDialog("It thinks they're protected? But no one is even here.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Computer, where is everyone?", npc_id=NpcID.GROK),
                    NpcDialog(">> Skeletris Catacombs", npc_id=NpcID.ROBO),
                    NpcDialog("The catacombs? That's where the city's fungus reserves are kept. Why would it move everyone down there?", npc_id=NpcID.GROK),
                    NpcDialog("Maybe it malfunctioned?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Stupid machine! Why did you move everyone down there? You destroyed the city!", npc_id=NpcID.SKELEKID),
                    NpcDialog(">> Citizens were moved to satisfy the PRIMARY GOALS.", npc_id=NpcID.ROBO),
                    NpcDialog("What are the primary goals?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog(">> 1. Protect Citizens from Harm\n" +
                              ">> 2. Maintain Order and Justice\n" +
                              ">> 3. Increase Gross Assets of Skeletris"),
                    NpcDialog("Those seem... reasonable?", npc_id=NpcID.SKELEKID),
                    NpcDialog("I wonder... computer, how have the city's gross assets changed over the past eight cycles?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog(">> Cycle 1532: +3.9%\n" +
                              ">> Cycle 1533: +4.2%\n" +
                              ">> Cycle 1534: +3.7%\n" +
                              ">> Cycle 1535: +3.9%", npc_id=NpcID.ROBO),
                    NpcDialog(">> Cycle 1536: +45,023.2%\n" +
                              ">> Cycle 1537: +113,003,203.3%\n" +
                              ">> Cycle 1538: +5.2%\n" +
                              ">> Cycle 1539: +4.9%", npc_id=NpcID.ROBO),
                    NpcDialog("Those numbers are impossible. Mushrooms don't grow that fast.", npc_id=NpcID.GROK),
                    NpcDialog("It was... raising revenue? Those spikes happened immediately before and during the attacks.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("So it did malfunction?! How could our leaders let this happen?", npc_id=NpcID.SKELEKID),
                    NpcDialog("Let's search the catacombs. If the computer is telling the truth that's where everyone is being held.", npc_id=NpcID.MARY_SKELLY),
                ]
            else:
                res_list = [
                    NpcDialog("We should search the catacombs.", npc_id=NpcID.MARY_SKELLY),
                ]

        if conv == Conversations.MARY_AND_GROK_AT_SERVER_AFTER_LOAD:
            res_list = [
                NpcDialog("Whew, I'm glad that worked. Are you ok?", npc_id=NpcID.MARY_SKELLY),
                NpcDialog("You lucked out - we almost didn't find enough material to regenerate you.", npc_id=NpcID.GROK),
                NpcDialog("Glad to see you back in one piece.", npc_id=NpcID.GROK)
            ]

        if conv == Conversations.MARY_AT_VAULT_AFTER_LOAD:
            res_list = [
                NpcDialog("Hi again. Let's finish this.")
            ]

        if conv == Conversations.MARY_SKELLY_CATACOMBS:
            if interact_count == 0:
                res_list = [
                    NpcDialog("The bones... they're everywhere. Scattered like garbage..."),
                    NpcDialog("How could this happen...?"),
                ]
            else:
                res_list = [
                    NpcDialog("And... where are the heads?")
                ]

        if conv == Conversations.MARY_PRE_CAVE_HORROR:
            if interact_count == 0:
                res_list = [
                    NpcDialog("I... I found her. My wife."),
                    NpcDialog("I'm going to rebuild her. And then the others."),
                    NpcDialog("They're in agony. I can't leave them like this."),
                    NpcDialog("The central vault is up ahead. Whatever's in there... the computer thinks it's more valuable than the city itself."),
                    NpcDialog("I don't know what that means, but be careful."),
                    NpcDialog("Thank you for everything, survivor."),
                ]
            else:
                res_list = [
                    NpcDialog("Thank you, survivor.")
                ]

        if conv == Conversations.MARY_DOCTOR_POST_CAVE_HORROR:
            if interact_count == 0:
                res_list = [
                    NpcDialog("It's not enough, you know. No matter how many fights you win, the fungus will rebuild.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Everything that breathes is already infected. The spread can't be stopped like this.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Who the hell are you? Why are you following us?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("I knew this would happen. These systems were NOT designed to carry out genetic experiments. But they wouldn't listen.", npc_id=NpcID.DOCTOR),
                    NpcDialog("I tried to stop them. I knew they wouldn't control it. This all could have been avoided.", npc_id=NpcID.DOCTOR),
                    NpcDialog("What are you talking about?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Many, many, cycles ago, the city wanted to modernize and automate certain tasks.", npc_id=NpcID.DOCTOR),
                    NpcDialog("So my team was tasked to build a supercomputer to meet those needs.", npc_id=NpcID.DOCTOR),
                    NpcDialog("We called it the \"Benevolent Organization System for Skeletris.\" And it was marvelous.", npc_id=NpcID.DOCTOR),
                    NpcDialog("B.O.S.S. was always learning, observing, and improving. It become so clever...", npc_id=NpcID.DOCTOR),
                    NpcDialog("At first, it was only used for basic civic duties, like energy distribution, waste disposal, and traffic coordination.", npc_id=NpcID.DOCTOR),
                    NpcDialog("But it didn't stop there. The city wanted to use B.O.S.S. for more serious things too, like helping to protect the city.", npc_id=NpcID.DOCTOR),
                    NpcDialog("They used it to predict the movement of criminals, send out automatic threat alerts, and contain fires and gas leaks.", npc_id=NpcID.DOCTOR),
                    NpcDialog("And it worked pretty well. But it made mistakes. Mostly minor, but some were deadly.", npc_id=NpcID.DOCTOR),
                    NpcDialog("I tried to get them to reduce the scope of the AI's responsibilities, but they always refused.", npc_id=NpcID.DOCTOR),
                    NpcDialog("They would just patch out the most recent issue, and claim that overall it was still doing better than any team of skeletons could.", npc_id=NpcID.DOCTOR),
                    NpcDialog("It was a mockery of the safety protocols we outlined.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Eventually, they enlisted it to help manage the city's finances, which was deeply unpopular at the time.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Giving such a sacred and important job to a computer was almost.. blasphemous.  Citizens resisted at first.", npc_id=NpcID.DOCTOR),
                    NpcDialog("But there it remained, watching over the fungus reserves, caring for them, breeding them.", npc_id=NpcID.DOCTOR),
                    NpcDialog("And, of course, the growth rates were better than the city had ever seen.", npc_id=NpcID.DOCTOR),
                    NpcDialog("It started inventing new species of mushrooms. More exotic and beautiful than we ever could. Revenue soared, and complaints died down.", npc_id=NpcID.DOCTOR),
                    NpcDialog("And then... well... it found the perfect formula.", npc_id=NpcID.DOCTOR),
                    NpcDialog("It created a parasite.", npc_id=NpcID.DOCTOR),
                    NpcDialog("A tiny spore that enters the respiratory system, attaches to the brain stem, and lays dormant waiting for the signal.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Skeletons are immune, of course, because they don't have brains. But almost everything with a central nervous system is susceptible.", npc_id=NpcID.DOCTOR),
                    NpcDialog("The parasite spread silently. And rapidly.", npc_id=NpcID.DOCTOR),
                    NpcDialog("After a certain... gestation period, the infected would come down here and merge their flesh into that... thing, and become one with it.", npc_id=NpcID.DOCTOR),
                    NpcDialog("The resulting \"mushroom\", if you could even call it that, was off the scales. B.O.S.S. thought it was incredibly valuable.", npc_id=NpcID.DOCTOR),
                    NpcDialog("But... why did it let them attack us, the skeletons? Wasn't the primary objective to protect us?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("It was. But you can't restrict something with such power and... creativity.", npc_id=NpcID.DOCTOR),
                    NpcDialog("It knew the city would shut this plan down when they realized what was happening. So it found a loophole.", npc_id=NpcID.DOCTOR),
                    NpcDialog("When the parasite first activates, the host obsessively pursues one goal: Dismantle skeletons, and bring their skulls here - unharmed.", npc_id=NpcID.DOCTOR),
                    NpcDialog("And it worked, as you can see.", npc_id=NpcID.DOCTOR),
                    NpcDialog("So what now? How do we reverse this?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("The activation signal - it wasn't released by B.O.S.S. directly. It's a pheromone. Something biological.", npc_id=NpcID.DOCTOR),
                    NpcDialog("If we destroy the source, the parasite will become dormant again, and the infected will return to normal.", npc_id=NpcID.DOCTOR),
                    NpcDialog("Where is the signal coming from?", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("It's coming from the Undergrowth. Where the city's rot is kept. Destroy that source, and the hivemind will fall.", npc_id=NpcID.DOCTOR),
                    NpcDialog("It sounds like a plan.", npc_id=NpcID.MARY_SKELLY)
                ]
            else:
                res_list = [
                    NpcDialog("You must destroy the source of the pheromone. It's our only hope.", npc_id=NpcID.DOCTOR)
                ]

        if conv == Conversations.DOCTOR_PRE_MEDUSA:
            if interact_count == 0:
                res_list = [
                    NpcDialog("I've traced the signal to this room. Whatever's in there, it's controlling the rest of them."),
                    NpcDialog("Let's end this nightmare, right here, right now. For Skeletris!")
                ]
            else:
                res_list = [
                    NpcDialog("Good luck, friend.")
                ]

        if conv == Conversations.DOCTOR_SCORP_EPILOGUE:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Look - it's working."),
                    NpcDialog("See? It's acting normal. I think. It's not attacking us, at least."),
                    NpcDialog("After the pheromone dissipates from the city and surrounding areas, it should become safe to start rebuilding."),
                    NpcDialog("We'll get the city, and its inhabitants, up and running in no time."),
                    NpcDialog("Thank you, hero. They'll build statues to commemorate this moment, I'm sure of it.")
                ]
            else:
                res_list = [
                    NpcDialog("I might return to public service. Make sure this kind of thing never happens again.")
                ]

        if conv == Conversations.SCORP_EPILOGUE:
            res_list = [
                NpcDialog("Grrr grrr. Grrr...", npc_id=NpcID.WANDERER)
            ]

        if conv == Conversations.MARY_MATHILDA_EPILOGUE:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Look, she's fixed! Well, mostly...", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("Hi! I'm Mathilda. Mary's been telling me all about you. And I saw some of it for myself too.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("The way you fought that huge monster was unlike anything I'd ever seen! You use your weapons with such deadly efficiency. It's incredible.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("And without you, I would be sitting on a shelf somewhere right now.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("I owe you a debt of gratitude, adventurer. Thank you.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("Listen, we've been talking - and if you're up for it, we'd like you to come live with us at Tombtown.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("You can test out Mathilda's weapons as much as you like, and we can explore the caves together and try to figure out where you really came from.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("We'll carve out a room for you, and we'd be a family.", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("We'd love to have you! Take some time to think it over.", npc_id=NpcID.MATHILDA_INCOMPLETE)
                ]
            else:
                res_list = [
                    NpcDialog("Oh - and by the way, that frog in the swamps didn't dismantle me. Contrary to what SOMEONE's been apparently telling everyone.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("Oh no, here we go...", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("I wouldn't lose to something that SLOW! I'm a trained fighter. I just slipped past it!", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("I just assumed...", npc_id=NpcID.MARY_SKELLY),
                    NpcDialog("I was AMBUSHED in the city! Hundreds of creatures descended on me in an instant. It was a bloodbath.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("After cutting dozens of them down, my blade was still sharp, but my strength ran out. And so I fell. A warrior, defeated.", npc_id=NpcID.MATHILDA_INCOMPLETE),
                    NpcDialog("I believe you <3", npc_id=NpcID.MARY_SKELLY),
                ]

        # TODO - not used
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
                    NpcDialog("Welcome to Skeletris! I'm Machine, your virtual guide."),
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
                    NpcDialog("Hello there! Thank you for taking care of that spider!"),
                    NpcDialog("We haven't met before, have we? I'm Beanskull. What's your name?"),
                    NpcDialog("Well... no matter. Welcome to Tombtown! The final outpost before Skeletris."),
                    NpcDialog("Although... I don't believe we've heard from them in a while."),
                    NpcDialog("It's no matter though. I don't need their hi-tech gadgets or artificial what-cha-ma-call-it to grow my tomatoes."),
                    NpcDialog("The real problem is the wildlife. Very dangerous now. Makes it risky to gather seeds."),
                    NpcDialog("Something strange is going on out there. I can feel it in my bones.")
                ]
            else:
                res_list = [
                    NpcDialog("I'd offer you a tomato, but these won't be ready for at least another half-cycle."),
                    NpcDialog("Come back soon, and you can have a whole basketful! They're to die for, believe me.")
                ]

        if conv == Conversations.MAYOR_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("What was all that commotion out there? Spiders again?"),
                    NpcDialog("I keep telling our citizens to close the doors after themselves but they refuse to listen! Can you believe that?"),
                    NpcDialog("But never mind that! Welcome to Tombtown! I'm Patches, the Mayor."),
                    NpcDialog("Say... perhaps you'd like to open a savings account!"),
                    NpcDialog("The activation fee is just a couple of portabellos, and our growing cellar is perfect for any spore, common or exotic!"),
                    NpcDialog("Up to 4% interest after a cycle or two is practically guaranteed! What do you say?"),
                    NpcDialog("Oh, unless, you don't seem to have any... Nevermind. Well. Better days ahead then, friend.")
                ]
            else:
                res_list = [
                    NpcDialog("A strong economy makes a strong town, is what I always say."),
                    NpcDialog("Central bank or not, we'll be ready when the market returns.")
                ]

        if len(res_list) > 0:
            # setting sprites here just to avoid endless clutter above
            for dia in res_list:
                if isinstance(dia, NpcDialog):
                    if dia.sprites is None and dia.npc_id is not None:
                        dia.sprites = get_template(dia.npc_id).get_dialog_sprites()
                    elif dia.sprites is None and dia.npc_id is None:
                        dia.npc_id = conv.get_npc_id()
                        dia.sprites = get_template(conv.get_npc_id()).get_dialog_sprites()

            return dialog.Dialog.link_em_up(res_list)
        else:
            print("WARN: no dialog defined for conv_id: {}".format(conv.get_id()))
            return None


class NpcTradeProtocol:

    def accepts_trade(self, item):
        return True

    def do_trade(self, item):
        return [item]

    def get_explain_dialog(self, npc_id):
        return dialog.NpcDialog("You give me an item, I give it back. Simple.", npc_id=npc_id)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Here's your item! Have a nice day.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        return dialog.NpcDialog("I hope you're enjoying the item!", npc_id=npc_id)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("I can't accept that type of item.", npc_id=npc_id)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("No more trades today. Sorry!", npc_id=npc_id)


class NpcMirrorTradeProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.mirror()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Need some help? If you give me an Artifact, I'll flip it for you.", npc_id=npc_id),
             dialog.NpcDialog("Interested? It's probably easier to just show you.", npc_id=npc_id)]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("No, no. Not that kind of item. It needs to be more... " +
                                "how do I describe it... cubelike? An Artifact.", npc_id=npc_id)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Mirror service complete! Hope this helps.", npc_id=npc_id)

    def get_no_more_trades_dialog(self, npc_id):
        d = [dialog.NpcDialog("Sorry! I can't do any more right now.", npc_id=npc_id),
             dialog.NpcDialog("It's hard work, you know, rotating things out of this 2D plane. You have to push REALLY hard.", npc_id=npc_id),
             dialog.NpcDialog("And sometimes it doesn't quite work, and things get... weird...", npc_id=npc_id),
             dialog.NpcDialog("Anyways, I'm glad that didn't happen this time!", npc_id=npc_id)]
        return dialog.Dialog.link_em_up(d)


class NpcPotionProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CONSUMABLE in item.get_type().get_tags()

    def do_trade(self, item):
        my_level = item.get_level()
        drop_as_level = my_level + 5

        import src.items.itemgen as itemgen

        candidates = itemgen.PotionTemplates.all_templates(for_level=drop_as_level)

        # it feels bad to get the same potion back
        candidates = [c for c in candidates if c.name != item.get_title()]

        if len(candidates) > 0:
            # rare ones are equally likely as common ones
            template = random.choice(candidates)
            res_item = itemgen.PotionItemFactory.gen_item(drop_as_level, template=template)
            if res_item is not None:
                return [res_item]

        print("WARN: failed to generate a potion to trade for {}".format(item.get_title()))
        return [item]

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("I can't accept that. Only potions.", npc_id=npc_id)

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Here's the deal. You give me a potion, and I'll give you a new one back.", npc_id=npc_id),
             dialog.NpcDialog("How about it?", npc_id=npc_id)]
        return dialog.Dialog.link_em_up(d)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Here you go.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        return dialog.NpcDialog("Oh, by the way... don't operate any heavy machinery after drinking that.", npc_id=npc_id)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Hey, hey. I think you've had enough.", npc_id=npc_id)


class NpcRerollCubesProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_cubes()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Shh! Listen closely. I can... reshape things. Artifacts. I'll show you.", npc_id=npc_id),
             dialog.NpcDialog("Come on. Give me one. Quickly.", npc_id=npc_id)]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Stop screwing around! An Artifact! Give me an Artifact.", npc_id=npc_id)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Look at that! Completely reforged. Does it fit better now?", npc_id=npc_id)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Sorry. I'm spent. Come back another time.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        d = [dialog.NpcDialog("Enjoying that item I gave you?"),
             dialog.NpcDialog("No need to thank me. I do accept tips though. And positive reviews are appreciated. " +
                              "And have you seen my twitter?", npc_id=npc_id),
             dialog.PlayerDialog("Yeah! yeah. I'll check it out. I gotta... get going, though, ya know."),
             dialog.NpcDialog("Oh, right, right. Very busy. You will check it out though? " +
                              "Let me just get you the URL...", npc_id=npc_id),
             dialog.PlayerDialog("Yeah! No worries, I'll find it. Thanks! Love the item. Bye!")]
        return dialog.Dialog.link_em_up(d)


class NpcRerollStatsProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_stats()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Need some help? Give me an Artifact, and I'll re-roll the stats for you.", npc_id=npc_id),
             dialog.NpcDialog("It's a bit unpredictable, I'm afraid! But I promise to do my best!", npc_id=npc_id),
             dialog.NpcDialog("Care to give it a shot?", npc_id=npc_id)
            ]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Oh no, I've confused you. The item needs to be an Artifact.", npc_id=npc_id)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Here you go! I hope you like it.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        d = [dialog.NpcDialog("This process is a lot like growing tomatoes, you know. You never know what to expect.", npc_id=npc_id),
             dialog.NpcDialog("Well... unless you're expecting a tomato. You always get a tomato when you plant tomatoes.", npc_id=npc_id),
             dialog.NpcDialog("But actually, this ONE time, I planted what I thought were tomato seeds, but then when it came time to harvest, it turned out they were RADISHES!", npc_id=npc_id),
             dialog.NpcDialog("That was some of the worst spaghetti sauce I've ever had, let me tell you.", npc_id=npc_id)
             ]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("I can't do any more right now I'm afraid. But if you see me around, don't hesitate to say hello!", npc_id=npc_id)


class NpcRerollArtProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_art()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Hey, you there! Hey! You! I've got something for you.", npc_id=npc_id),
             dialog.NpcDialog("I can do something quite special. Something no one else can do. Something few can even wrap their minds around.", npc_id=npc_id),
             dialog.NpcDialog("Just give me your best, favorite, Artifact, and then you'll see.", npc_id=npc_id),
             ]
        return dialog.Dialog.link_em_up(d)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Ah-ha, see? Look at that. Spectacular.", npc_id=npc_id)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Are you deaf? It's gotta be an artifact. This won't work.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        d = [dialog.PlayerDialog("Did anything... change?"),
             dialog.NpcDialog("Ha, ha... you're joking, right? Look at the color! " +
                              "The designs! It's totally different!", npc_id=npc_id),
             dialog.PlayerDialog("Oh. Hmm. I guess... I don't remember how it used to look."),
             dialog.NpcDialog("What are you, a goldfish? Two seconds pass and everything goes \"poof\"? "
                              "No one cares about the details anymore.", npc_id=npc_id),
             dialog.PlayerDialog("What's a goldfish?"),
             dialog.NpcDialog("...", npc_id=npc_id),
             dialog.NpcDialog("Just astonishing, you turned out to be. ", npc_id=npc_id)
            ]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Only one per customer! I'm very busy you know.", npc_id=npc_id)


class NpcItemThatFitsProtocol(NpcTradeProtocol):

    def __init__(self):
        NpcTradeProtocol.__init__(self)
        self._chance_to_shrink_item = 0.25

    def accepts_trade(self, item):
        return self._is_valid_item_type(item) and self._is_enough_space_for_new_item(item)

    def _is_valid_item_type(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def _is_enough_space_for_new_item(self, item):
        return len(self._get_empty_equipment_grid_cell_clusters(min_size=5)) > 0

    def _get_empty_equipment_grid_cell_clusters(self, min_size=5):
        """
        returns: list of groups of connected empty cells in player's equipment grid (aka 'cell clusters').
        min_size: if a region has less than min_size cells, it's discarded.
        """
        player_equip_grid = gs.get_instance().player_state().inventory().get_equip_grid()

        empty_cells = []

        for x in range(0, player_equip_grid.w()):
            for y in range(0, player_equip_grid.h()):
                if player_equip_grid.item_at_position((x, y)) is None:
                    empty_cells.append((x, y))

        clusters = []

        # n^2, don't care. the grid is 5x5
        for cell in empty_cells:
            touching_clusters = []
            for cluster in clusters:
                if any([Utils.dist_manhattan(cell, c) == 1 for c in cluster]):
                    touching_clusters.append(cluster)

            if len(touching_clusters) > 1:
                mega_cluster = [cell]
                for cluster in touching_clusters:
                    clusters.remove(cluster)
                    mega_cluster.extend(cluster)
                clusters.append(mega_cluster)

            elif len(touching_clusters) == 1:
                touching_clusters[0].append(cell)

            else:
                # start a new one
                clusters.append([cell])

        return [cluster for cluster in clusters if len(cluster) >= min_size]

    def _gen_rand_n_cubes(self, max_n_cubes=7):
        if max_n_cubes < 5 or max_n_cubes > 7:
            raise ValueError("illegal argument max_n_cubes: {}".format(max_n_cubes))

        if max_n_cubes == 5 or random.random() > self._chance_to_shrink_item:
            # leave the number of cubes unmodified
            return max_n_cubes
        else:
            choices = [x for x in range(5, max_n_cubes)]
            return random.choice(choices)

    def do_trade(self, item):
        item_n_cubes = min(len(item.cubes), 7)
        empty_clusters = self._get_empty_equipment_grid_cell_clusters(min_size=5)

        if len(empty_clusters) == 0:
            print("ERROR: bad state, no empty cell clusters in equipment grid...")
            return [item]

        # can't generate an item of size n unless there's a cluster that's big enough
        max_cluster_size = max([len(cluster) for cluster in empty_clusters])

        n_cubes = self._gen_rand_n_cubes(max_n_cubes=min(item_n_cubes, max_cluster_size))

        big_enough_clusters = [cluster for cluster in empty_clusters if len(cluster) >= n_cubes]

        cluster = list(random.choice(big_enough_clusters))
        random.shuffle(cluster)

        # now we just need to generate an n-cube item that fits in our cluster
        new_cubes = [cluster.pop()]

        while len(new_cubes) < n_cubes:
            did_expand = False
            for c in new_cubes:
                # trying to 'expand' off of c to fill the region.
                c_n = [n for n in Utils.neighbors(c[0], c[1])]
                random.shuffle(c_n)
                for n in c_n:
                    if n in cluster:
                        new_cubes.insert(0, n)  # want to keep growing off this one if possible
                        cluster.remove(n)       # makes the result more "snaky"
                        did_expand = True
                        break

                if did_expand:
                    break  # start the process over

            if not did_expand:
                raise ValueError("failed to expand to fill cluster...?")

        if len(new_cubes) != n_cubes:
            raise ValueError("res_cubes has incorrect size={}, expected={}".format(len(new_cubes), n_cubes))

        new_cubes = cubeutils.CubeUtils.clean_cubes(new_cubes)

        import src.items.itemgen as itemgen

        new_stats = {}  # stat_type -> value
        for applied_stat in item.all_applied_stats():
            if applied_stat.get_type() not in new_stats:  # there shouldn't be dupes, but nuke them just in case.
                new_stats[applied_stat.get_type()] = applied_stat.get_value()

        # might need to delete stats if we lost cubes.
        deleted_some_stats = False
        n_stats_to_remove = len(new_stats) - balance.max_stats_for_n_cubes(len(new_cubes))

        if n_stats_to_remove > 0:
            core_stats = [s for s in new_stats if s in itemgen.CORE_STATS]
            if len(core_stats) > 0:
                protected_core_stat = random.choice(core_stats)
            else:
                protected_core_stat = None  # weird but ok...

            deletable_stat_types = [s for s in new_stats if s != protected_core_stat]

            while n_stats_to_remove > 0 and len(deletable_stat_types) > 0:
                to_del = random.choice(deletable_stat_types)
                deletable_stat_types.remove(to_del)
                del new_stats[to_del]
                n_stats_to_remove -= 1
                deleted_some_stats = True

        # XXX special case-y stuff to deal with holy artifact stat doubling / un-doubling
        was_holy = cubeutils.CubeUtils.is_holy(item.cubes)
        is_holy = cubeutils.CubeUtils.is_holy(new_cubes)
        if was_holy != is_holy:
            for stat_type in new_stats:
                new_stats[stat_type] = itemgen.StatCubesItemFactory.modify_stat_for_holy_item(stat_type,
                                                                                              new_stats[stat_type],
                                                                                              unmodify=not is_holy)

        new_applied_stats = []
        for stat_type in new_stats:
            # we're relying on the fact that python uses an ordered dict by default to ensure
            # that these stats end up in the same order as they appear on the original item.
            new_applied_stat = itemgen.AppliedStat(stat_type, new_stats[stat_type])
            new_applied_stats.append(new_applied_stat)

        new_name = itemgen.StatCubesItemFactory.gen_name_for_stats_and_cubes(new_applied_stats, new_cubes)
        new_color = item.color if not deleted_some_stats else itemgen.StatCubesItemFactory.gen_color_for_stats(new_applied_stats)

        orig_art_types = [item.cube_art[c] for c in item.cubes if (c in item.cube_art and item.cube_art[c] != 0)]
        new_cube_art = itemgen.StatCubesItemFactory.gen_cube_art_for_stats_and_cubes(new_applied_stats, new_cubes,
                                                                                     art_types=orig_art_types)

        new_item = itemgen.StatCubesItem(new_name, item.get_level(), new_applied_stats, new_cubes, new_color, cube_art=new_cube_art)

        return [new_item]

    def get_explain_dialog(self, npc_id):
        pct_modify_stats = "{:.1%}".format(self._chance_to_shrink_item)
        d = [dialog.NpcDialog(">> Welcome to PrintBot!\n" +
                              ">> Insert an artifact to get started.", npc_id=npc_id),

             dialog.NpcDialog(">> Instructions:\n" +
                              ">> 1. Make space in your equipment grid.\n" +
                              ">> 2. Insert an artifact.", npc_id=npc_id),

             dialog.NpcDialog(">> Result: The artifact will be re-printed so that it fits inside your grid.", npc_id=npc_id),

             dialog.NpcDialog(">> Warning: There is a {} chance that the artifact's stats will be modified by the procedure.".format(pct_modify_stats),
                              npc_id=npc_id)
            ]
        return dialog.Dialog.link_em_up(d)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog(">> Print completed successfully.", npc_id=npc_id)

    def get_wrong_item_dialog(self, npc_id, item):
        if not self._is_valid_item_type(item):
            return dialog.NpcDialog(">> ERROR: PrintBot is not compatible with this item. Only artifacts are supported.",
                                    npc_id=npc_id)
        elif not self._is_enough_space_for_new_item(item):
            return dialog.NpcDialog(">> ERROR: Not enough space. Clear some room in your equipment grid to proceed.", npc_id=npc_id)
        else:
            return dialog.NpcDialog(">> ERROR: Unexpected error.", npc_id=npc_id)

    def get_post_success_dialog(self, npc_id):
        d = [dialog.NpcDialog(">> Please rate the service you received:\n" +
                              ">>   [1] [2] [3] [4] [5] Star(s)", npc_id=npc_id),
             dialog.PlayerDialog("..."),
             dialog.NpcDialog(">> Confirming [5] star rating.\n" +
                              ">> Thank you!", npc_id=npc_id)]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog(">> ERROR: Toner cartridge is not genuine. Please install a genuine PrintBot toner cartridge to proceed.", npc_id=npc_id)


class NpcTradeProtocols:

    IDENTITY_TRADE = NpcTradeProtocol()
    MIRROR_TRADE = NpcMirrorTradeProtocol()
    POTION_EXCHANGE = NpcPotionProtocol()
    REROLL_CUBES = NpcRerollCubesProtocol()
    REROLL_STATS = NpcRerollStatsProtocol()
    REROLL_ART = NpcRerollArtProtocol()
    ITEM_THAT_FITS = NpcItemThatFitsProtocol()


def get_template(npc_id):
    return TEMPLATES[npc_id]


def get_sprites(npc_id):
    if npc_id in TEMPLATES:
        return TEMPLATES[npc_id].get_dialog_sprites()
    else:
        print("WARN: no npc template exists for id: {}".format(npc_id))
        return None


class NpcFactory:

    @staticmethod
    def gen_convo_npcs(from_convo_ids, n, not_npc_ids=None):
        res = []

        if len(from_convo_ids) == 0:
            return []

        import src.world.entities as entities

        available_convos = [c for c in Conversations.get_all() if (c.get_id() in from_convo_ids and c.is_available())]
        random.shuffle(available_convos)

        # can't have dupes of the same NPC in the zone
        used_npc_ids = set()

        if not_npc_ids is not None:
            for npc_id in not_npc_ids:
                used_npc_ids.add(npc_id)

        while len(available_convos) > 0 and len(res) < n:
            convo = available_convos.pop()
            npc_id = convo.get_npc_id()
            if npc_id not in used_npc_ids:
                used_npc_ids.add(npc_id)
                res.append(entities.NpcConversationEntity(0, 0, get_template(npc_id), convo))
                break

        return res

    @staticmethod
    def gen_trade_npcs(level, n, not_npc_ids=None):
        res = []

        available_traders = [npc_id for npc_id in TEMPLATES if
                             get_template(npc_id).get_trade_protocol(level) is not None]

        random.shuffle(available_traders)

        import src.world.entities as entities

        # can't have dupes of the same NPC in the zone
        used_npc_ids = set()

        if not_npc_ids is not None:
            for npc_id in not_npc_ids:
                used_npc_ids.add(npc_id)

        while len(available_traders) > 0 and len(res) < n:
            npc_id = available_traders.pop()
            if npc_id not in used_npc_ids:
                used_npc_ids.add(npc_id)
                template = get_template(npc_id)
                res.append(entities.NpcTradeEntity(0, 0, template, template.get_trade_protocol(level)))

        return res

    @staticmethod
    def gen_trade_npc(npc_id, level):
        import src.world.entities as entities

        template = get_template(npc_id)
        return entities.NpcTradeEntity(0, 0, template, template.get_trade_protocol(level))

    @staticmethod
    def gen_convo_npc(npc_id, convo):
        import src.world.entities as entities

        return entities.NpcConversationEntity(0, 0, get_template(npc_id), convo)

    @staticmethod
    def gen_linked_npc(npc_id, parent_uid):
        import src.world.entities as entities

        return entities.NpcLinkedEntity(0, 0, get_template(npc_id), parent_uid)