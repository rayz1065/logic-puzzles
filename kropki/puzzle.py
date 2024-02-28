from math import isqrt
from logic_puzzles.puzzle import Puzzle, PuzzleState
from functools import cached_property


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


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

        return cls(initial_grid, between_columns, between_rows, sudoku_mode=sudoku_mode)

    def __init__(
        self, initial_grid, between_columns, between_rows, sudoku_mode, state=None
    ):
        self.initial_grid = initial_grid
        self.between_columns = between_columns
        self.between_rows = between_rows
        self.sudoku_mode = sudoku_mode

        if state is None:
            grid = [
                [None for _ in range(self.grid_size)] for _ in range(self.grid_size)
            ]
            conflict_cells = [
                [[0 for _ in range(self.grid_size + 1)] for _ in range(self.grid_size)]
                for _ in range(self.grid_size)
            ]
            self.state = KropkiPuzzleState(grid, conflict_cells)
            self._initialize_state()
        else:
            self.state = state

    def _initialize_state(self):
        for r, row in enumerate(self.initial_grid):
            for c, cell in enumerate(row):
                if cell is None:
                    continue
                self.set_value(r, c, cell)

    def __str__(self):
        res = []
        for r, row in enumerate(self.state.grid):
            for c, cell in enumerate(row):
                res.append(str(cell) if cell is not None else ".")
                if c + 1 < self.grid_size:
                    constraint = self.get_constraint_between(r, c, r, c + 1)
                    res.append(f" {constraint} ")

            if r + 1 < self.grid_size:
                res.append("\n")
                for c, cell in enumerate(row):
                    constraint = self.get_constraint_between(r, c, r + 1, c)
                    res.append(constraint)
                    if c + 1 < self.grid_size:
                        res.append("   ")
                res.append("\n")

        return "".join(res)

    @cached_property
    def grid_size(self):
        return len(self.between_columns)

    @cached_property
    def sudoku_square_size(self):
        return isqrt(self.grid_size)

    def get_constraint_between(self, r, c, new_r, new_c):
        if r == new_r:
            return self.between_columns[r][min(c, new_c)]
        return self.between_rows[min(r, new_r)][c]

    def in_range(self, r, c):
        return 0 <= r < self.grid_size and 0 <= c < self.grid_size

    def get_constraint_conflicts(self, value, constraint):
        if constraint == ".":
            return set()

        conflicts = set(range(1, self.grid_size + 1))

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

    def is_valid(self, r, c, value):
        return self.state.conflict_cells[r][c][value] == 0

    def _update_conflicts(self, r, c, value, delta):
        dirty = set()

        for dr, dc in DIRECTIONS:
            for dist in range(1, self.grid_size):
                new_r, new_c = r + dr * dist, c + dc * dist
                if not self.in_range(new_r, new_c):
                    break

                self.state.conflict_cells[new_r][new_c][value] += delta

                if (
                    self.state.conflict_cells[new_r][new_c][value] == delta
                    and self.state.grid[new_r][new_c] is None
                ):
                    dirty.add((new_r, new_c))

            new_r, new_c = r + dr, c + dc
            if not self.in_range(new_r, new_c):
                continue

            constraint = self.get_constraint_between(r, c, new_r, new_c)
            for conflict in self.get_constraint_conflicts(value, constraint):
                self.state.conflict_cells[new_r][new_c][conflict] += delta

                if (
                    self.state.conflict_cells[new_r][new_c][value] == delta
                    and self.state.grid[new_r][new_c] is None
                ):
                    dirty.add((new_r, new_c))

        if self.sudoku_mode:
            square_r, square_c = (
                r // self.sudoku_square_size,
                c // self.sudoku_square_size,
            )
            for dr in range(self.sudoku_square_size):
                for dc in range(self.sudoku_square_size):
                    if dr == dc == 0:
                        continue

                    new_r, new_c = (
                        square_r * self.sudoku_square_size + dr,
                        square_c * self.sudoku_square_size + dc,
                    )

                    self.state.conflict_cells[new_r][new_c][value] += delta
                    if (
                        self.state.conflict_cells[new_r][new_c][value] == delta
                        and self.state.grid[new_r][new_c] is None
                    ):
                        dirty.add((new_r, new_c))

        return dirty

    def set_value(self, r, c, value):
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        return self._update_conflicts(r, c, value, 1)

    def unset_value(self, r, c):
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_conflicts(r, c, value, -1)
