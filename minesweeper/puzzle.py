from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class MinesweeperPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_indicator: dict[tuple[int, int, int], int]  # (r, c, value) -> count

    def __init__(self, grid, found_by_indicator):
        self.grid = grid
        self.found_by_indicator = found_by_indicator


class MinesweeperPuzzle(Puzzle):
    initial_grid: list[list[int | None]]
    state: MinesweeperPuzzleState
    grid_utils: GridUtils
    mine_indicators: list[tuple[int, int]]
    field_cells: list[tuple[int, int]]
    adjacent_indicators: dict[
        tuple[int, int], list[tuple[int, int]]
    ]  # (field_r, field_c) -> [(indicator_r, indicator_c)]
    adjacent_cells: dict[
        tuple[int, int], list[tuple[int, int]]
    ]  # (indicator_r, indicator_c) -> [(field_r, field_c)]

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x for x in lines if x and not x.startswith("#")]
        initial_grid = [
            [int(x) if x.isdigit() else None for x in line.split()] for line in lines
        ]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.state = state
        self.grid_utils = GridUtils(len(self.initial_grid), len(self.initial_grid[0]))
        self.mine_indicators = [
            (r, c)
            for r, c in self.grid_utils.iter_grid()
            if self.initial_grid[r][c] is not None
        ]
        self.field_cells = [
            (r, c)
            for r, c in self.grid_utils.iter_grid()
            if self.initial_grid[r][c] is None
        ]

        self.adjacent_indicators = {
            (r, c): [
                (new_r, new_c)
                for new_r, new_c in self.grid_utils.all_directions_iter(r, c, 1)
                if self.initial_grid[new_r][new_c] is not None
            ]
            for r, c in self.field_cells
        }
        self.adjacent_cells = {
            (new_r, new_c): [
                (r, c)
                for r, c in self.grid_utils.all_directions_iter(new_r, new_c, 1)
                if self.initial_grid[r][c] is None
            ]
            for new_r, new_c in self.mine_indicators
        }

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.initial_grid[r][c] is not None:
                return str(self.initial_grid[r][c])
            if self.state.grid[r][c] is None:
                return "_"
            return "x" if self.state.grid[r][c] else "."

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(len(self.initial_grid[r])))
            for r in range(len(self.initial_grid))
        )

    def initialize_state(self):
        self.state = MinesweeperPuzzleState(
            grid=[[None for _ in row] for row in self.initial_grid],
            found_by_indicator={
                (r, c, value): 0
                for r, c in self.mine_indicators
                for value in self.iter_values()
            },
        )

    def iter_values(self):
        yield from (0, 1)

    def iter_locations(self):
        yield from self.field_cells

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def can_set(self, location, value):
        def _check_bounds(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return 0 <= missing <= available

        r, c = location

        self.set_value(location, value)

        res = all(
            _check_bounds(
                self.state.found_by_indicator[new_r, new_c, 1],
                self.state.found_by_indicator[new_r, new_c, 0],
                self.initial_grid[new_r][new_c],
                len(self.adjacent_cells[new_r, new_c]),
            )
            for new_r, new_c in self.adjacent_indicators[r, c]
        )

        self.unset_value(location)

        return res

    def _update_value(self, location, value, delta):
        r, c = location
        for new_r, new_c in self.adjacent_indicators[r, c]:
            self.state.found_by_indicator[new_r, new_c, value] += delta

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
