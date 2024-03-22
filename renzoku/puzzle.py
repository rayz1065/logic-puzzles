from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils

# fmt: off
SUDOKU_VALUES = [
    "1","2","3","4","5","6","7","8","9",
    "A","B","C","D","E","F","G",
]
# fmt: on


class RenzokuPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_row: dict[tuple[int, int], int]
    found_by_col: dict[tuple[int, int], int]
    hints_grid: dict[tuple[int, int, int], int | None]

    def __init__(self, grid, found_by_row, found_by_col, hints_grid):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.hints_grid = hints_grid


class RenzokuPuzzle(Puzzle):
    initial_grid: list[list[int | None]]
    between_rows: list[list[str]]
    between_cols: list[list[str]]
    state: RenzokuPuzzleState
    grid_utils: GridUtils

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        initial_grid = [
            [
                SUDOKU_VALUES.index(lines[i][j]) if lines[i][j] != "." else None
                for j in range(0, len(lines), 2)
            ]
            for i in range(0, len(lines), 2)
        ]
        between_cols = [
            [lines[i][j] for j in range(1, len(lines), 2)]
            for i in range(0, len(lines), 2)
        ]
        between_rows = [lines[i] for i in range(1, len(lines), 2)]

        return cls(initial_grid, between_rows, between_cols)

    def __init__(self, initial_grid, between_rows, between_cols, state=None):
        self.initial_grid = initial_grid
        self.between_rows = between_rows
        self.between_cols = between_cols
        self.state = state
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "."
            return SUDOKU_VALUES[self.state.grid[r][c]]

        result = []
        for r in range(self.grid_utils.rows):
            row = []
            for c in range(self.grid_utils.cols):
                row.append(stringify_cell(r, c))
                if c + 1 < self.grid_utils.cols:
                    row.append(self.get_constraint_between(r, c, r, c + 1))
            result.append(" ".join(row))

            if r + 1 < self.grid_utils.rows:
                result.append(
                    "   ".join(
                        self.get_constraint_between(r, c, r + 1, c)
                        for c in range(self.grid_utils.rows)
                    )
                )

        return "\n".join(result)

    def get_constraint_between(self, r, c, r2, c2):
        if r == r2:
            return self.between_cols[r][min(c, c2)]
        elif c == c2:
            return self.between_rows[min(r, r2)][c]
        else:
            raise ValueError("No constraint between non-adjacent cells")

    def initialize_state(self):
        self.state = RenzokuPuzzleState(
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
            hints_grid={
                (r, c, value): None
                for r, c in self.grid_utils.iter_grid()
                for value in self.iter_values()
            },
        )

        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] is not None:
                self.set_value(("grid", (r, c)), self.initial_grid[r][c])

    def get_valid_values(self, location):
        location_type, location_data = location
        if location_type == "hint":
            return [value for value in (0, 1) if self.can_set(location, value)]

        return [value for value in self.iter_values() if self.can_set(location, value)]

    def iter_values(self):
        yield from range(self.grid_utils.rows)

    def iter_locations(self):
        for r, c in self.grid_utils.iter_grid():
            yield "grid", (r, c)
        for r, c in self.grid_utils.iter_grid():
            for value in self.iter_values():
                yield "hint", (r, c, value)

    def get_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            if self.state.grid[r][c] is not None:
                return 1 if self.state.grid[r][c] == hint_value else 0
            return self.state.hints_grid[r, c, hint_value]

        r, c = location_data
        return self.state.grid[r][c]

    def check_constraint(self, left, right, constraint):
        if constraint == "O":
            return abs(left - right) == 1
        return abs(left - right) > 1

    def can_set(self, location, value):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            if value == 0:
                return True
            if self.state.grid[r][c] is not None:
                return 1 if self.state.grid[r][c] == hint_value else 0

            return self.can_set(("grid", (r, c)), hint_value)

        r, c = location_data
        if self.state.found_by_row[r, value] > 0:
            return False
        if self.state.found_by_col[c, value] > 0:
            return False
        if self.state.hints_grid[r, c, value] == 0:
            return False

        for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
            constraint = self.get_constraint_between(r, c, new_r, new_c)
            new_value = self.state.grid[new_r][new_c]
            if new_value is not None:
                if not self.check_constraint(value, new_value, constraint):
                    return False
                continue

            if constraint == "O":
                if all(
                    not (0 <= x < self.grid_utils.rows)
                    or self.state.hints_grid[new_r, new_c, x] == 0
                    for x in (value - 1, value + 1)
                ):
                    return False
            else:
                if all(
                    self.state.hints_grid[new_r, new_c, x] == 0 or abs(x - value) <= 1
                    for x in self.iter_values()
                ):
                    return False

        return True

    def _update_grid(self, r, c, value, delta):
        self.state.found_by_row[r, value] += delta
        self.state.found_by_col[c, value] += delta

    def set_value(self, location, value):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            assert self.state.hints_grid[r, c, hint_value] is None
            self.state.hints_grid[r, c, hint_value] = value
            return

        r, c = location_data
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_grid(r, c, value, 1)

    def unset_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            assert self.state.hints_grid[r, c, hint_value] is not None
            self.state.hints_grid[r, c, hint_value] = None
            return

        r, c = location_data
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_grid(r, c, value, -1)
