import traceback
import datetime
import os
import pathlib

"""
The main entry point.
"""

NAME_OF_GAME = "Skeletris"


def _get_crash_report_file_name():
    now = datetime.datetime.now()
    date_str = now.strftime("--%Y-%m-%d--%H-%M-%S")
    return "crash_report" + date_str + ".txt"


def _generate_readme(name_of_game):
    if debug.is_dev():
        print("INFO: generating readme...")
        import src.game.readme_writer as readme_writer
        import src.utils.util as util

        readme_writer.write_readme(name_of_game,
                                   util.Utils.resource_path("readme_template.txt"),
                                   util.Utils.resource_path("README.md"),
                                   util.Utils.resource_path("gifs"))


if __name__ == "__main__":
    version_string = "?"
    try:
        import src.game.debug as debug
        import src.game.version as version

        debug.init()
        version.load_version_info()
        version_string = version.get_pretty_version_string()

        print("INFO: started {} version: {}".format(NAME_OF_GAME, version_string))
        print("INFO: development mode: {}".format(debug.is_dev()))

        if debug.is_dev():
            _generate_readme(NAME_OF_GAME)

        import src.game.gameloop as gameloop
        gameloop.init(NAME_OF_GAME)
        gameloop.run()

    except Exception as e:
        crash_file_name = _get_crash_report_file_name()
        print("INFO: generating crash file {}".format(crash_file_name))

        directory = os.path.dirname("logs/")
        if not os.path.exists(directory):
            os.makedirs(directory)

        crash_file_path = pathlib.Path("logs/" + crash_file_name)
        with open(crash_file_path, 'w') as f:
            print("o--------------------------o", file=f)
            print("|  Skeletris Crash Report  |", file=f)
            print("o--------------------------o", file=f)
            print("\nVersion: {}\n".format(version_string), file=f)

            traceback.print_exc(file=f)

        raise e

