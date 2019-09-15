
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

    def get_trade_protocol(self, level):
        if level >= 7:
            return NpcTradeProtocols.MIRROR_TRADE


class MayorPatchesTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MAYOR, "Mayor Patches", sr.mayor_pumpkin_all, sr.mayor_pumpkin_faces,
                             ("p", colors.YELLOW), shadow_sprite=sr.large_shadow)

    def get_trade_protocol(self, level):
        if level >= 9:
            return NpcTradeProtocols.REROLL_ART


class BeanskullTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.BEANSKULL, "Beanskull", sr.beanskull_all, sr.beanskull_faces, ("b", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 3:
            return NpcTradeProtocols.REROLL_STATS


class GlorpleTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.GLORPLE, "Glorple", sr.enemy_glorple_all, sr.glorple_faces, ("g", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 4:
            return NpcTradeProtocols.REROLL_CUBES


class MachineTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.MACHINE, "Machine", sr.save_stations, sr.save_station_faces, ("M", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 5:
            return NpcTradeProtocols.ITEM_THAT_FITS


class DoctorTemplate(NpcTemplate):

    def __init__(self):
        NpcTemplate.__init__(self, NpcID.DOCTOR, "Doc", sr.doctor_all, sr.doctor_faces, ("d", colors.YELLOW))

    def get_trade_protocol(self, level):
        if level >= 2:
            return NpcTradeProtocols.POTION_EXCHANGE


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


def all_templates():
    for npc_id in TEMPLATES:
        if npc_id != NpcID.CAVE_HORROR:
            yield TEMPLATES[npc_id]


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

        from src.items.itemgen import PotionItemFactory
        res_item = PotionItemFactory.gen_item(drop_as_level)
        if res_item is not None:
            return [res_item]
        else:
            print("WARN: failed to generate a potion to trade..?")
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
                              "No one appreciates the little details anymore.", sprites=get_sprites(npc_id)),
             dialog.PlayerDialog("What's a goldfish?"),
             dialog.NpcDialog("...", sprites=get_sprites(npc_id)),
             dialog.NpcDialog("Just astonishing, you turned out to be.", sprites=get_sprites(npc_id))
            ]
        return dialog.Dialog.link_em_up(d)

    def get_no_more_trades_dialog(self, npc_id):
        return dialog.NpcDialog("Only one per customer! I'm very busy you know.", sprites=get_sprites(npc_id))


class NpcItemThatFitsProtocol(NpcTradeProtocol):

    def accepts_trade(self, item):
        from src.items.item import ItemTags
        if ItemTags.CUBES not in item.get_type().get_tags():
            return False

        # not enough space in grid to create a valid item.
        if len(self._get_empty_equipment_grid_cell_clusters(min_size=5)) == 0:
            return False

        return True

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
        choices = [5] * balance.STAT_CUBE_5_DROP_RATE
        if max_n_cubes >= 6:
            choices.extend([6] * balance.STAT_CUBE_6_DROP_RATE)
        if max_n_cubes >= 7:
            choices.extend([7] * balance.STAT_CUBE_7_DROP_RATE)

        return random.choice(choices)

    def do_trade(self, item):
        item_n_cubes = min(len(item.cubes), 7)
        empty_clusters = self._get_empty_equipment_grid_cell_clusters(min_size=5)

        if len(empty_clusters) == 0:
            print("ERROR: bad state, no empty cell clusters in equipment grid...")
            return [item]

        # can't generate an item of size n unless there's a cluster that's big enough
        max_cluster_size = max([len(cluster) for cluster in empty_clusters])

        # same drop rate as regular item drops
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

        return [itemgen.StatCubesItemFactory.gen_item_for_cubes(item.get_level(), res_cubes)]


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
    def get_npcs(level, n_convo, n_trade):
        convo_res = []
        trade_res = []

        npc_types = []
        for i in range(0, n_convo):
            npc_types.append(True)
        for i in range(0, n_trade):
            npc_types.append(False)
        random.shuffle(npc_types)

        import src.world.entities as entities

        used_npc_ids = []

        available_convos = [c for c in Conversations.get_all() if c.is_available(level)]
        available_traders = [npc_id for npc_id in TEMPLATES if get_template(npc_id).get_trade_protocol(level) is not None]

        random.shuffle(available_convos)
        random.shuffle(available_traders)

        for t in npc_types:
            if t:
                # conversation type
                while len(available_convos) > 0:
                    next_convo = available_convos.pop()
                    npc_id = next_convo.get_npc_id()
                    if npc_id not in used_npc_ids:
                        used_npc_ids.append(npc_id)
                        convo_res.append(entities.NpcConversationEntity(0, 0, get_template(npc_id), next_convo))
                        break
            else:
                # trade type
                while len(available_traders) > 0:
                    npc_id = available_traders.pop()
                    if npc_id not in used_npc_ids:
                        used_npc_ids.append(npc_id)
                        template = get_template(npc_id)
                        trade_res.append(entities.NpcTradeEntity(0, 0, template, template.get_trade_protocol(level)))
                        break

        return (convo_res, trade_res)

    @staticmethod
    def gen_trade_npc(npc_id, level):
        import src.world.entities as entities

        template = get_template(npc_id)
        return entities.NpcTradeEntity(0, 0, template, template.get_trade_protocol(level))
