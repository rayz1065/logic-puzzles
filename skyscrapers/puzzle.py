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

    rows: tuple[list[int], list[int]]
    cols: tuple[list[int], list[int]]

    @classmethod
    def from_string(cls, string):
        lines = [line.strip() for line in string.split("\n")]
        lines = [
            [int(x) if x not in ["0", "."] else None for x in line.split()]
            for line in lines
            if line and not line.startswith("#")
        ]

        return cls(tuple(lines[:2]), tuple(lines[2:]))

    def __init__(self, rows, cols, state=None):
        self.rows = rows
        self.cols = cols
        self.grid_utils = GridUtils(len(self.rows[0]), len(self.rows[0]))
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

    def __str__(self):
        def stringify_hint(hint):
            return "." if hint is None else str(hint)

        res = []
        res.append("  " + " ".join(stringify_hint(x) for x in self.cols[0]))
        for r, row in enumerate(self.state.grid):
            res.append(
                stringify_hint(self.rows[0][r])
                + " "
                + " ".join("." if x is None else str(x + 1) for x in row)
                + " "
                + stringify_hint(self.rows[1][r])
            )
        res.append("  " + " ".join(stringify_hint(x) for x in self.cols[1]))

        return "\n".join(res)

    @property
    def grid_size(self):
        return len(self.rows[0])

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
            (self.rows[0][r], (r, 0, 0, 1)),
            (self.rows[1][r], (r, self.grid_utils.rows - 1, 0, -1)),
            (self.cols[0][c], (0, c, 1, 0)),
            (self.cols[1][c], (self.grid_utils.rows - 1, c, -1, 0)),
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
        lower = self._compute_vision_bound(cells, True)
        upper = self._compute_vision_bound(cells, False)

        return lower, upper

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
                for value in range(current + 1, self.grid_utils.rows):
                    if value not in cells:
                        current = value
                        vision += 1
                        break

        return vision
