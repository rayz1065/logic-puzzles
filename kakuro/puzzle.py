from itertools import product
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class KakuroPuzzleState(PuzzleState):
    numbers_grid: list[list[int]]
    conflicts: list[list[list[int]]]
    constraints_sum: list[int]

    def __init__(self, numbers_grid, conflicts, constraints_sum):
        self.numbers_grid = numbers_grid
        self.conflicts = conflicts
        self.constraints_sum = constraints_sum


class KakuroCell:
    def __init__(self, is_wall=False, horizontal=None, vertical=None):
        self.is_wall = is_wall
        self.horizontal = horizontal
        self.vertical = vertical

    def set_horizontal(self, constraint):
        self.horizontal = constraint
        self.is_wall = True

    def set_vertical(self, constraint):
        self.vertical = constraint
        self.is_wall = True

    def __str__(self):
        return "#" if self.is_wall else "."


class KakuroPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Kakuro"""

    grid: list[list[KakuroCell]]
    constraints: list[tuple[int, list[tuple[int, int]]]]
    constraint_indexes: dict[tuple[int, int], list[int]]
    state: KakuroPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        grid_size = len(lines) // 2
        horizontal = lines[:grid_size]
        vertical = lines[grid_size:]

        grid = [[KakuroCell() for _ in range(grid_size)] for _ in range(grid_size)]

        for r, line in enumerate(horizontal):
            for c, cell in enumerate(line):
                if cell != ".":
                    grid[r][c].set_horizontal(int(cell))

        for r, line in enumerate(vertical):
            for c, cell in enumerate(line):
                assert (grid[r][c].horizontal is None) == (
                    cell == "."
                ), f"Vertical and horizontal cells disagree for {r},{c}"
                if cell != ".":
                    grid[r][c].set_vertical(int(cell))

        return cls(grid)

    def __init__(self, grid, state=None):
        self.grid = grid
        self.grid_utils = GridUtils(len(grid), len(grid[0]))
        self.state = state
        self.constraints = []
        for r, c in self.grid_utils.iter_grid():
            # we can ignore zeros as well
            if grid[r][c].horizontal:
                cells = []
                for new_r, new_c in self.grid_utils.ray_iter(r, c + 1, 0, 1):
                    if grid[new_r][new_c].horizontal is not None:
                        break
                    cells.append((new_r, new_c))
                self.constraints.append((grid[r][c].horizontal, cells))

            if grid[r][c].vertical:
                cells = []
                for new_r, new_c in self.grid_utils.ray_iter(r + 1, c, 1, 0):
                    if grid[new_r][new_c].vertical is not None:
                        break
                    cells.append((new_r, new_c))
                self.constraints.append((grid[r][c].vertical, cells))

        self.constraint_indexes = {}
        for i, (constraint, cells) in enumerate(self.constraints):
            for r, c in cells:
                self.constraint_indexes.setdefault((r, c), []).append(i)

        if state is None:
            self.initialize_state()

    def initialize_state(self):
        self.state = KakuroPuzzleState(
            numbers_grid=[
                [None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)
            ],
            conflicts=[
                [[0] * 10 for c in range(self.grid_utils.cols)]
                for r in range(self.grid_utils.rows)
            ],
            constraints_sum=[0] * len(self.constraints),
        )

    def __str__(self):
        return "\n".join(
            " ".join(
                (str(y) if y is not None else str(x)) for y, x in zip(state_line, line)
            )
            for state_line, line in zip(self.state.numbers_grid, self.grid)
        )

    def iter_values(self):
        yield from range(1, 10)

    def iter_locations(self):
        for r, c in self.grid_utils.iter_grid():
            if not self.grid[r][c].is_wall:
                yield r, c

    def can_set(self, location, value):
        r, c = location
        if self.state.conflicts[r][c][value]:
            return False

        for i in self.constraint_indexes[r, c]:
            constraint, cells = self.constraints[i]
            free_cells = (
                sum(
                    1
                    for other_r, other_c in cells
                    if self.state.numbers_grid[other_r][other_c] is None
                )
            ) - 1

            new_sum = self.state.constraints_sum[i] + value

            # estimate the lower bound for the new sum, 1 + 2 + ...
            # this does not consider values that are not available, for simplicity
            sum_up_to_free_cells = free_cells * (free_cells + 1) // 2
            new_sum_lb = new_sum + sum_up_to_free_cells

            # do the same for the upper bound, 9 + 8 + ...
            new_sum_ub = new_sum + 10 * free_cells - sum_up_to_free_cells

            if not (new_sum_lb <= constraint <= new_sum_ub):
                return False

        return True

    def _update_value(self, r, c, value, delta):
        for i in self.constraint_indexes[r, c]:
            self.state.constraints_sum[i] += value * delta
            cells = self.constraints[i][1]
            for other_r, other_c in cells:
                self.state.conflicts[other_r][other_c][value] += delta

    def get_value(self, location):
        r, c = location
        return self.state.numbers_grid[r][c]

    def set_value(self, location, value):
        r, c = location
        assert self.state.numbers_grid[r][c] is None
        self.state.numbers_grid[r][c] = value
        self._update_value(r, c, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.numbers_grid[r][c]
        assert value is not None
        self.state.numbers_grid[r][c] = None
        self._update_value(r, c, value, -1)
