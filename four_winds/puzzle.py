from logic_puzzles.puzzle import Puzzle, PuzzleState
from itertools import product

DIRECTION_STR = {
    (0, 1): ">",
    (0, -1): "<",
    (1, 0): "v",
    (-1, 0): "^",
}


class FourWindsPuzzleState(PuzzleState):
    regions_grid: list[list[int]]
    grid: list[list[int]]

    def __init__(self, regions_grid, grid):
        self.regions_grid = regions_grid
        self.grid = grid


class FourWindsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Ai+quattro+venti"""

    initial_grid: list[list[int | None]]
    regions: list[list[tuple[int, int]]]
    state: FourWindsPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x for x in lines if x and not x.startswith("#")]
        initial_grid = [
            [None if x == "." else int(x) for x in line.split()] for line in lines
        ]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.regions = []

        for r, c in product(range(self.rows), range(self.cols)):
            cell = self.initial_grid[r][c]
            if cell is None:
                continue

            self.regions.append((r, c))

        if state is None:
            regions_grid = [[None] * self.cols for _ in range(self.rows)]

            for r, c in product(range(self.rows), range(self.cols)):
                cell = self.initial_grid[r][c]
                if cell is None:
                    continue

                regions_grid[r][c] = (r, c)

            grid = [row.copy() for row in self.initial_grid]
            self.state = FourWindsPuzzleState(regions_grid, grid)
        else:
            self.state = state

    def __str__(self):
        def stringify_cell(r, c):
            cell = self.state.grid[r][c]
            if isinstance(cell, int):
                return str(cell)
            if cell is None:
                return "."
            parent_r, parent_c = self.state.regions_grid[r][c]
            dr = parent_r - r
            dc = parent_c - c
            dr //= max(1, abs(dr))
            dc //= max(1, abs(dc))
            return DIRECTION_STR[dr, dc]

        return "\n".join(
            " ".join(stringify_cell(r, c).ljust(2) for c, cell in enumerate(row))
            for r, row in enumerate(self.state.grid)
        )

    @property
    def rows(self):
        return len(self.initial_grid)

    @property
    def cols(self):
        return len(self.initial_grid[0])

    def is_parent(self, r, c):
        region_id = self.state.regions_grid[r][c]
        if region_id is None:
            return False

        return (r, c) == region_id

    def in_range(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_aligned(self, r, c, r2, c2):
        return r == r2 or c == c2

    def ray_iter(self, r, c, r2, c2):
        assert self.is_aligned(r, c, r2, c2)
        dr = r2 - r
        dc = c2 - c
        dr //= max(1, abs(dr))
        dc //= max(1, abs(dc))

        while (r, c) != (r2, c2):
            yield r, c
            r += dr
            c += dc

    def star_iter(self, r, c):
        iterators = [
            self.ray_iter(r, c, r, -1),
            self.ray_iter(r, c, r, self.cols),
            self.ray_iter(r, c, -1, c),
            self.ray_iter(r, c, self.rows, c),
        ]

        for iterator in iterators:
            for new_r, new_c in iterator:
                if (new_r, new_c) == (r, c):
                    continue
                if self.initial_grid[new_r][new_c] is not None:
                    break
                yield new_r, new_c

    def get_unmet_demand(self):
        res = 0
        for r, c in self.regions:
            res += self.state.grid[r][c]

        return res

    def get_potential_regions(self, r, c):
        res = set()
        for region in self.regions:
            parent_r, parent_c = region
            if not self.is_aligned(r, c, parent_r, parent_c):
                continue

            distance = abs(r - parent_r) + abs(c - parent_c)

            for new_r, new_c in self.ray_iter(r, c, parent_r, parent_c):
                new_region = self.state.regions_grid[new_r][new_c]
                if new_region is not None and new_region != region:
                    distance = None
                    break
                elif new_region == region:
                    distance -= 1

            if distance is not None and distance <= self.state.grid[parent_r][parent_c]:
                res.add(region)

        return res

    def set_region_ray(self, r, c, region_id):
        updated = set()
        parent_r, parent_c = region_id

        for new_r, new_c in self.ray_iter(r, c, parent_r, parent_c):
            if self.state.regions_grid[new_r][new_c] is not None:
                assert self.state.regions_grid[new_r][new_c] == region_id
                continue

            updated.add((new_r, new_c))
            self.set_region(new_r, new_c, region_id)

        assert self.state.grid[parent_r][parent_c] >= 0
        return updated

    def set_region(self, r, c, region_id):
        # NOTE: this does not check that the grid is left in a valid state
        parent_r, parent_c = region_id
        dr = parent_r - r
        dc = parent_c - c
        dr //= max(1, abs(dr))
        dc //= max(1, abs(dc))
        self.state.grid[parent_r][parent_c] -= 1
        self.state.grid[r][c] = DIRECTION_STR[-dr, -dc]
        self.state.regions_grid[r][c] = region_id

    def unset_region(self, r, c):
        # NOTE: this does not check that the grid is left in a valid state
        region_id = self.state.regions_grid[r][c]
        parent_r, parent_c = region_id
        self.state.grid[r][c] = None
        self.state.regions_grid[r][c] = None
        self.state.grid[parent_r][parent_c] += 1
