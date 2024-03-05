from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils, ARROWS, ORTHOGONAL_DIRECTIONS, BENDS


class ThermometersPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_col: tuple[list[int], list[int]]
    found_by_row: tuple[list[int], list[int]]
    found_by_thermometer: tuple[list[int], list[int]]

    def __init__(self, grid, found_by_col, found_by_row, found_by_thermometer):
        self.grid = grid
        self.found_by_col = found_by_col
        self.found_by_row = found_by_row
        self.found_by_thermometer = found_by_thermometer


class ThermometersPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Termometri"""

    initial_grid: list[list[str]]
    col_counts: list[int]
    row_counts: list[int]
    grid_utils: GridUtils
    state: ThermometersPuzzleState
    thermometers: list[list[tuple[int, int]]]
    thermometer_directions: list[tuple[int, int] | None]
    cell_thermometer: list[list[tuple[int, int]]]

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        col_counts = list(map(int, lines[0]))
        row_counts = [int(row[0]) for row in lines[1:]]
        initial_grid = [[x.lower() for x in row[1:]] for row in lines[1:]]

        return cls(col_counts, row_counts, initial_grid)

    def __init__(self, col_counts, row_counts, initial_grid, state=None):
        self.col_counts = col_counts
        self.row_counts = row_counts
        self.initial_grid = initial_grid
        self.grid_utils = GridUtils(len(row_counts), len(col_counts))
        self.state = state

        self.thermometers = []
        self.thermometer_directions = []
        self.cell_thermometer = [
            [None for _ in range(self.grid_utils.cols)]
            for _ in range(self.grid_utils.rows)
        ]
        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] == "o":
                self._add_thermometer(r, c)

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(cell):
            if cell is None:
                return "."
            return "O" if cell else "/"

        return "\n".join(
            " ".join(stringify_cell(cell) for c, cell in enumerate(row))
            for r, row in enumerate(self.state.grid)
        )

    def _add_thermometer(self, r, c):
        # find the second cell of the thermometer
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            new_r, new_c = r + dr, c + dc
            if not self.grid_utils.in_range(new_r, new_c):
                continue

            cell = self.initial_grid[new_r][new_c]
            if cell in BENDS and (-dr, -dc) in BENDS[cell]:
                break
            if cell in ARROWS and ARROWS[cell] == (dr, dc):
                break
        else:
            raise ValueError(f"Thermometer at {r},{c} is too short")

        thermometer_idx = len(self.thermometers)
        self.cell_thermometer[r][c] = (thermometer_idx, 0)
        self.thermometers.append([(r, c)])
        self.thermometer_directions.append((dr, dc))

        while True:
            r, c = new_r, new_c
            self.cell_thermometer[r][c] = (
                thermometer_idx,
                len(self.thermometers[-1]),
            )
            self.thermometers[-1].append((r, c))
            cell = self.initial_grid[r][c]
            if cell in ARROWS:
                break

            directions = BENDS[cell].copy()
            directions.remove((-dr, -dc))
            dr, dc = directions[0]
            if (dr, dc) != self.thermometer_directions[-1]:
                self.thermometer_directions[-1] = None

            new_r, new_c = r + dr, c + dc

    def initialize_state(self):
        self.state = ThermometersPuzzleState(
            grid=[[None] * self.grid_utils.cols for _ in range(self.grid_utils.rows)],
            found_by_col=([0] * self.grid_utils.cols, [0] * self.grid_utils.cols),
            found_by_row=([0] * self.grid_utils.rows, [0] * self.grid_utils.rows),
            found_by_thermometer=(
                [0] * len(self.thermometers),
                [0] * len(self.thermometers),
            ),
        )

    def get_thermometer_min_fill_level(self, thermometer_idx):
        values = [self.state.grid[r][c] for r, c in self.thermometers[thermometer_idx]]
        if all(x != 1 for x in values):
            return 0
        return max(i for i, x in enumerate(values) if x == 1)

    def get_thermometer_max_fill_level(self, thermometer_idx):
        r, c = self.thermometers[thermometer_idx][0]
        direction = self.thermometer_directions[thermometer_idx]

        res = len(self.thermometers[thermometer_idx]) - 1
        if direction is not None:
            # the thermometer is straight, it cannot contain more cells than the
            # ones available in the row/column
            dr, dc = direction
            if dc == 0:
                res = self.col_counts[c] - self.state.found_by_col[1][c] - 1
            else:
                res = self.row_counts[r] - self.state.found_by_row[1][r] - 1
            res += self.state.found_by_thermometer[1][thermometer_idx]

        values = [self.state.grid[r][c] for r, c in self.thermometers[thermometer_idx]]
        if all(x != 0 for x in values):
            return min(res, len(values) - 1)

        return min(res, min(i for i, x in enumerate(values) if x == 0) - 1)

    def get_valid_values(self, location):
        return [x for x in (0, 1) if self.can_set(location, x)]

    def can_set(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None

        thermometer_idx, cell_idx = self.cell_thermometer[r][c]
        if (
            value == 0
            and self.get_thermometer_min_fill_level(thermometer_idx) > cell_idx
        ):
            return False

        if (
            value == 1
            and self.get_thermometer_max_fill_level(thermometer_idx) < cell_idx
        ):
            return False

        def check_bounds(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return 0 <= missing <= available

        self.set_value(location, value)

        res = True
        if res:
            res = check_bounds(
                self.state.found_by_row[1][r],
                self.state.found_by_row[0][r],
                self.row_counts[r],
                self.grid_utils.cols,
            )

        if res:
            res = check_bounds(
                self.state.found_by_col[1][c],
                self.state.found_by_col[0][c],
                self.col_counts[c],
                self.grid_utils.rows,
            )

        self.unset_value(location)

        return res

    def _update_value(self, location, value, delta):
        r, c = location
        thermometer_idx, _ = self.cell_thermometer[r][c]
        self.state.found_by_col[value][c] += delta
        self.state.found_by_row[value][r] += delta
        self.state.found_by_thermometer[value][thermometer_idx] += delta

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
