import os

IS_DEV = os.path.exists("this_is_dev.txt")
DEBUG = IS_DEV and True
