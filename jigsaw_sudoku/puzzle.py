from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils

# fmt: off
SUDOKU_VALUES = [
    "1","2","3","4","5","6","7","8","9",
    "A","B","C","D","E","F","G",
]
# fmt: on


class JigsawSudokuPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_row: dict[tuple[int, str], int]  # row, value -> count
    found_by_col: dict[tuple[int, str], int]  # col, value -> count
    found_by_region: dict[tuple[int, str], int]  # region, value -> count

    def __init__(self, grid, found_by_row, found_by_col, found_by_region):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.found_by_region = found_by_region


class JigsawSudokuPuzzle(Puzzle):
    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]

        grid_size = len(lines) // 2
        regions_grid = lines[:grid_size]

        initial_grid = [
            [cell if cell != "." else None for cell in row] for row in lines[grid_size:]
        ]

        return cls(regions_grid, initial_grid)

    def __init__(self, regions_grid, initial_grid, state=None):
        self.regions_grid = regions_grid
        self.initial_grid = initial_grid
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))
        self.state = state

        self.regions = {}
        for r, c in self.grid_utils.iter_grid():
            region = self.regions_grid[r][c]
            self.regions.setdefault(region, []).append((r, c))

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "."

            return str(self.state.grid[r][c])

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        self.state = JigsawSudokuPuzzleState(
            [
                [None for c in range(self.grid_utils.cols)]
                for r in range(self.grid_utils.rows)
            ],
            {
                (r, value): 0
                for r in range(self.grid_utils.rows)
                for value in self.iter_values()
            },
            {
                (c, value): 0
                for c in range(self.grid_utils.cols)
                for value in self.iter_values()
            },
            {
                (region, value): 0
                for region in self.regions
                for value in self.iter_values()
            },
        )

        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] is not None:
                self.set_value((r, c), self.initial_grid[r][c])

    def iter_values(self):
        yield from SUDOKU_VALUES[: self.grid_utils.rows]

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def can_set(self, location, value):
        r, c = location
        region = self.regions_grid[r][c]
        return (
            self.state.found_by_row[r, value] == 0
            and self.state.found_by_col[c, value] == 0
            and self.state.found_by_region[region, value] == 0
        )

    def _update_value(self, location, value, delta):
        r, c = location
        region = self.regions_grid[r][c]

        self.state.found_by_row[r, value] += delta
        self.state.found_by_col[c, value] += delta
        self.state.found_by_region[region, value] += delta

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(location, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_value(location, value, -1)
