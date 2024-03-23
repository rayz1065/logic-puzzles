from itertools import product, combinations
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


def compute_all_possible_sums():
    res = {}
    for quantity in range(1, 10):
        for combination in combinations(range(1, 10), quantity):
            x = sum(combination)
            res.setdefault((x, quantity), []).append(combination)

    res[0, 0] = [()]

    return res


ALL_POSSIBLE_SUMS = compute_all_possible_sums()


class KakuroPuzzleState(PuzzleState):
    numbers_grid: list[list[int]]
    constraints_sum: list[int]
    found_by_constraint: dict[tuple[int, int], int]
    hints_grid: dict[tuple[int, int, int], int]

    def __init__(self, numbers_grid, constraints_sum, found_by_constraint, hints_grid):
        self.numbers_grid = numbers_grid
        self.constraints_sum = constraints_sum
        self.found_by_constraint = found_by_constraint
        self.hints_grid = hints_grid


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
        return " " if self.is_wall else "."


class KakuroPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Kakuro"""

    grid: list[list[KakuroCell]]
    constraints: list[tuple[int, list[tuple[int, int]]]]
    state: KakuroPuzzleState
    cell_constraints: dict[tuple[int, int], list[tuple[int, int]]]
    grid_utils: GridUtils

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
        self.constraints = {}
        for r, c in self.grid_utils.iter_grid():
            constraint = grid[r][c].horizontal
            if constraint is not None:
                cells = self.find_constraint_cells(r, c, 0, 1)
                if constraint != 0:
                    self.constraints[r, c, "H"] = (constraint, cells)

            constraint = grid[r][c].vertical
            if constraint is not None:
                cells = self.find_constraint_cells(r, c, 1, 0)
                if constraint != 0:
                    self.constraints[r, c, "V"] = (constraint, cells)

        self.cell_constraints = {}
        for i, (_, cells) in self.constraints.items():
            for r, c in cells:
                self.cell_constraints.setdefault((r, c), []).append(i)

        if state is None:
            self.initialize_state()

    def find_constraint_cells(self, r, c, dr, dc):
        constraint = self.grid[r][c].horizontal if dr == 0 else self.grid[r][c].vertical
        cells = []
        for new_r, new_c in self.grid_utils.ray_iter(r + dr, c + dc, dr, dc):
            if self.grid[new_r][new_c].is_wall:
                break
            cells.append((new_r, new_c))

        if not self.check_sum_possible(len(cells), set(self.iter_values()), constraint):
            raise ValueError(
                f"Impossible sum for constraint {constraint} at {r},{c} with direction {dr},{dc}"
            )

        return cells

    def initialize_state(self):
        self.state = KakuroPuzzleState(
            numbers_grid=[
                [None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)
            ],
            constraints_sum={k: 0 for k in self.constraints},
            found_by_constraint={
                (k, value): 0 for k in self.constraints for value in self.iter_values()
            },
            hints_grid={
                (r, c, value): None
                for r, c in self.grid_utils.iter_grid()
                for value in self.iter_values()
            },
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
                yield "grid", (r, c)
        for r, c in self.grid_utils.iter_grid():
            if self.grid[r][c].is_wall:
                continue
            for value in self.iter_values():
                yield "hint", (r, c, value)

    def check_sum_possible(self, cells_count, available_values, constraint):
        if (constraint, cells_count) not in ALL_POSSIBLE_SUMS:
            return False

        for combination in ALL_POSSIBLE_SUMS[constraint, cells_count]:
            if all(x in available_values for x in combination):
                return True

        return False

    def can_set(self, location, value):
        location_type, location_data = location

        if location_type == "hint":
            if value == 0:
                return True
            r, c, hint_value = location_data
            return self.can_set(("grid", (r, c)), hint_value)

        r, c = location_data
        if self.state.hints_grid[r, c, value] == 0:
            return False

        res = True

        for i in self.cell_constraints[r, c]:
            if self.state.found_by_constraint[i, value] > 0:
                res = False
                break

            constraint, cells = self.constraints[i]
            free_cells = [
                (other_r, other_c)
                for other_r, other_c in cells
                if (other_r, other_c) != (r, c)
                and self.state.numbers_grid[other_r][other_c] is None
            ]
            available_values = set(
                new_value
                for other_r, other_c in free_cells
                for new_value in self.iter_values()
                if self.state.hints_grid[other_r, other_c, new_value] is None
                and new_value != value
            )
            new_sum = self.state.constraints_sum[i] + value

            if not self.check_sum_possible(
                len(free_cells), available_values, constraint - new_sum
            ):
                res = False
                break

        return res

    def _update_value(self, r, c, value, delta):
        for i in self.cell_constraints[r, c]:
            self.state.constraints_sum[i] += value * delta
            self.state.found_by_constraint[i, value] += delta

    def get_valid_values(self, location):
        location_type, location_data = location
        if location_type == "hint":
            return [x for x in (0, 1) if self.can_set(location, x)]
        return super().get_valid_values(location)

    def get_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            if self.state.numbers_grid[r][c] is not None:
                return 1 if self.state.numbers_grid[r][c] == hint_value else 0
            return self.state.hints_grid[r, c, hint_value]

        r, c = location_data
        return self.state.numbers_grid[r][c]

    def set_value(self, location, value):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            assert self.state.hints_grid[r, c, hint_value] is None
            self.state.hints_grid[r, c, hint_value] = value
            return

        r, c = location_data
        assert self.state.numbers_grid[r][c] is None
        self.state.numbers_grid[r][c] = value
        self._update_value(r, c, value, 1)

    def unset_value(self, location):
        location_type, location_data = location
        if location_type == "hint":
            r, c, hint_value = location_data
            value = self.state.hints_grid[r, c, hint_value]
            assert value is not None
            self.state.hints_grid[r, c, hint_value] = None
            return

        r, c = location_data
        value = self.state.numbers_grid[r][c]
        assert value is not None
        self.state.numbers_grid[r][c] = None
        self._update_value(r, c, value, -1)
