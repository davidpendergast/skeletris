import os

IS_DEV = os.path.exists("this_is_debug.txt")
DEBUG = IS_DEV and True
