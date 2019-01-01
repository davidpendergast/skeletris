import random


_WORDS = ("abet ache acid acme adze ague akin amen ammo amok ankh apse arid aver awry axis bard berm " +
          "bevy bilk bled boor bort brig bulk busk clef coda coif coir cuil culb curb cyst czar dais " +
          "daub deft dhow doff doup echo ecru egad elan epic esox espy faro faux fiat flax frig froe " +
          "fusc gawk gkol glee glom glum glut gnat gorp gory grok iamb ibex ibis icon ilex iota iris " +
          "jape jawa jive jolt keen kiln kine kith knob kyat lamb lanx lava lens lewd lieu loin lung " +
          "lynx minx mump navy nerd oboe ogle ogre okra onus onyx oont ooze opal oryx orzo oust oxen " +
          "peen pelf peon pimp ping pith plat pook puce puha pulp puma quip rale rapt rasp ruby scat " +
          "scry serf shiv silo skep skua slue smar smew snog sofa spad sped spry tael thug tofu tsar " +
          "tutu tuya udon ulna vamp viol vuln waif welt winx wisp wonk wren yawl yeta yolk")
_WORDS = _WORDS.split(" ")


def gen_unique_password(current_passwords):
    thresh = 100
    pw_set = set(current_passwords)

    for i in range(0, thresh):
        pw = gen_nice_password()
        if pw not in pw_set:
            return pw

    for i in range(0, thresh):
        pw = gen_mean_password()
        if pw not in pw_set:
            return pw

    for i in range(0, thresh):
        pw = gen_very_mean_password()
        if pw not in pw_set:
            return pw

    print("WARN: failed to generate a unique password")
    return "000000"


def gen_nice_password():
    word = random.choice(_WORDS)
    number = str(random.randint(0, 9)) + str(random.randint(0, 9))
    return word + number


def gen_mean_password():
    word = ""
    for i in range(0, 4):
        word += random.choice("abcdefghijklmnopqrstuvwxyz")
    number = str(random.randint(0, 9)) + str(random.randint(0, 9))
    return word + number


def gen_very_mean_password():
    res = ""
    for i in range(0, 6):
        res += random.choice("abcdefghijklmnopqrstuvwxyz0123456789")
    return res


def is_valid(password):
    if password is None:
        return False
    if len(password) != 6:
        return False
    for c in password:
        if c not in "abcdefghijklmnopqrstuvwxyz0123456789":
            return False

    return True


if __name__ == "__main__":
    nice = [gen_nice_password() for _ in range(0, 100)]
    mean = [gen_mean_password() for _ in range(0, 100)]
    very_mean = [gen_nice_password() for _ in range(0, 100)]
    print("nice = {}".format(nice))
    print("mean = {}".format(mean))
    print("very_mean = {}".format(very_mean))


