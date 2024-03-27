from functools import cache
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils
from logic_puzzles.constraints import CountConstraint


class BinairoPuzzleState(PuzzleState):
    grid: list[list[int]]
    found_by_row: dict[tuple[int, int], int | None]
    found_by_col: dict[tuple[int, int], int | None]
    found_row_codes: dict[tuple[int], int]
    found_col_codes: dict[tuple[int], int]

    def __init__(
        self, grid, found_by_row, found_by_col, found_row_codes, found_col_codes
    ):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.found_row_codes = found_row_codes
        self.found_col_codes = found_col_codes


class BinairoPuzzle(Puzzle):
    initial_grid: list[list[int | None]]
    grid_utils: GridUtils
    state: BinairoPuzzleState
    row_constraint: CountConstraint
    col_constraint: CountConstraint

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        initial_grid = [[int(x) if x != "." else None for x in line] for line in lines]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))
        self.state = state
        self.row_constraint = CountConstraint(
            self.grid_utils.cols // 2, self.grid_utils.cols
        )
        self.col_constraint = CountConstraint(
            self.grid_utils.rows // 2, self.grid_utils.rows
        )

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "_"
            return str(self.state.grid[r][c])

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        self.state = BinairoPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            found_by_row={
                (r, value): 0
                for r in range(self.grid_utils.rows)
                for value in self.iter_values()
            },
            found_by_col={
                (c, value): 0
                for c in range(self.grid_utils.cols)
                for value in self.iter_values()
            },
            found_row_codes=dict(),
            found_col_codes=dict(),
        )

        for r, c in self.grid_utils.iter_grid():
            value = self.initial_grid[r][c]
            if value is None:
                continue

            self.set_value((r, c), value)

    def iter_values(self):
        yield from (0, 1)

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def check_not_three_adjacent(self, r, c, dr, dc):
        if not self.grid_utils.in_range(r, c) or not self.grid_utils.in_range(
            r + dr * 2, c + dc * 2
        ):
            return True

        values = [
            self.state.grid[new_r][new_c]
            for new_r, new_c in self.grid_utils.ray_iter(r, c, dr, dc, 3)
        ]

        if None in values:
            return True

        return len(set(values)) > 1

    def can_set(self, location, value):
        r, c = location

        res = True
        self.set_value(location, value)

        # same number of zeros and ones in each row and column
        if res and not self.row_constraint.check(
            self.state.found_by_row[r, 0], self.state.found_by_row[r, 1]
        ):
            res = False

        if res and not self.col_constraint.check(
            self.state.found_by_col[c, 0], self.state.found_by_col[c, 1]
        ):
            res = False

        # no 3 identical cells adjacent cells
        for distance in range(-2, 1):
            if res and not self.check_not_three_adjacent(r + distance, c, 1, 0):
                res = False
                break

            if res and not self.check_not_three_adjacent(r, c + distance, 0, 1):
                res = False
                break

        # no two identical rows or columns
        if (
            res
            and self.state.found_by_row[r, 0] + self.state.found_by_row[r, 1]
            == self.grid_utils.cols
        ):
            res = self.state.found_row_codes[self.get_row_code(r)] == 1

        if (
            res
            and self.state.found_by_col[c, 0] + self.state.found_by_col[c, 1]
            == self.grid_utils.rows
        ):
            res = self.state.found_col_codes[self.get_col_code(c)] == 1

        self.unset_value(location)

        return res

    def get_row_code(self, r):
        return tuple(self.state.grid[r][c] for c in range(self.grid_utils.cols))

    def get_col_code(self, c):
        return tuple(self.state.grid[r][c] for r in range(self.grid_utils.rows))

    def _update_value(self, r, c, value, delta):
        self.state.found_by_row[r, value] += delta
        self.state.found_by_col[c, value] += delta

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

        if (
            self.state.found_by_row[r, 0] + self.state.found_by_row[r, 1]
            == self.grid_utils.cols
        ):
            self.state.found_row_codes.setdefault(self.get_row_code(r), 0)
            self.state.found_row_codes[self.get_row_code(r)] += 1
        if (
            self.state.found_by_col[c, 0] + self.state.found_by_col[c, 1]
            == self.grid_utils.rows
        ):
            self.state.found_col_codes.setdefault(self.get_col_code(c), 0)
            self.state.found_col_codes[self.get_col_code(c)] += 1

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert value is not None

        if (
            self.state.found_by_row[r, 0] + self.state.found_by_row[r, 1]
            == self.grid_utils.cols
        ):
            self.state.found_row_codes[self.get_row_code(r)] -= 1
        if (
            self.state.found_by_col[c, 0] + self.state.found_by_col[c, 1]
            == self.grid_utils.rows
        ):
            self.state.found_col_codes[self.get_col_code(c)] -= 1

        self.state.grid[r][c] = None
        self._update_value(r, c, value, -1)
