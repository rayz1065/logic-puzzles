from itertools import product
from logic_puzzles.puzzle import Puzzle, PuzzleState

DIRECTIONS = {
    "v": [(-1, 0)],
    "^": [(1, 0)],
    ">": [(0, -1)],
    "<": [(0, 1)],
    "O": [],
    "+": [(-1, 0), (0, -1), (0, 1), (1, 0)],
}
ORTHOGONAL_DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
DIAGONAL_DIRECTIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ALL_DIRECTIONS = ORTHOGONAL_DIRECTIONS + DIAGONAL_DIRECTIONS


class BattleshipsPuzzleState(PuzzleState):
    grid: list[list[int | None]]
    row_cells_by_value: list[int]
    col_cells_by_value: list[int]
    found_boats: list[int]

    def __init__(self, grid, row_cells_by_value, col_cells_by_value, found_boats):
        self.grid = grid
        self.row_cells_by_value = row_cells_by_value
        self.col_cells_by_value = col_cells_by_value
        self.found_boats = found_boats


class BattleshipsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Battaglia+navale"""

    boats: list[int]
    row_counts: list[int]
    col_counts: list[int]
    initial_grid: list[list[str]]
    state: BattleshipsPuzzleState

    @classmethod
    def from_string(self, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        raw_boats = [int(x) for x in lines[0]]
        boats = [0] * (max(raw_boats) + 1)
        for boat in raw_boats:
            boats[boat] += 1
        col_counts = [int(x) for x in lines[1]]
        row_counts = [int(x[0]) for x in lines[2:]]
        initial_grid = [[x for x in line[1:]] for line in lines[2:]]

        return BattleshipsPuzzle(boats, col_counts, row_counts, initial_grid)

    def __init__(self, boats, col_counts, row_counts, initial_grid, state=None):
        self.boats = boats
        self.col_counts = col_counts
        self.row_counts = row_counts
        self.initial_grid = initial_grid

        if state is None:
            self.state = BattleshipsPuzzleState(
                grid=[[None] * self.cols for _ in range(self.rows)],
                row_cells_by_value=([0] * self.rows, [0] * self.rows),
                col_cells_by_value=([0] * self.cols, [0] * self.cols),
                found_boats=[0] * len(self.boats),
            )
            self.initialize_state()
        else:
            self.state = state

    def __str__(self):
        return "\n".join(
            " ".join("O" if x else "." for x in row) for row in self.state.grid
        )

    def initialize_state(self):
        for r, c in product(range(self.rows), range(self.cols)):
            boat_type = self.initial_grid[r][c]
            if boat_type == ".":
                continue
            if boat_type == "X":
                if self.state.grid[r][c] is None:
                    self.set_value(r, c, 0)
                continue

            if self.state.grid[r][c] is None:
                self.set_value(r, c, 1)

            if len(DIRECTIONS[boat_type]) == 1:
                dr, dc = DIRECTIONS[boat_type][0]
                new_r, new_c = r + dr, c + dc

                if self.state.grid[new_r][new_c] is None:
                    self.set_value(new_r, new_c, 1)

            invalid_directions = set(ALL_DIRECTIONS) - set(DIRECTIONS[boat_type])
            for new_r, new_c in self.directions_iter(r, c, invalid_directions, 1):
                if self.state.grid[new_r][new_c] is None:
                    self.set_value(new_r, new_c, 0)

    @property
    def rows(self):
        return len(self.initial_grid)

    @property
    def cols(self):
        return len(self.initial_grid[0])

    def in_range(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def ray_iter(self, r, c, dr, dc, max_distance=None):
        max_distance = max_distance or self.rows + self.cols
        for distance in range(1, max_distance + 1):
            new_r, new_c = r + dr * distance, c + dc * distance
            if not self.in_range(new_r, new_c):
                break
            yield new_r, new_c

    def directions_iter(self, r, c, directions, max_distance=None):
        for dr, dc in directions:
            yield from self.ray_iter(r, c, dr, dc, max_distance)

    def orthogonal_iter(self, r, c, max_distance=None):
        yield from self.directions_iter(r, c, ORTHOGONAL_DIRECTIONS, max_distance)

    def diagonal_iter(self, r, c, max_distance=None):
        yield from self.directions_iter(r, c, DIAGONAL_DIRECTIONS, max_distance)

    def can_set(self, r, c, value):
        if value == 1:
            # no cell diagonal from this one can contain a boat
            for new_r, new_c in self.diagonal_iter(r, c, 1):
                if self.state.grid[new_r][new_c] == 1:
                    return False

            # check if the newly created boat is too large
            old_boat_sizes = [len(x) for x in self.get_boats_around(r, c)]
            new_boat_size = sum(old_boat_sizes) + 1
            if new_boat_size >= len(self.boats):
                return False

            # if we have already placed all the boats,
            # check that we have the right number of boats for each size
            new_found_boats = self.state.found_boats[:]
            new_found_boats[new_boat_size] += 1
            for length in old_boat_sizes:
                new_found_boats[length] -= 1

            current_boat_count = sum(x * i for i, x in enumerate(new_found_boats))
            target_boat_count = sum(x * i for i, x in enumerate(self.boats))

            if (
                current_boat_count == target_boat_count
                and new_found_boats != self.boats
            ):
                return False

            # sizes of boats cannot shrink, we can check that for every size there
            # are not too many boats of size [size, size + 1, ...]
            # this is guaranteed by induction for new_boat_size + 1
            target_acc = sum(
                self.boats[size] for size in range(new_boat_size, len(self.boats))
            )
            current_acc = sum(
                new_found_boats[size]
                for size in range(new_boat_size, len(new_found_boats))
            )

            if current_acc > target_acc:
                return False

        new_row_cells_by_value = [x[r] for x in self.state.row_cells_by_value]
        new_col_cells_by_value = [x[c] for x in self.state.col_cells_by_value]
        new_row_cells_by_value[value] += 1
        new_col_cells_by_value[value] += 1

        bounds = [
            (
                new_col_cells_by_value[1],
                self.rows - new_col_cells_by_value[0],
                self.col_counts[c],
            ),
            (
                new_row_cells_by_value[1],
                self.cols - new_row_cells_by_value[0],
                self.row_counts[r],
            ),
        ]

        for lower, upper, target in bounds:
            if not (lower <= target <= upper):
                return False

        return True

    def get_boats_around(self, r, c):
        boats = []
        for new_r, new_c in self.orthogonal_iter(r, c, 1):
            if self.state.grid[new_r][new_c] != 1:
                continue
            boats.append(self.get_boat(new_r, new_c))

        return boats

    def get_boat(self, r, c):
        if self.state.grid[r][c] == 0:
            return set()

        res = set([(r, c)])
        for dr, dc in ORTHOGONAL_DIRECTIONS:
            for new_r, new_c in self.ray_iter(r, c, dr, dc):
                if self.state.grid[new_r][new_c] != 1:
                    break
                res.add((new_r, new_c))

        return res

    def _update_value(self, r, c, value, delta):
        self.state.row_cells_by_value[value][r] += delta
        self.state.col_cells_by_value[value][c] += delta

    def _merge_boats(self, r, c, delta):
        lengths = [len(x) for x in self.get_boats_around(r, c)]
        for length in lengths:
            self.state.found_boats[length] -= delta
        self.state.found_boats[sum(lengths) + 1] += delta

    def set_value(self, r, c, value):
        if value == 1:
            self._merge_boats(r, c, 1)

        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

    def unset_value(self, r, c):
        value = self.state.grid[r][c]
        self.state.grid[r][c] = None
        self._update_value(r, c, value, -1)

        if value == 1:
            self._merge_boats(r, c, -1)
