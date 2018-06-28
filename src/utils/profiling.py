import cProfile
import pstats

_instance = None


def get_instance():
    global _instance
    if _instance is None:
        _instance = Profiler()
    
    return _instance


class Profiler:

    def __init__(self):
        self.is_running = False
        self.pr = cProfile.Profile(builtins=False)

    def toggle(self):
        self.is_running = not self.is_running

        if not self.is_running:
            self.pr.disable()

            sortby = 'cumulative'
            ps = pstats.Stats(self.pr)
            ps.strip_dirs()
            ps.sort_stats(sortby)
            ps.print_stats(35)

        else:
            print("INFO\tstarted profiling...")
            self.pr.clear()
            self.pr.enable()
