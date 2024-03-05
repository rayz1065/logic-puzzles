from itertools import product
from collections import namedtuple
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class GalaxiesPuzzleState(PuzzleState):
    grid: list[list[int | None]]

    def __init__(self, grid):
        self.grid = grid


class Galaxy(namedtuple("Galaxy", ["row_1", "row_2", "col_1", "col_2"])):
    def iter_core(self):
        yield from product(
            range(self.row_1, self.row_2 + 1), range(self.col_1, self.col_2 + 1)
        )


class GalaxiesPuzzle(Puzzle):
    """
    http://www.puzzlefountain.com/giochi.php?tipopuzzle=Galassie
    NOTE: The rule that a galaxy cannot be adjacent to itself is not enforced.
    """

    initial_grid: list[list[int | None]]
    galaxies: list[Galaxy]
    grid_utils: GridUtils
    cell_galaxies: list[list[list[int]]]
    galaxy_cores: dict[tuple[int, int], int]
    galaxy_cells: list[list[tuple[int, int]]]
    state: GalaxiesPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.replace(" ", "") for x in lines if x and not x.startswith("#")]

        rows = (len(lines) + 1) // 2
        cols = (len(lines[0]) + 1) // 2
        initial_grid = [[None for _ in range(cols)] for _ in range(rows)]

        galaxies = []
        for i, line in enumerate(lines):
            for j, cell in enumerate(line):
                if cell != "x":
                    continue

                row_1 = i // 2
                row_2 = i // 2 + i % 2
                col_1 = j // 2
                col_2 = j // 2 + j % 2
                galaxies.append(Galaxy(row_1, row_2, col_1, col_2))

        return cls(initial_grid, galaxies)

    def __init__(self, initial_grid, galaxies, state=None):
        self.initial_grid = initial_grid
        self.galaxies = galaxies
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))
        self.cell_galaxies = [
            [[] for _ in range(self.grid_utils.cols)]
            for _ in range(self.grid_utils.rows)
        ]
        self.galaxy_cores = {}
        for galaxy_id, galaxy in enumerate(galaxies):
            for r, c in galaxy.iter_core():
                self.galaxy_cores[r, c] = galaxy_id

        self.galaxy_cells = [[] for _ in self.galaxies]
        for galaxy_id, galaxy in enumerate(galaxies):
            for r, c in self.find_galaxy_bounds(galaxy_id):
                self.cell_galaxies[r][c].append(galaxy_id)
                self.galaxy_cells[galaxy_id].append((r, c))

        if state is None:
            self.initialize_state()

    def __str__(self):
        return "\n".join(
            " ".join(".".rjust(2) if x is None else str(x).rjust(2) for x in row)
            for row in self.state.grid
        )

    def rotational_symmetry(self, row, col, galaxy):
        # 180 degrees rotational symmetry around the center of the galaxy
        row_1, row_2, col_1, col_2 = galaxy
        center_row = row_1 + row_2
        center_col = col_1 + col_2
        return center_row - row, center_col - col

    def initialize_state(self):
        self.state = GalaxiesPuzzleState(
            grid=[
                [None for _ in range(self.grid_utils.cols)]
                for _ in range(self.grid_utils.rows)
            ],
        )

        for galaxy_id, galaxy in enumerate(self.galaxies):
            for r, c in galaxy.iter_core():
                self.set_value((r, c), galaxy_id)

    def find_galaxy_bounds(self, galaxy_id):
        galaxy = self.galaxies[galaxy_id]
        stack = []
        for r, c in galaxy.iter_core():
            if (r, c) <= self.rotational_symmetry(r, c, galaxy):
                stack.append((r, c))

        visited = set(galaxy.iter_core())
        while stack:
            r, c = stack.pop()
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                new_s_r, new_s_c = self.rotational_symmetry(new_r, new_c, galaxy)

                if (
                    (new_r, new_c) in visited
                    or (new_r, new_c) in self.galaxy_cores
                    or not self.grid_utils.in_range(new_s_r, new_s_c)
                    or (new_s_r, new_s_c) in self.galaxy_cores
                ):
                    continue

                stack.append((new_r, new_c))
                visited.add((new_r, new_c))
                visited.add((new_s_r, new_s_c))

        return visited

    def find_path_to_core(self, r, c, galaxy_id):
        if self.galaxy_cores.get((r, c), None) == galaxy_id:
            return True

        stack = [(r, c)]
        visited = set([(r, c)])
        while stack:
            r, c = stack.pop()
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                if self.galaxy_cores.get((new_r, new_c), None) == galaxy_id:
                    return True

                new_state = self.state.grid[new_r][new_c]
                if (
                    (new_r, new_c) in visited
                    or (new_state is not None and new_state != galaxy_id)
                    or galaxy_id not in self.cell_galaxies[new_r][new_c]
                ):
                    continue

                visited.add((new_r, new_c))
                stack.append((new_r, new_c))

        return False

    def get_valid_values(self, location):
        r, c = location
        return [i for i in self.cell_galaxies[r][c] if self.can_set((r, c), i)]

    def can_set(self, location, value):
        r, c = location

        # the symmetric cell wrt this galaxy must be empty or belong to the same galaxy
        new_r, new_c = self.rotational_symmetry(r, c, self.galaxies[value])
        if (
            self.state.grid[new_r][new_c] is not None
            and self.state.grid[new_r][new_c] != value
        ):
            return False

        # the symmetric cells wrt another galaxy must not already belong to that galaxy
        for galaxy_id in self.cell_galaxies[r][c]:
            if galaxy_id == value:
                continue

            new_r, new_c = self.rotational_symmetry(r, c, self.galaxies[galaxy_id])
            if self.state.grid[new_r][new_c] == galaxy_id:
                return False

        # there must be a path towards the core of the galaxy
        if not self.find_path_to_core(r, c, value):
            return False

        res = True

        self.set_value((r, c), value)

        # this cell cannot be a bridge for another galaxy
        for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
            galaxy_id = self.state.grid[new_r][new_c]
            if galaxy_id is None or galaxy_id == value:
                continue

            if not self.find_path_to_core(new_r, new_c, galaxy_id):
                res = False
                break

        self.unset_value((r, c))

        return res

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
