from logic_puzzles.puzzle import Puzzle, PuzzleState

DIRECTIONS = {
    "|": [(1, 0), (-1, 0)],
    "-": [(0, 1), (0, -1)],
    "J": [(-1, 0), (0, -1)],
    "L": [(-1, 0), (0, 1)],
    "7": [(1, 0), (0, -1)],
    "F": [(1, 0), (0, 1)],
}
MAX_VALUE = 3


class MagicalMazePuzzleState(PuzzleState):
    values: list[list[int]]
    conflict_values: list[list[list[int]]]
    rows_found: list[list[int]]
    cols_found: list[list[int]]

    def __init__(self, values, conflict_values, rows_found, cols_found):
        self.values = values
        self.conflict_values = conflict_values
        self.rows_found = rows_found
        self.cols_found = cols_found


class MagicalMazePuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Labirinto+magico"""

    grid: list[str]
    initial_values: list[list[int]]
    locations: list[tuple[int, int]]
    distance: list[list[int]]
    state: MagicalMazePuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [line.strip() for line in string.split("\n") if line.strip() != ""]
        grid_size = len(lines) // 2
        grid = [x.replace(" ", "") for x in lines[:grid_size]]
        values = [
            [int(x) if x not in ["0", "."] else None for x in row.split()]
            for row in lines[grid_size:]
        ]

        return cls(grid, values)

    @property
    def grid_size(self):
        return len(self.grid)

    def __init__(self, grid, initial_values, state=None):
        self.grid = grid
        self.initial_values = initial_values
        self.locations = []
        self.distance = [[None] * self.grid_size for _ in range(self.grid_size)]

        # find the entrance of the maze
        for (r, c), cell in self.iter_grid():
            if self.is_entrance(r, c):
                self.locations.append((r, c))
                self.distance[r][c] = 0
                break

        if len(self.locations) == 0:
            raise ValueError("Entrance not found!")

        # traverse the maze
        for dist in range(1, self.grid_size**2):
            r, c = self.locations[-1]
            for dr, dc in DIRECTIONS[self.grid[r][c]]:
                new_r, new_c = r + dr, c + dc
                if self.in_range(new_r, new_c) and self.distance[new_r][new_c] is None:
                    self.locations.append((new_r, new_c))
                    self.distance[new_r][new_c] = dist
                    break

            if len(self.locations) != dist + 1:
                raise ValueError(f"Nowhere to go from {r}, {c}!")

        if state is None:
            values = [[None] * self.grid_size for _ in range(self.grid_size)]
            conflict_values = [
                [[0] * (MAX_VALUE + 1) for _ in range(self.grid_size)]
                for _ in range(self.grid_size)
            ]

            rows_found = [[0] * (MAX_VALUE + 1) for _ in range(self.grid_size)]
            cols_found = [[0] * (MAX_VALUE + 1) for _ in range(self.grid_size)]

            self.state = MagicalMazePuzzleState(
                values, conflict_values, rows_found, cols_found
            )

            for (r, c), _ in self.iter_grid():
                if self.initial_values[r][c] is not None:
                    self.set_value(r, c, self.initial_values[r][c])
        else:
            self.state = state

    def __str__(self):
        return (
            "\n".join(self.grid)
            + "\n"
            + "\n".join(
                " ".join(str(x) if x is not None else "." for x in row)
                for row in self.state.values
            )
        )

    def iter_grid(self):
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(self.grid):
                yield (r, c), cell

    def in_range(self, r, c):
        return 0 <= r < self.grid_size and 0 <= c < self.grid_size

    def is_entrance(self, r, c):
        for dr, dc in DIRECTIONS[self.grid[r][c]]:
            if not self.in_range(r + dr, c + dc):
                return True

        return False

    def get_available_values(self, r, c):
        if self.state.values[r][c] is not None:
            return []

        res = [
            i
            for i in range(1, MAX_VALUE + 1)
            if self.state.conflict_values[r][c][i] == 0
        ]
        if not self.must_fill_cell(r, c):
            res.append(0)

        return res

    def must_fill_cell(self, r, c):
        row_available = self.grid_size - sum(self.state.rows_found[r])
        row_missing = MAX_VALUE - sum(self.state.rows_found[r][1:])
        col_available = self.grid_size - sum(self.state.cols_found[c])
        col_missing = MAX_VALUE - sum(self.state.cols_found[c][1:])

        return row_available == row_missing or col_available == col_missing

    def _update_conflicts(self, r, c, value, delta=1):
        self.state.rows_found[r][value] += delta
        self.state.cols_found[c][value] += delta

        dirty = set()

        # the cells in the same row/column cannot share the same number
        for dr, dc in DIRECTIONS["|"] + DIRECTIONS["-"]:
            for dist in range(1, self.grid_size):
                new_r, new_c = r + dr * dist, c + dc * dist
                if not self.in_range(new_r, new_c):
                    break
                self.state.conflict_values[new_r][new_c][value] += delta
                if (
                    self.state.conflict_values[new_r][new_c][value] == delta == 1
                    and self.state.values[new_r][new_c] is None
                ):
                    dirty.add((new_r, new_c))

        if value == 0:
            return dirty

        # the next few cells are restricted to only have consecutive numbers
        # we do not want to perform this heuristic for 0
        dist = self.distance[r][c]
        for spacing in range(1, MAX_VALUE):
            new_dist = dist + spacing
            max_new_value = value + spacing
            if new_dist >= len(self.locations):
                break

            new_r, new_c = self.locations[new_dist]

            if delta == 1:
                dirty.add((new_r, new_c))

            for new_value in range(max_new_value + 1, value + MAX_VALUE + 1):
                actual_new_value = (new_value - 1) % MAX_VALUE + 1
                self.state.conflict_values[new_r][new_c][actual_new_value] += delta

        return dirty

    def set_value(self, r, c, value):
        assert self.state.values[r][c] is None
        self.state.values[r][c] = value
        return self._update_conflicts(r, c, value, 1)

    def unset_value(self, r, c):
        value = self.state.values[r][c]
        assert value is not None
        self.state.values[r][c] = None
        self._update_conflicts(r, c, value, -1)
