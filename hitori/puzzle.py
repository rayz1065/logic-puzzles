from queue import PriorityQueue
from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils


class HitoriPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    white_numbers_by_row: list[list[int]]
    white_numbers_by_col: list[list[int]]
    numbers_by_row: list[list[int]]
    numbers_by_col: list[list[int]]

    def __init__(
        self,
        grid,
        white_numbers_by_row,
        white_numbers_by_col,
        numbers_by_row,
        numbers_by_col,
    ):
        self.grid = grid
        self.white_numbers_by_row = white_numbers_by_row
        self.white_numbers_by_col = white_numbers_by_col
        self.numbers_by_row = numbers_by_row
        self.numbers_by_col = numbers_by_col


class HitoriPuzzle(Puzzle):
    initial_grid: list[list[int]]
    grid_utils: GridUtils
    state: HitoriPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [line.strip() for line in string.split("\n")]
        lines = [line.split() for line in lines if line and not line.startswith("#")]
        initial_grid = [[int(cell) for cell in line] for line in lines]

        return cls(initial_grid)

    def __init__(self, initial_grid, state=None):
        self.initial_grid = initial_grid
        self.grid_utils = GridUtils(len(self.initial_grid), len(self.initial_grid[0]))
        self.state = state

        if state is None:
            self.initialize_state()

    def __str__(self):
        def stringify_cell(r, c):
            if self.state.grid[r][c] == 0:
                return "X"
            if self.state.grid[r][c] == 1:
                return "."
            return str(self.initial_grid[r][c])

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    def initialize_state(self):
        max_number = max(cell for row in self.initial_grid for cell in row)

        numbers_by_row = [[0] * (max_number + 1) for _ in range(self.grid_utils.rows)]
        numbers_by_col = [[0] * (max_number + 1) for _ in range(self.grid_utils.cols)]

        for r, c in self.grid_utils.iter_grid():
            numbers_by_row[r][self.initial_grid[r][c]] += 1
            numbers_by_col[c][self.initial_grid[r][c]] += 1

        self.state = HitoriPuzzleState(
            grid=[
                [None for _ in range(self.grid_utils.cols)]
                for _ in range(self.grid_utils.rows)
            ],
            white_numbers_by_row=[
                [0] * (max_number + 1) for _ in range(self.grid_utils.rows)
            ],
            white_numbers_by_col=[
                [0] * (max_number + 1) for _ in range(self.grid_utils.cols)
            ],
            numbers_by_row=numbers_by_row,
            numbers_by_col=numbers_by_col,
        )

    def get_valid_values(self, location):
        return [x for x in (0, 1) if self.can_set(location, x)]

    def can_set(self, location, value):
        r, c = location
        number = self.initial_grid[r][c]

        if value == 1:
            return (
                self.state.white_numbers_by_row[r][number] == 0
                and self.state.white_numbers_by_col[c][number] == 0
            )

        # check that there are no two adjacent black cells
        neigh = list(self.grid_utils.orthogonal_iter(r, c, 1))
        for new_r, new_c in neigh:
            if self.state.grid[new_r][new_c] == 0:
                return False

        # if the cell above and below have the same value, this one must be white
        for direction in ((-1, 0), (0, -1)):
            cells = list(self.grid_utils.directions_iter(r, c, [direction], 1))
            values = set(self.initial_grid[new_r][new_c] for new_r, new_c in cells)
            if len(cells) == 2 and len(values) == 1:
                return False

        # check that there is a path between all surrounding cells
        self.set_value(location, value)

        res = self.find_paths(*neigh[0], neigh[1:])

        self.unset_value(location)

        return res

    def find_paths(self, r, c, targets):
        visited = set([(r, c)])
        queue = PriorityQueue()
        queue.put((0, (r, c)))

        def manhattan_dist(r1, c1, r2, c2):
            return abs(r1 - r2) + abs(c1 - c2)

        def a_star_score(r, c):
            return min(manhattan_dist(r, c, to_r, to_c) for to_r, to_c in targets)

        while not queue.empty():
            r, c = queue.get_nowait()[1]
            for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
                if self.state.grid[new_r][new_c] == 0 or (new_r, new_c) in visited:
                    continue

                if (new_r, new_c) in targets:
                    targets.remove((new_r, new_c))
                    if not targets:
                        return True

                score = a_star_score(new_r, new_c)
                queue.put_nowait((score, (new_r, new_c)))
                visited.add((new_r, new_c))

        return False

    def _update_value(self, location, value, delta):
        r, c = location
        number = self.initial_grid[r][c]
        if value == 0:
            self.state.numbers_by_row[r][number] -= delta
            self.state.numbers_by_col[c][number] -= delta
        else:
            self.state.white_numbers_by_row[r][number] += delta
            self.state.white_numbers_by_col[c][number] += delta

    def set_value(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        self.state.grid[r][c] = value
        self._update_value(location, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        assert self.state.grid[r][c] is not None
        self.state.grid[r][c] = None
        self._update_value(location, value, -1)
