import os
import sys
import platform
import pathlib
import datetime
import tempfile
import shutil
import stat

import src.game.version as version


_WINDOWS = "Windows"
_LINUX = "Linux"


SPEC_CONTENTS = """
# -*- mode: python -*-
# WARNING: This file is auto-generated (see make_exe.py)

block_cipher = None

a = Analysis(['skeletris.py'],
             pathex=[''],
             binaries=[],
             datas=[('assets', 'assets'), ('info', 'info')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Skeletris',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='assets/icon.ico')
"""


def _ask_yes_or_no_question(question):
    print("")  # newline to make it a little less claustrophobic
    answer = None
    while answer is None:
        txt = input("  " + question + " (y/n): ")
        if txt == "y" or txt == "Y":
            answer = True
        elif txt == "n" or txt == "N":
            answer = False
    print("")
    return answer


def _get_info_text(system_str, bit_count_str, version_str, date_str):
    return """
 ~ Skeletris ~ 

Controls:
 Move: W, A, S, D
 Attack & Interact: W, A, S, D or Click
 Skip Turn: Space
 Open Inventory: R
 Open Map: M
 Pick up Item: Click it
 Use, Trade, or Throw Item: While the item is on the cursor, click the target 

 Rotate Item on Cursor: E
 Activate Weapon: 1-6

 Toggle Fullscreen: F4
 Toggle Resolution: F5
 Pause: Esc
 
 
Version Info:
  Platform: {} ({})
  Game Version: {}
  Date Generated: {}


Launch Instructions:
  The game and all of its assets are bundled into a single executable, so after 
  unzipping this directory you should be able to just double click "Skeletris.exe" 
  to launch it. A subdirectory named "save_data" will be created to store settings 
  and stuff like that.
  
  On Windows 8.1 and onwards, when you launch the game it may show a warning like:
    "Windows protected your PC - Windows Defender SmartScreen prevented an 
    unrecognized app from starting. Running this app might put your PC at risk."
    
  You can bypass this by clicking "more info" -> "Run Anyway" in the Windows popup.
    
  This happens because I don't have a digital certificate, because they're quite 
  expensive. That being said, https://ghastly.itch.io/skeletris is the ONLY official 
  distribution channel for this game. If you got this file from somewhere else, you 
  should probably re-download it from that link.
""".format(system_str, bit_count_str, version_str, date_str)


if __name__ == "__main__":
    version.load_version_info(force_nodev=True)
    version_num_str = version.get_pretty_version_string()  # version number of the game, expect "X.Y.Z-DESC"

    os_system_str = platform.system()  # expect "Windows" or "Linux"
    if os_system_str != _WINDOWS and os_system_str != _LINUX:
        raise ValueError("Unrecognized operating system: {}".format(os_system_str))

    os_bit_count_str = platform.architecture()[0]  # expect "32bit" or "64bit" (note that this doesn't work in OSX).

    make_the_exe = _ask_yes_or_no_question("Create v{} executable for {} ({})?".format(
        version_num_str, os_system_str, os_bit_count_str))

    if not make_the_exe:
        print("INFO: make_exe was canceled by user, exiting")
        sys.exit(0)

    spec_filename = pathlib.Path("skeletris.spec")
    print("INFO: creating spec file {}".format(spec_filename))
    with open(spec_filename, "w") as f:
        f.write(SPEC_CONTENTS)

    version_num_str_no_dots = version_num_str.replace(".", "_").replace("-", "_")

    dist_dir = pathlib.Path("dist/skeletris_v{}_{}_{}".format(
        version_num_str_no_dots.lower(), os_system_str.lower(), os_bit_count_str.lower()))

    if os.path.exists(str(dist_dir)):
        ans = _ask_yes_or_no_question("Overwrite {}?".format(dist_dir))
        if ans:
            print("INFO: deleting pre-existing build {}".format(dist_dir))
            shutil.rmtree(str(dist_dir), ignore_errors=True)
        else:
            print("INFO: user opted to not overwrite pre-existing build, exiting")
            sys.exit(0)

    dist_dir_subdir = pathlib.Path("{}/Skeletris".format(dist_dir))

    with tempfile.TemporaryDirectory() as temp_dir:
        print("INFO: created temp directory: {}".format(temp_dir))
        print("INFO: launching pyinstaller...\n")

        # note that this call blocks until the process is finished
        os.system("pyinstaller {} --distpath {} --workpath {}".format(spec_filename, dist_dir_subdir, temp_dir))

        print("\nINFO: cleaning up {}".format(temp_dir))

    print("INFO: cleaning up {}".format(spec_filename))
    if os.path.exists(str(spec_filename)):
        os.remove(str(spec_filename))

    print("INFO: writing info.txt")
    info_txt_filepath = pathlib.Path("{}/info.txt".format(dist_dir_subdir))
    with open(info_txt_filepath, "w") as f:
        date_str = datetime.datetime.today()
        f.write(_get_info_text(os_system_str, os_bit_count_str, version_num_str, date_str))

    if os_system_str == _LINUX:
        print("INFO: chmod'ing execution permissions to all users (linux)")
        exe_path = pathlib.Path("{}/Skeletris".format(dist_dir_subdir))
        if not os.path.exists(str(exe_path)):
            raise ValueError("couldn't find exe to apply exec permissions: {}".format(exe_path))
        else:
            st = os.stat(str(exe_path))
            os.chmod(str(exe_path), st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print("\nINFO: make_exe.py has finished")
