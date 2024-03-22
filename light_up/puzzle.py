from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils, ORTHOGONAL_DIRECTIONS, ALL_DIRECTIONS
from logic_puzzles.constraints import CountConstraint


class LightUpPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    lit: list[list[int]]
    available_lights: list[list[int]]
    found_by_box: dict[tuple[int, int], int]  # (box_id, value) -> frequency

    def __init__(self, grid, lit, available_lights, found_by_box):
        self.grid = grid
        self.lit = lit
        self.available_lights = available_lights
        self.found_by_box = found_by_box


class LightUpPuzzle(Puzzle):
    """https://en.wikipedia.org/wiki/Light_Up_(puzzle)"""

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.lower().split() for x in lines if x and not x.startswith("#")]
        initial_grid = [[int(x) if x.isdigit() else x for x in line] for line in lines]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.state = state
        self.grid_utils = GridUtils(len(self.initial_grid), len(self.initial_grid[0]))
        self.box_constraints = {}
        for r, c in self.grid_utils.iter_grid():
            cell = self.initial_grid[r][c]
            if cell == "." or cell == "x":
                continue

            self.box_constraints[r, c] = CountConstraint(
                cell, self.spaces_around_cell(r, c)
            )

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c, cell):
            if self.initial_grid[r][c] != ".":
                return str(self.initial_grid[r][c])
            if cell is None and self.state.lit[r][c] == 0:
                return "."
            if cell is None:
                return "*"
            return "O" if cell else "/"

        return "\n".join(
            " ".join(stringify_cell(r, c, cell) for c, cell in enumerate(row))
            for r, row in enumerate(self.state.grid)
        )

    def compute_available_lights(self, r, c):
        if self.initial_grid[r][c] != ".":
            return 0

        res = 1
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            for new_r, new_c in self.grid_utils.ray_iter(r + dr, c + dc, dr, dc):
                if self.initial_grid[new_r][new_c] != ".":
                    break
                res += 1

        return res

    def initialize_state(self):
        self.state = LightUpPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            lit=[[0] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            available_lights=[
                [
                    self.compute_available_lights(r, c)
                    for c in range(self.grid_utils.cols)
                ]
                for r in range(self.grid_utils.rows)
            ],
            found_by_box={
                (box_id, value): 0
                for box_id in self.box_constraints.keys()
                for value in self.iter_values()
            },
        )

    def _update_value(self, location, value, delta):
        r, c = location

        if value == 1:
            self.state.lit[r][c] += delta
        else:
            self.state.available_lights[r][c] -= delta
            assert self.state.available_lights[r][c] >= 0

        for dr, dc in ORTHOGONAL_DIRECTIONS:
            for new_r, new_c in self.grid_utils.ray_iter(r + dr, c + dc, dr, dc):
                if self.initial_grid[new_r][new_c] != ".":
                    break

                if value == 1:
                    self.state.lit[new_r][new_c] += delta
                else:
                    self.state.available_lights[new_r][new_c] -= delta
                    assert self.state.available_lights[new_r][new_c] >= 0

            new_r, new_c = r + dr, c + dc
            if (new_r, new_c) in self.box_constraints:
                self.state.found_by_box[(new_r, new_c), value] += delta

    def spaces_around_cell(self, r, c):
        return sum(
            self.initial_grid[new_r][new_c] == "."
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1)
        )

    def _check_box_satisfiable(self, box_r, box_c):
        box_id = (box_r, box_c)
        if box_id not in self.box_constraints:
            return True

        constraint = self.box_constraints[box_id]
        return constraint.check(
            self.state.found_by_box[box_id, 1], self.state.found_by_box[box_id, 0]
        )

    def can_set(self, location, value):
        r, c = location
        if value == 1 and self.state.lit[r][c] > 0:
            return False

        if value == 0 and self.state.available_lights[r][c] == 1:
            return False

        self.set_value(location, value)

        res = True
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            if not res:
                break

            # check that we don't leave some places in the dark
            new_r, new_c = r + dr, c + dc
            for new_r, new_c in self.grid_utils.ray_iter(r + dr, c + dc, dr, dc):
                if self.initial_grid[new_r][new_c] != ".":
                    break

                if self.state.available_lights[new_r][new_c] == 0:
                    res = False
                    break

            # check that we didn't add too many lights/empty spaces around a box
            box_r, box_c = new_r, new_c
            if not self._check_box_satisfiable(box_r, box_c):
                res = False
                break

        self.unset_value(location)

        return res

    def iter_locations(self):
        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] == ".":
                yield r, c

    def iter_values(self):
        yield from (0, 1)

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
