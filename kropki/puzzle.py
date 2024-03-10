from itertools import product
from functools import cached_property, cache
from math import isqrt
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import ORTHOGONAL_DIRECTIONS, GridUtils


class KropkiPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    conflict_cells: list[list[list[int]]]

    def __init__(self, grid, conflict_cells):
        self.grid = grid
        self.conflict_cells = conflict_cells


class KropkiPuzzle(Puzzle):
    """
    http://www.puzzlefountain.com/giochi.php?tipopuzzle=Kropki
    https://puzzlephil.com/puzzles/kropkisudoku/en/
    """

    initial_grid: list[list[int | None]]
    between_columns: list[list[str]]
    between_rows: list[list[str]]
    sudoku_mode: bool
    grid_utils: GridUtils
    state: KropkiPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        options = [line.upper() for line in lines if line.startswith("!")]
        lines = [
            line
            for line in lines
            if line and not line.startswith("#") and not line.startswith("!")
        ]

        rows_data = [lines[i].replace(" ", "") for i in range(0, len(lines), 2)]
        cols_data = [lines[i].replace(" ", "") for i in range(1, len(lines), 2)]

        initial_grid = [
            [int(row[j]) if row[j] not in "0." else None for j in range(0, len(row), 2)]
            for row in rows_data
        ]
        between_columns = [[row[j] for j in range(1, len(row), 2)] for row in rows_data]
        between_rows = cols_data

        sudoku_mode = "!SUDOKU" in options

        return cls(initial_grid, between_columns, between_rows, sudoku_mode)

    def __init__(
        self, initial_grid, between_columns, between_rows, sudoku_mode, state=None
    ):
        self.initial_grid = initial_grid
        self.between_columns = between_columns
        self.between_rows = between_rows
        self.sudoku_mode = sudoku_mode
        self.grid_utils = GridUtils(len(self.initial_grid), len(self.initial_grid))
        self.state = state

        if state is None:
            self.initialize_state()

    def initialize_state(self):
        self.state = KropkiPuzzleState(
            grid=[
                [None for _ in range(self.grid_utils.rows)]
                for _ in range(self.grid_utils.rows)
            ],
            conflict_cells=[
                [
                    [0 for _ in range(self.grid_utils.rows + 1)]
                    for _ in range(self.grid_utils.rows)
                ]
                for _ in range(self.grid_utils.rows)
            ],
        )

        for r, c in self.grid_utils.iter_grid():
            cell = self.initial_grid[r][c]
            if cell is not None:
                self.set_value((r, c), cell)

    def __str__(self):
        res = []
        for r, row in enumerate(self.state.grid):
            for c, cell in enumerate(row):
                res.append(str(cell) if cell is not None else ".")
                if c + 1 < self.grid_utils.rows:
                    constraint = self.get_constraint_between(r, c, r, c + 1)
                    res.append(f" {constraint} ")

            if r + 1 < self.grid_utils.rows:
                res.append("\n")
                for c, cell in enumerate(row):
                    constraint = self.get_constraint_between(r, c, r + 1, c)
                    res.append(constraint)
                    if c + 1 < self.grid_utils.rows:
                        res.append("   ")
                res.append("\n")

        return "".join(res)

    @cached_property
    def sudoku_square_size(self):
        return isqrt(self.grid_utils.rows)

    def get_constraint_between(self, r, c, new_r, new_c):
        if r == new_r:
            return self.between_columns[r][min(c, new_c)]
        return self.between_rows[min(r, new_r)][c]

    @cache
    def get_constraint_conflicts(self, value, constraint):
        if constraint == ".":
            return set()

        conflicts = set(range(1, self.grid_utils.rows + 1))

        if constraint == "+":
            conflicts.discard(value - 1)
            conflicts.discard(value + 1)
        elif constraint == "x":
            if value % 2 == 0:
                conflicts.discard(value // 2)
            conflicts.discard(value * 2)
        else:
            raise ValueError(f"Unknown constraint {constraint}")

        return conflicts

    def iter_values(self):
        yield from range(1, self.grid_utils.rows + 1)

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def can_set(self, location, value):
        r, c = location
        return self.state.conflict_cells[r][c][value] == 0

    def _update_conflicts(self, r, c, value, delta):
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            for new_r, new_c in self.grid_utils.ray_iter(r, c, dr, dc):
                self.state.conflict_cells[new_r][new_c][value] += delta

            new_r, new_c = r + dr, c + dc
            if not self.grid_utils.in_range(new_r, new_c):
                continue

            constraint = self.get_constraint_between(r, c, new_r, new_c)
            for conflict in self.get_constraint_conflicts(value, constraint):
                self.state.conflict_cells[new_r][new_c][conflict] += delta

        if not self.sudoku_mode:
            return

        square_r, square_c = (
            r - r % self.sudoku_square_size,
            c - c % self.sudoku_square_size,
        )
        for dr, dc in product(range(self.sudoku_square_size), repeat=2):
            new_r, new_c = square_r + dr, square_c + dc
            if new_r == r and new_c == c:
                continue

            self.state.conflict_cells[new_r][new_c][value] += delta

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_conflicts(r, c, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_conflicts(r, c, value, -1)
