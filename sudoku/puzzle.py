from math import isqrt
from functools import cached_property
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils

# fmt: off
SUDOKU_VALUES = [
    "1","2","3","4","5","6","7","8","9",
    "A","B","C","D","E","F","G",
]
# fmt: on


class SudokuPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_row: dict[tuple[int, str], int]  # row, value -> count
    found_by_col: dict[tuple[int, str], int]  # col, value -> count
    found_by_square: dict[
        tuple[int, int, str], int
    ]  # square_r, square_c, value -> count

    def __init__(self, grid, found_by_row, found_by_col, found_by_square):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.found_by_square = found_by_square


class SudokuPuzzle(Puzzle):
    initial_grid: list[list[int | None]]
    grid_utils: GridUtils
    state: SudokuPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        initial_grid = [
            [cell if cell != "." else None for cell in row] for row in lines
        ]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))
        self.state = state

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

    @cached_property
    def rows_square_size(self):
        return isqrt(self.grid_utils.rows)

    @cached_property
    def cols_square_size(self):
        return self.grid_utils.rows // self.rows_square_size

    @property
    def rows_square_count(self):
        return self.cols_square_size

    @property
    def cols_square_count(self):
        return self.rows_square_size

    @cached_property
    def sudoku_values(self):
        return SUDOKU_VALUES[: self.grid_utils.rows]

    def iter_square(self, square_r, square_c):
        base_r, base_c = (
            square_r * self.rows_square_size,
            square_c * self.cols_square_size,
        )

        for dr in range(self.rows_square_size):
            for dc in range(self.cols_square_size):
                yield base_r + dr, base_c + dc

    def get_square_coords(self, r, c):
        square_r = r // self.rows_square_size
        square_c = c // self.cols_square_size

        return square_r, square_c

    def initialize_state(self):
        self.state = SudokuPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            found_by_row={
                (row, value): 0
                for row in range(self.grid_utils.rows)
                for value in self.sudoku_values
            },
            found_by_col={
                (col, value): 0
                for col in range(self.grid_utils.rows)
                for value in self.sudoku_values
            },
            found_by_square={
                (square_r, square_c, value): 0
                for square_r in range(self.rows_square_count)
                for square_c in range(self.cols_square_count)
                for value in self.sudoku_values
            },
        )

        for r, c in self.grid_utils.iter_grid():
            value = self.initial_grid[r][c]
            if value is not None:
                self.set_value((r, c), value)

    def get_valid_values(self, location):
        return [value for value in self.sudoku_values if self.can_set(location, value)]

    def can_set(self, location, value):
        r, c = location
        square_r, square_c = self.get_square_coords(r, c)

        return (
            self.state.found_by_col[c, value] == 0
            and self.state.found_by_row[r, value] == 0
            and self.state.found_by_square[square_r, square_c, value] == 0
        )

    def _update_value(self, location, value, delta):
        r, c = location
        square_r, square_c = self.get_square_coords(r, c)

        self.state.found_by_col[c, value] += delta
        self.state.found_by_row[r, value] += delta
        self.state.found_by_square[square_r, square_c, value] += delta

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
