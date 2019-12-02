
from enum import Enum
import random

import src.game.spriteref as sr
from src.game.dialog import Dialog, NpcDialog, PlayerDialog
import src.game.globalstate as gs
import src.game.dialog as dialog
import src.utils.colors as colors
from src.utils.util import Utils
import src.game.balance as balance


class NpcID(Enum):

    MAYOR = "MAYOR"
    MARY_SKELLY = "MARY_SKELLY"
    BEANSKULL = "BEANSKULL"
    GLORPLE = "GLORPLE"
    MACHINE = "MACHINE"
    DOCTOR = "DOCTOR"
    SKELEKID = "SKELEKID"
    HEAD = "HEAD"

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

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MARY_SKELLY, "Mary Skelly",
                             sr.mary_skelly_all, sr.mary_skelly_faces, ("m", colors.YELLOW))


class MayorPatchesTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MAYOR, "Mayor", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             ("p", colors.YELLOW), shadow_sprite=sr.large_shadow)

    def get_trade_protocol(self, level):
        if level >= 3:
            return NpcTradeProtocols.REROLL_ART


class BeanskullTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces, ("b", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 3:
            return NpcTradeProtocols.REROLL_STATS


class GlorpleTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.GLORPLE, "Glorple", sr.glorple_all, sr.glorple_faces, ("g", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 8:
            return NpcTradeProtocols.REROLL_CUBES


class MachineTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MACHINE, "PrintBot", sr.save_stations, sr.save_station_faces, ("P", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 8:
            return NpcTradeProtocols.ITEM_THAT_FITS


class DoctorTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.DOCTOR, "Doc", sr.doctor_all, sr.doctor_faces, ("d", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 3:
            return NpcTradeProtocols.POTION_EXCHANGE


class SkelekidTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.SKELEKID, "Skelekid", sr.skelekid_all, sr.skelekid_faces, ("s", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 3:
            return NpcTradeProtocols.MIRROR_TRADE


class HeadTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.HEAD, "Disembodied Head", sr.skull_head_all, sr.skull_head_faces, ("h", colors.YELLOW))


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
    # The "Farmer", well liked, provides food and equipment for the remaining citizens.
    # Interested in all things related to plants.

    NpcID.GLORPLE: GlorpleTemplate(),
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

    NpcID.CAVE_HORROR: CaveHorrorNpcTemplate()  # TODO - not used, it's stupid to have them talk
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
        except ValueError:
            return False


class Conversations:

    MARY_SKELLY_PRE_SPIDER_FIGHT = Conversation("MARY_SKELLY_PRE_SPIDER_FIGHT", NpcID.MARY_SKELLY)

    BEANSKULL_INTRO = Conversation("BEANSKULL_INTRO", NpcID.BEANSKULL)

    MAYOR_INTRO = Conversation("MAYOR_INTRO", NpcID.MAYOR)

    MARY_SKELLY_POST_SPIDER_FIGHT = Conversation("MARY_SKELLY_POST_SPIDER_FIGHT", NpcID.MARY_SKELLY)

    MARY_SKELLY_PRE_FROG_FIGHT = Conversation("MARY_SKELLY_PRE_FROG_FIGHT", NpcID.MARY_SKELLY)

    MARY_SKELLY_POST_FROG_FIGHT = Conversation("MARY_SKELLY_POST_FROG_FIGHT", NpcID.MARY_SKELLY)

    MARY_SKELLY_SWAMPS_1 = Conversation("MARY_SKELLY_SWAMPS_1", NpcID.MARY_SKELLY)

    MARY_AND_HEAD_AT_GATE = Conversation("MARY_AND_HEAD_AT_GATE", NpcID.HEAD)

    # TODO - these have all been cut
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

        if conv == Conversations.MARY_SKELLY_INTRO:
            if interact_count == 0:
                res_list = [
                    NpcDialog("Oh my! Are you a... Husk? Where did you come from?"),
                    PlayerDialog("I... don't know."),
                    NpcDialog("Are there more of you? We thought your kind was... lost during, ya know..."),
                    PlayerDialog("I... don't think so. What is this place?"),
                    NpcDialog("This used to be an outpost between the Swamps the Caves, but we call it Tomb Town now."),
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
                    NpcDialog("But that could take a quarter-cycle or longer depending on when it last fed..."),
                    NpcDialog("And meanwhile I'm stuck out here, hoping nothing worse comes out of the caves and dismantles me."),
                    NpcDialog("Do you... think you could help? You must be tough as nails, coming all the way here by yourself."),
                    NpcDialog("It's strong, but not very fast. The best way to fight it is to hit and step away."),
                    NpcDialog("Does that make sense? Just hit and step away. And repeat."),
                    NpcDialog("That way, you can deal damage while it's resting and it will waste its energy chasing you. Make sense?"),
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
                    NpcDialog("They became aggressive 12 cycles ago, around the same time we lost contact with Skeletris."),
                    NpcDialog("And since then, we haven't received a single message or traveler from the city."),
                    NpcDialog("There's a path, through the swamps to the north, but it's too dangerous for any of us."),
                    NpcDialog("We've already... lost some friends, trying..."),
                    NpcDialog("If we can't reconnect, we'll eventually run out of supplies here and go dormant."),
                    NpcDialog("Would you help guide us to the city? We'll follow behind and assist you on the journey."),
                    NpcDialog("What do you say?")
                ]
            else:
                res_list = [
                    NpcDialog("The path is just north of here, through the swamps."),
                    NpcDialog("You're our only hope, survivor.")
                ]

        if conv == Conversations.MARY_SKELLY_SWAMPS_1:
            res_list = [
                NpcDialog("You wouldn't be able to tell now, but these swamps used to be a popular place for picnics and hikes."),
                NpcDialog("City skeletons would come through here all the time, and it was our job at the outpost to make sure none of them accidentally wandered into the caves."),
                NpcDialog("Getting lost was the biggest danger back then. Not like now. It's so violent now.")
            ]

        if conv == Conversations.MARY_SKELLY_PRE_FROG_FIGHT:
            res_list = [
                NpcDialog("This is the gate to the city."),
                NpcDialog("The monster behind this door... it dismantled... someone important to me."),
                NpcDialog("If you see any stray bones in there... well just be careful with them, ok?"),
                NpcDialog("Good luck, survivor.")
            ]

        if conv == Conversations.MARY_SKELLY_POST_FROG_FIGHT:
            res_list = [
                NpcDialog("No bones, no weapons, not a trace of her. It doesn't add up."),
                NpcDialog("But thank you. You're a true warrior, and you've given us hope."),
                NpcDialog("This is the door to the city. I don't know what we'll find on the other side."),
            ]

        if conv == Conversations.MARY_AND_HEAD_AT_GATE:
            head_sprites = get_sprites(NpcID.HEAD)
            mary_sprites = get_sprites(NpcID.MARY_SKELLY)
            if interact_count == 0:
                res_list = [
                    NpcDialog("AHH! HELP! They took my BONES! MY BONES.", sprites=head_sprites),
                    NpcDialog("Who did this? Where are the gate guards?", sprites=mary_sprites),
                    NpcDialog("I'm so NUMB. So UNFEELING. So EMPTY. My BONES...", sprites=head_sprites),
                    NpcDialog("What happened to your bones?", sprites=mary_sprites),
                    NpcDialog("Those DAMN scientists with their experiments. Drove the animals MAD with their tinkering.", sprites=head_sprites),
                    NpcDialog("Attacked the city. Systems failed. Bones, STOLEN. Discarded. DISMANTLED", sprites=head_sprites),
                    NpcDialog("The animals did this to you?", sprites=mary_sprites),
                    NpcDialog("No... other... things too. Horrible things...", sprites=head_sprites),
                    NpcDialog("The whole city fell? How could that.. even happen?", sprites=mary_sprites),
                    NpcDialog("Need my bones... Where are my BONES...?", sprites=head_sprites),
                    NpcDialog("We're going to try to find your bones, ok? We're going to fix this.", sprites=mary_sprites)
                ]
            else:
                res_list = [
                    NpcDialog("Where are my BONES? My precious bones...", sprites=head_sprites),
                    NpcDialog("We should get moving. There's nothing we can do for him here.", sprites=mary_sprites)
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
                    NpcDialog("Well... no matter. Welcome to Tomb Town! The final outpost before Skeletris."),
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
            npc_sprites = get_template(conv.get_npc_id()).get_dialog_sprites()
            for dia in res_list:
                if isinstance(dia, NpcDialog) and dia.sprites is None:
                    dia.sprites = npc_sprites

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
        return dialog.NpcDialog("You give me an item, I give it back. Simple.", sprites=get_sprites(npc_id))

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Here's your item! Have a nice day.", sprites=get_sprites(npc_id))

    def get_post_success_dialog(self, npc_id):
        return dialog.NpcDialog("I hope you're enjoying the item!", sprites=get_sprites(npc_id))

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("I can't accept that type of item.", sprites=get_sprites(npc_id))

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("No more trades today. Sorry!", sprites=get_sprites(npc_id))


class NpcMirrorTradeProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.mirror()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Care to make a trade?", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What's the trade?"),
             dialog.NpcDialog("It's simple. You give me an Artifact, and I'll flip it for you.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("Flip it for me?"),
             dialog.NpcDialog("You'll see. Interested?", sprites=get_sprites(npc_id))]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("No, no. Not that kind of item. It needs to be more... " +
                                "how do I describe it... cubelike?", sprites=get_sprites(npc_id))


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
        return dialog.NpcDialog("I can't accept that. Only potions.", sprites=get_sprites(npc_id))

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Here's the deal. You give me a potion, and I'll give you a new one back.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What's the catch?"),
             dialog.NpcDialog("No catch. Just an honest deal. How about it?", sprites=get_sprites(npc_id))]
        return dialog.Dialog.link_em_up(d)

    def get_post_success_dialog(self, npc_id):
        return dialog.NpcDialog("Oh, by the way... don't operate any heavy machinery after drinking that.", sprites=get_sprites(npc_id))

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Hey, hey. I think you've had enough.", sprites=get_sprites(npc_id))


class NpcRerollCubesProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_cubes()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Shh! Listen closely. I can... reshape things. I'll show you.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What kind of things?"),
             dialog.NpcDialog("Artifacts! What else? Come on. Give me one. Quickly.", sprites=get_sprites(npc_id))]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Stop screwing around! An Artifact! Give me an Artifact.", sprites=get_sprites(npc_id))

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Look at that! Completely reforged. Does it fit better now?", sprites=get_sprites(npc_id))

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Sorry kid. I'm spent. Come back another time.", sprites=get_sprites(npc_id))

    def get_post_success_dialog(self, npc_id):
        d = [dialog.NpcDialog("Enjoying that item I gave you?"),
             dialog.PlayerDialog("Yeah, it's pretty nice."),
             dialog.NpcDialog("No need to thank me. I do accept tips though. And positive reviews are appreciated. " +
                              "And have you seen my twitter?", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("Yeah! yeah. I'll check it out. I gotta... get going, though, ya know."),
             dialog.NpcDialog("Oh, right, right. Very busy. You will check it out though? " +
                              "Let me just get you the URL...", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("Yeah! No worries, I'll find it. Thanks! Love the item. Bye!")]
        return dialog.Dialog.link_em_up(d)


class NpcRerollStatsProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_stats()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Need some help? Give me an Artifact, and I'll re-roll the stats for you.",
                              sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("That does sound helpful."),
             dialog.NpcDialog("I'll do my best! But it's unpredictable. " +
                              "No guarantees it'll improve, I'm afraid.", sprites=get_sprites(npc_id)),
             dialog.NpcDialog("Care to give it a shot?", sprites=get_sprites(npc_id))
            ]
        return dialog.Dialog.link_em_up(d)

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Oh, I've confused you. The item needs to be an Artifact.", sprites=get_sprites(npc_id))

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Here you go! I hope you like it.", sprites=get_sprites(npc_id))

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("I can't do any more right now I'm afraid. " +
                                "But if you see me around, don't hesitate to say hello!", sprites=get_sprites(npc_id))


class NpcRerollArtProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        return ItemTags.CUBES in item.get_type().get_tags()

    def do_trade(self, item):
        return [item.reroll_art()]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Hey, you there! Hey! You! I've got something for you.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("I'm standing right here... no need to yell..."),
             dialog.NpcDialog("I can do something quite special. Something no one else can do. " +
                              "Something few can even wrap their minds around.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What are you going to do?"),
             dialog.NpcDialog("Just give me your best, favorite, Artifact, and then you'll see.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("You can't just tell me?"),
             dialog.NpcDialog("And spoil the surprise? No way! What do you say?", sprites=get_sprites(npc_id))
             ]
        return dialog.Dialog.link_em_up(d)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Ah-ha, see? Look at that. Spectacular.", sprites=get_sprites(npc_id))

    def get_wrong_item_dialog(self, npc_id, item):
        return dialog.NpcDialog("Are you deaf? It's gotta be an artifact. This won't work.", sprites=get_sprites(npc_id))

    def get_post_success_dialog(self, npc_id):
        d = [dialog.PlayerDialog("Did anything... change?"),
             dialog.NpcDialog("Ha, ha... you're joking, right? Look at the color! " +
                              "The designs! It's totally different!", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("Oh. Hmm. I guess... I don't remember how it used to look."),
             dialog.NpcDialog("What are you, a goldfish? Two seconds pass and everything goes \"poof\"? "
                              "No one cares about the details anymore.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What's a goldfish?"),
             dialog.NpcDialog("...", sprites=get_sprites(npc_id)),
             dialog.NpcDialog("Just astonishing, you turned out to be. ", sprites=get_sprites(npc_id))
            ]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Only one per customer! I'm very busy you know.", sprites=get_sprites(npc_id))


class NpcItemThatFitsProtocol(NpcTradeProtocol):

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
        # mirroring the actual drop rates is pretty brutal...
        #
        # choices = [5] * balance.STAT_CUBE_5_DROP_RATE
        # if max_n_cubes >= 6:
        #    choices.extend([6] * balance.STAT_CUBE_6_DROP_RATE)
        # if max_n_cubes >= 7:
        #    choices.extend([7] * balance.STAT_CUBE_7_DROP_RATE)

        choices = [x for x in range(5, max_n_cubes + 1)]
        if len(choices) > 0:
            return random.choice(choices)
        else:
            raise ValueError("illegal argument max_n_cubes: {}".format(max_n_cubes))

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
        res_cubes = [cluster.pop()]

        while len(res_cubes) < n_cubes:
            did_expand = False
            for c in res_cubes:
                # trying to 'expand' off of c to fill the region.
                c_n = [n for n in Utils.neighbors(c[0], c[1])]
                random.shuffle(c_n)
                for n in c_n:
                    if n in cluster:
                        res_cubes.insert(0, n)  # want to keep growing off this one if possible
                        cluster.remove(n)       # makes the result more "snaky"
                        did_expand = True
                        break

                if did_expand:
                    break  # start the process over

            if not did_expand:
                raise ValueError("failed to expand to fill cluster...?")

        if len(res_cubes) != n_cubes:
            raise ValueError("res_cubes has incorrect size={}, expected={}".format(len(res_cubes), n_cubes))

        import src.items.itemgen as itemgen

        stat_types = []
        for applied_stat in item.all_applied_stats():
            if applied_stat.get_type() not in stat_types:  # there shouldn't be dupes, but nuke them just in case.
                stat_types.append(applied_stat.get_type())

        # might need to delete stats if we lost cubes.
        n_stats_to_remove = len(stat_types) - balance.max_stats_for_n_cubes(len(res_cubes))
        if n_stats_to_remove > 0:
            core_stats = [s for s in stat_types if s in itemgen.CORE_STATS]
            if len(core_stats) > 0:
                protected_core_stat = random.choice(core_stats)
            else:
                protected_core_stat = None  # weird but ok...

            deletable_stat_types = [s for s in stat_types if s != protected_core_stat]

            while n_stats_to_remove > 0 and len(deletable_stat_types) > 0:
                to_del = random.choice(deletable_stat_types)
                deletable_stat_types.remove(to_del)
                stat_types.remove(to_del)

                n_stats_to_remove -= 1

        new_applied_stats = itemgen.StatCubesItemFactory.gen_applied_stats_for_cubes_and_stat_types(
            item.get_level(), res_cubes, stat_types)

        new_item = itemgen.StatCubesItemFactory.gen_item_for_cubes_and_stats(
            item.get_level(), res_cubes, new_applied_stats)

        return [new_item]

    def get_explain_dialog(self, npc_id):
        d = [dialog.NpcDialog("Welcome to PrintBot. I perform an item re-printing service. How can I help you?", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("How does this work?"),
             dialog.NpcDialog("Clear some space in your equipment grid and give me an artifact. Then I'll re-print it so it fits in your grid.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("Will the item's stats change?"),
             dialog.NpcDialog("Sometimes. That's part of the fun!", sprites=get_sprites(npc_id)),
             dialog.NpcDialog("Just make sure there is enough space for the new item. Otherwise it definitely won't work.", sprites=get_sprites(npc_id)),
        ]
        return dialog.Dialog.link_em_up(d)

    def get_success_dialog(self, npc_id, item):
        return dialog.NpcDialog("Print completed successfully. Enjoy!", sprites=get_sprites(npc_id))

    def get_wrong_item_dialog(self, npc_id, item):
        if not self._is_valid_item_type(item):
            return dialog.NpcDialog("ERROR: PrintBot is not compatible with this item. Only artifacts are supported.",
                                    sprites=get_sprites(npc_id))
        elif not self._is_enough_space_for_new_item(item):
            return dialog.NpcDialog("ERROR: Not enough space in equipment grid.", sprites=get_sprites(npc_id))
        else:
            return dialog.NpcDialog("ERROR: Unexpected error.", sprites=get_sprites(npc_id))

    def get_post_success_dialog(self, npc_id):
        d = [dialog.NpcDialog("Please rate the service you received from [1] to [5] stars.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("I..."),
             dialog.NpcDialog("Confirming [5] star rating. Thank you!", sprites=get_sprites(npc_id))]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("ERROR: Toner cartridge is not genuine. Please install a genuine PrintBot toner cartridge and try again.",
                                sprites=get_sprites(npc_id))


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
    return TEMPLATES[npc_id].get_dialog_sprites()


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