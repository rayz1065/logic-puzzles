from functools import cache
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils
from .vision_computer import compute_vision_lower_bound, compute_vision_upper_bound


class SkyscrapersPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_row: list[list[int]]  # row -> value -> frequency
    found_by_col: list[list[int]]  # col -> value -> frequency
    hints: dict[tuple[int, int, int], int | None]  # (r, c, value) -> 0 for absent

    def __init__(self, grid, found_by_row, found_by_col, hints):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.hints = hints


class SkyscrapersPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Grattacieli"""

    row_counts: tuple[list[int], list[int]]
    col_counts: tuple[list[int], list[int]]
    initial_grid: list[list[str]]
    state: SkyscrapersPuzzleState
    grid_utils: GridUtils

    @classmethod
    def from_string(cls, string):
        lines = [line.strip() for line in string.split("\n")]
        lines = [line.split() for line in lines if line and not line.startswith("#")]

        def parse_counts(counts):
            return [int(x) if x != "." and x != "0" else None for x in counts]

        col_counts = (parse_counts(lines[0]), parse_counts(lines[-1]))
        row_counts = (
            parse_counts([x[0] for x in lines[1:-1]]),
            parse_counts([x[-1] for x in lines[1:-1]]),
        )
        initial_grid = [x[1:-1] for x in lines[1:-1]]

        return cls(initial_grid, row_counts, col_counts)

    def __init__(self, initial_grid, row_counts, col_counts, state=None):
        self.initial_grid = initial_grid
        self.row_counts = row_counts
        self.col_counts = col_counts
        self.grid_utils = GridUtils(len(self.row_counts[0]), len(self.row_counts[0]))
        self.state = state

        if state is None:
            self.initialize_state()

    def initialize_state(self):
        grid = [[None] * self.grid_utils.rows for _ in range(self.grid_utils.rows)]
        self.state = SkyscrapersPuzzleState(
            grid=grid,
            found_by_row=[
                ([0] * self.grid_utils.rows) for _ in range(self.grid_utils.rows)
            ],
            found_by_col=[
                ([0] * self.grid_utils.rows) for _ in range(self.grid_utils.rows)
            ],
            hints={
                (r, c, value): None
                for r, c in self.grid_utils.iter_grid()
                for value in range(self.grid_utils.rows)
            },
        )

        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] != ".":
                value = int(self.initial_grid[r][c]) - 1
                self.set_value(("grid", (r, c)), value)

    def __str__(self):
        def stringify_hint(hint):
            return "." if hint is None else str(hint)

        def stringify_cell(cell):
            return "." if cell is None else str(cell + 1)

        res = []
        res.append("  " + " ".join(map(stringify_hint, self.col_counts[0])))
        for r, row in enumerate(self.state.grid):
            res.append(
                stringify_hint(self.row_counts[0][r])
                + " "
                + " ".join(map(stringify_cell, row))
                + " "
                + stringify_hint(self.row_counts[1][r])
            )
        res.append("  " + " ".join(map(stringify_hint, self.col_counts[1])))

        return "\n".join(res)

    def _update_conflicts(self, r, c, value, delta):
        self.state.found_by_row[r][value] += delta
        self.state.found_by_col[c][value] += delta

    def get_valid_values(self, location):
        location_type, location_data = location
        if location_type == "hint":
            return [x for x in (0, 1) if self.can_set(location, x)]

        return [x for x in self.iter_values() if self.can_set(location, x)]

    def get_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, value = location_data
            if self.state.grid[r][c] == value:
                return 1
            if self.state.grid[r][c] is not None:
                return 0

            return self.state.hints[r, c, value]

        r, c = location_data
        return self.state.grid[r][c]

    def set_value(self, location, value):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            self.state.hints[r, c, hint_value] = value
            return

        r, c = location_data
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_conflicts(r, c, value, 1)

    def unset_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            self.state.hints[r, c, hint_value] = None
            return

        r, c = location_data
        value = self.state.grid[r][c]
        assert value is not None
        self.state.grid[r][c] = None
        self._update_conflicts(r, c, value, -1)

    def iter_values(self):
        yield from range(self.grid_utils.rows)

    def iter_locations(self):
        for r, c in self.grid_utils.iter_grid():
            yield ("grid", (r, c))

        for r, c in self.grid_utils.iter_grid():
            for value in range(self.grid_utils.rows):
                yield ("hint", (r, c, value))

    def _compute_available_mask(self, r, c):
        """computes the availability mask for the location based only on the state"""
        return tuple(
            (
                self.state.found_by_row[r][value] == 0
                and self.state.found_by_col[c][value] == 0
                and self.state.hints[r, c, value] != 0
            )
            for value in range(self.grid_utils.rows)
        )

    def can_set(self, location, value):
        location_type, location_data = location

        if location_type == "hint":
            if value == 0:
                # we always allow the hint to be turned off
                return True

            # we restrict when the hint can be set to 1 to when the grid at the
            # location can be set to the hint value, this way if this check
            # fails we will set the hint to 0 and can use this in a feedback loop
            r, c, hint_value = location_data
            return self.can_set(("grid", (r, c)), hint_value)

        r, c = location_data
        if (
            self.state.found_by_row[r][value] > 0
            or self.state.found_by_col[c][value] > 0
            or self.state.hints[r, c, value] == 0
        ):
            return False

        def buildings_in_ray(r, c, dr, dc):
            return [
                self.state.grid[new_r][new_c]
                for new_r, new_c in self.grid_utils.ray_iter(r, c, dr, dc)
            ]

        self.set_value(location, value)

        # compute the exact bounds of the vision for this row and column
        # this considers availability of the buildings in each location
        # and sets up a feedback loop that takes advantage of the hints
        VISION_BOUNDS_CHECKS = [
            (self.row_counts[0][r], (r, 0, 0, 1)),
            (self.row_counts[1][r], (r, self.grid_utils.rows - 1, 0, -1)),
            (self.col_counts[0][c], (0, c, 1, 0)),
            (self.col_counts[1][c], (self.grid_utils.rows - 1, c, -1, 0)),
        ]

        res = True
        for bound, ray_bounds in VISION_BOUNDS_CHECKS:
            if bound is None:
                continue

            buildings = buildings_in_ray(*ray_bounds)
            available = tuple(
                self._compute_available_mask(new_r, new_c)
                for new_r, new_c in self.grid_utils.ray_iter(*ray_bounds)
            )

            lower, upper = self.compute_vision_bounds(buildings, available)

            if lower is None or not (lower <= bound <= upper):
                res = False
                break

        self.unset_value(location)

        return res

    def compute_vision_bounds(self, cells, available):
        lower = compute_vision_lower_bound(cells, available)
        if lower is None:
            return None, None

        upper = compute_vision_upper_bound(cells, available)

        return lower, upper
