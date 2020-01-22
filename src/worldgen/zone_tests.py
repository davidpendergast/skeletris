import src.worldgen.zones as zones
import src.worldgen.worldgen2 as worldgen2


def test_grids_are_possible(n, level, dims=(3, 3)):
    """
        possible just means 1 start tile, at least one exit tile, and all exits are reachable from the start.

        returns: an invalid tile grid if one is found, else None
    """
    for _ in range(0, n):

        t_grid = zones.ZoneBuilder.generate_tile_grid_dangerously(None, level, dims=dims)
        player_coords = worldgen2.TileGridBuilder.search(t_grid, worldgen2.TileType.PLAYER)

        if len(player_coords) != 1:
            print("FAIL: more than one player spawn (level={})".format(level))
            return t_grid

        start = list(player_coords)[0]

        exit_coords = worldgen2.TileGridBuilder.search(t_grid, worldgen2.TileType.EXIT)
        if len(exit_coords) == 0:
            print("FAIL: no exit (level={})".format(level))
            return t_grid

        # whitelisting tiles instead of blacklisting so that we err on the side of false test failures
        # instead of false passes when new tiletypes are added and we forget to update the test.
        can_traverse = (worldgen2.TileType.PLAYER,
                        worldgen2.TileType.EXIT,
                        worldgen2.TileType.SIGN,
                        worldgen2.TileType.DECORATION,
                        worldgen2.TileType.CHEST,
                        worldgen2.TileType.FLOOR,
                        worldgen2.TileType.DOOR,
                        worldgen2.TileType.MONSTER,
                        worldgen2.TileType.STRAY_ITEM)

        reachable_by_player = worldgen2.TileGridBuilder.flood_search(t_grid, start[0], start[1], can_traverse)
        for ex in exit_coords:
            if ex not in reachable_by_player:
                print("FAIL: unreachable exit: {} (level={})".format(ex, level))
                return t_grid


if __name__ == "__main__":

    class _ZoneGenTestCase:
        def __init__(self, level, n, dims):
            self.level = level
            self.n = n
            self.dims = dims

    test_cases = []

    for lvl in range(0, 16):
        for x in range(1, 4):
            for y in range(1, 4):
                if x + y <= 3:
                    continue

                if x + y < 5:
                    n = 100  # smaller levels are more failure prone
                else:
                    n = 20

                test_cases.append(_ZoneGenTestCase(lvl, n, (x, y)))

    for i in range(0, len(test_cases)):
        test = test_cases[i]

        print("INFO: testing level={},\tn={},\tdims={}\t({:.1f}% complete)".format(
            test.level, test.n, test.dims, (100 * i / len(test_cases))))

        err = test_grids_are_possible(test.level, test.n, dims=test.dims)
        if err is not None:
            print(err)
            quit(1)


