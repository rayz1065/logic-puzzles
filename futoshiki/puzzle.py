from functools import cached_property, cache
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class FutoshikiPuzzleState(PuzzleState):
    def __init__(self, grid, found_by_row, found_by_col, hints):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.hints = hints


class FutoshikiPuzzle(Puzzle):
    """https://en.wikipedia.org/wiki/Futoshiki"""

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        initial_grid = [
            [
                int(lines[i][j]) if lines[i][j] != "." else None
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
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid))
        self.state = state

        self.cell_constraints = {(r, c): [] for r, c in self.grid_utils.iter_grid()}

        for r, c in self.grid_utils.iter_grid():
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                constraint = self.get_constraint_between(r, c, new_r, new_c)
                if constraint == ".":
                    continue

                self.cell_constraints[r, c].append((new_r, new_c, constraint))

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "."
            return str(self.state.grid[r][c])

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

    def initialize_state(self):
        self.state = FutoshikiPuzzleState(
            grid=[[None] * self.grid_utils.rows for _ in range(self.grid_utils.rows)],
            found_by_row={
                (r, value): 0
                for r in range(self.grid_utils.rows)
                for value in self.iter_values()
            },
            found_by_col={
                (c, value): 0
                for c in range(self.grid_utils.rows)
                for value in self.iter_values()
            },
            hints={
                (r, c, value): None
                for r in range(self.grid_utils.rows)
                for c in range(self.grid_utils.cols)
                for value in self.iter_values()
            },
        )

        for r, c in self.grid_utils.iter_grid():
            value = self.initial_grid[r][c]
            if value is None:
                continue

            self.set_value(("grid", (r, c)), value)

    @cache
    def get_constraint_between(self, r, c, r2, c2):
        opposite_constraints_map = {"v": "^", "^": "v", "<": ">", ">": "<", ".": "."}

        if r == r2:
            res = self.between_cols[r][min(c, c2)]
        elif c == c2:
            res = self.between_rows[min(r, r2)][c]
        else:
            raise ValueError("No constraint between non-adjacent cells")

        res = res if (r, c) < (r2, c2) else opposite_constraints_map[res]
        return res

    def check_constraint(self, left, right, constraint):
        if constraint == ".":
            return True

        if constraint in ("<", "^"):
            return left < right
        elif constraint in (">", "v"):
            return left > right
        else:
            raise ValueError(f"Unknown constraint {constraint}")

    def iter_values(self):
        yield from range(1, self.grid_utils.rows + 1)

    def iter_locations(self):
        for r, c in self.grid_utils.iter_grid():
            yield ("grid", (r, c))
        for r, c in self.grid_utils.iter_grid():
            for value in self.iter_values():
                yield ("hint", (r, c, value))

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

    def get_valid_values(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, value = location_data
            return [value for value in (0, 1) if self.can_set(location, value)]

        return [value for value in self.iter_values() if self.can_set(location, value)]

    def get_value_bounds(self, r, c):
        if self.state.grid[r][c] is not None:
            return self.state.grid[r][c], self.state.grid[r][c]

        # recover the bounds from the hints
        min_value = self.grid_utils.rows * 2
        max_value = -1
        for value in self.iter_values():
            if self.state.hints[r, c, value] == 0:
                continue

            min_value = min(min_value, value)
            max_value = max(max_value, value)

        return min_value, max_value

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
        if self.state.hints[r, c, value] == 0:
            return False

        if self.state.found_by_col[c, value] != 0:
            return False
        if self.state.found_by_row[r, value] != 0:
            return False

        # take advantage of the hints to figure out whether this cell can be
        # set to this value, this creates a feedback look that greatly speeds
        # up the solving process
        for new_r, new_c, constraint in self.cell_constraints[r, c]:
            new_min, new_max = self.get_value_bounds(new_r, new_c)
            if not self.check_constraint(
                value, new_min, constraint
            ) and not self.check_constraint(value, new_max, constraint):
                return False

        return True

    def _update_value(self, r, c, value, delta):
        self.state.found_by_row[r, value] += delta
        self.state.found_by_col[c, value] += delta

    def set_value(self, location, value):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            self.state.hints[r, c, hint_value] = value
            return

        r, c = location_data
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

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
        self._update_value(r, c, value, -1)
