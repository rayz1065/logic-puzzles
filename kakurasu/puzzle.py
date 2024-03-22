from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils
from logic_puzzles.constraints import SumConstraint


class KakurasuPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    found_by_rows: dict[tuple[int, int], int]  # row, value -> sum
    found_by_cols: dict[tuple[int, int], int]  # col, value -> sum

    def __init__(self, grid, found_by_rows, found_by_cols):
        self.grid = grid
        self.found_by_rows = found_by_rows
        self.found_by_cols = found_by_cols


class KakurasuPuzzle(Puzzle):
    target_by_rows: list[int]
    target_by_cols: list[int]
    row_constraints: list[SumConstraint]
    col_constraints: list[SumConstraint]
    state: KakurasuPuzzleState
    grid_utils: GridUtils

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        target_by_rows = [int(x) for x in lines[0]]
        target_by_cols = [int(x) for x in lines[1]]

        return cls(target_by_rows, target_by_cols)

    def __init__(self, target_by_rows, target_by_cols, state=None):
        self.target_by_rows = target_by_rows
        self.target_by_cols = target_by_cols
        self.state = state

        self.grid_utils = GridUtils(len(target_by_rows), len(target_by_cols))

        max_row_sum = self.grid_utils.cols * (self.grid_utils.cols + 1) // 2
        max_col_sum = self.grid_utils.rows * (self.grid_utils.rows + 1) // 2

        self.row_constraints = [
            SumConstraint(target, max_row_sum) for target in target_by_rows
        ]
        self.col_constraints = [
            SumConstraint(target, max_col_sum) for target in target_by_cols
        ]

        if state is None:
            self.initialize_state()

    def initialize_state(self):
        self.state = KakurasuPuzzleState(
            grid=[[None for _ in self.target_by_cols] for _ in self.target_by_rows],
            found_by_rows={
                (r, value): 0
                for r in range(self.grid_utils.rows)
                for value in self.iter_values()
            },
            found_by_cols={
                (c, value): 0
                for c in range(self.grid_utils.cols)
                for value in self.iter_values()
            },
        )

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] is None:
                return "_"
            return "o" if self.state.grid[r][c] else "."

        max_number_len = max(len(str(x)) for x in self.target_by_cols)

        res = []
        for r in range(self.grid_utils.rows):
            res.append(
                " ".join(
                    stringify_cell(r, c).ljust(max_number_len)
                    for c in range(self.grid_utils.cols)
                )
                + f" {self.target_by_rows[r]}"
            )
        res.append(" ".join(str(x).ljust(max_number_len) for x in self.target_by_cols))

        return "\n".join(res)

    def iter_values(self):
        yield from (0, 1)

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def can_set(self, location, value):
        r, c = location

        self.set_value(location, value)

        res = self.row_constraints[r].check(
            self.state.found_by_rows[(r, 1)], self.state.found_by_rows[(r, 0)]
        ) and self.col_constraints[c].check(
            self.state.found_by_cols[(c, 1)], self.state.found_by_cols[(c, 0)]
        )

        self.unset_value(location)

        return res

    def _update_value(self, location, value, delta):
        r, c = location
        self.state.found_by_rows[(r, value)] += (c + 1) * delta
        self.state.found_by_cols[(c, value)] += (r + 1) * delta

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
