from functools import cache
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class SkyscrapersPuzzleState(PuzzleState):
    grid: list[list[int]]
    found_by_row: list[list[int]]  # row -> value -> frequency
    found_by_col: list[list[int]]  # col -> value -> frequency

    def __init__(self, grid, found_by_row, found_by_col):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col


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
        )

        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] != ".":
                value = int(self.initial_grid[r][c]) - 1
                self.set_value((r, c), value)

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

    def get_valid_values(self, location):
        return [x for x in range(self.grid_utils.rows) if self.can_set(location, x)]

    def can_set(self, location, value):
        r, c = location
        if (
            self.state.found_by_row[r][value] > 0
            or self.state.found_by_col[c][value] > 0
        ):
            return False

        def cells_in_ray(r, c, dr, dc):
            return [
                self.state.grid[new_r][new_c]
                for new_r, new_c in self.grid_utils.ray_iter(r, c, dr, dc)
            ]

        self.set_value(location, value)

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

            cells = cells_in_ray(*ray_bounds)
            lower, upper = self.compute_vision_bounds(cells)
            if not (lower <= bound <= upper):
                res = False
                break

        self.unset_value(location)

        return res

    def compute_vision_bounds(self, cells):
        lower = self._compute_vision_bound(tuple(cells), True)
        upper = self._compute_vision_bound(tuple(cells), False)

        return lower, upper

    @cache
    def _compute_vision_bound(self, cells, compute_lower):
        """Computes the specified bound for the vision in the ray"""
        current = -1
        vision = 0

        for cell in cells:
            if cell is not None:
                if cell > current:
                    current = cell
                    vision += 1
            elif compute_lower:
                if (self.grid_utils.rows - 1) not in cells:
                    # we can place the highest building here and compute
                    # the lower bound precisely
                    return vision + 1

                # this looks wrong but it's a valid heuristic:
                # we are looking for the tallest building that can be placed here but
                # we don't update the vision since it might be a suboptimal choice
                # since we are computing a lower bound this is fine
                for value in reversed(range(current + 1, self.grid_utils.rows)):
                    if value not in cells:
                        current = value
                        # NOTE: do not update vision here
                        break
            else:
                # we try to place the first building higher than current
                # we update current in a conservative way since this may be a suboptimal choice
                for value in range(current + 1, self.grid_utils.rows):
                    if value not in cells:
                        current = current + 1
                        vision += 1
                        break

        return vision
