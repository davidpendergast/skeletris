import src.game.spriteref as spriteref
import src.game.music as music


class Cinematic:

    def __init__(self, images, text, music_id=None):
        self.images = images
        self.text = text
        self.music_id = music_id


_already_inited = False

opening_cinematic = []
cave_horror_intro = []
frog_intro = []


def init_cinematics():
    """Needs to wait for spritesheets to be built"""

    if _already_inited:
        raise ValueError("cinematics are already initialized")

    print("initializing cinematics...")
    opening_cinematic.extend([
        Cinematic(spriteref.Cinematics.intro_skel_ghost_things, "many years ago, skeletons, ghosts, and things lived together in harmony", music_id=music.Songs.MENU_THEME),
        Cinematic(spriteref.Cinematics.intro_skel_slide, "skeletons built towns, farmed crops, and raised families"),
        Cinematic(spriteref.Cinematics.intro_thing_slide, "things lived in tribes, migrating with the seasons to find food"),
        Cinematic(spriteref.Cinematics.intro_ghost_slide, "ghosts mostly just chatted"),
        Cinematic(spriteref.Cinematics.blank, "but one day everything changed"),
        Cinematic(spriteref.Cinematics.intro_fighting_slide, "the skeletons and things began fighting a brutal, endless war"),
        Cinematic(spriteref.Cinematics.blank, "the ghosts vanished without a trace"),
        Cinematic(spriteref.Cinematics.blank, "years of fighting nearly wiped out the populations of skeletons and things"),
        Cinematic(spriteref.Cinematics.blank, "skeletal cities were destroyed, and survivors were forced to take refuge in cave systems or underwater"),
        Cinematic(spriteref.Cinematics.blank, "only the strongest, deadliest tribes of things survived, who still roam the land in small packs"),
        Cinematic(spriteref.Cinematics.blank, "the ghosts were never seen again. only rumors can explain their disappearance"),
        Cinematic(spriteref.Cinematics.blank, "as the war ceased, a new era of uneasy peace began, but the scars of the past remain...")
    ])

    cave_horror_intro.extend([
        Cinematic(spriteref.Cinematics.blank, "it's very dark, but you can sense that you aren't alone"),
        Cinematic(spriteref.Cinematics.blank, "your eyes begin to adjust to the darkness"),
        Cinematic(spriteref.Cinematics.cave_horrors, ""),
        Cinematic(spriteref.Cinematics.cave_horrors, "you've entered the cave horror's lair. prepare to fight")
    ])

    frog_intro.extend([
        Cinematic(spriteref.Cinematics.blank, "the ground is wet. swamplike."),
        Cinematic(spriteref.Cinematics.blank, "you can hear breathing. slow and heavy."),
        Cinematic(spriteref.Cinematics.frog_eye, "an eye glares at you from across the room. you wonder how long it's been watching."),
        Cinematic(spriteref.Cinematics.frog_eye, "the beast crawls into the light."),
        Cinematic(spriteref.Cinematics.frog_body, "it's hideous."),
        Cinematic(spriteref.Cinematics.frog_body, "prepare to fight.")
    ])

