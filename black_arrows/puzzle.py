from itertools import product
from logic_puzzles.puzzle import Puzzle, PuzzleState

DIRECTIONS = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
    "NE": (-1, 1),
    "SE": (1, 1),
    "SW": (1, -1),
    "NW": (-1, -1),
}
PRETTY_DIRECTIONS = {
    "↑": (-1, 0),
    "↓": (1, 0),
    "→": (0, 1),
    "←": (0, -1),
    "↗": (-1, 1),
    "↘": (1, 1),
    "↙": (1, -1),
    "↖": (-1, -1),
}


class BlackArrowsPuzzleState(PuzzleState):
    marked: list[list[int | None]]
    solved: list[list[int]]
    pointed_from_solved: list[list[int]]
    pointing_to_undecided: list[list[int]]

    def __init__(self, marked, solved, pointed_from_solved, pointing_to_undecided):
        self.marked = marked
        self.solved = solved
        self.pointed_from_solved = pointed_from_solved
        self.pointing_to_undecided = pointing_to_undecided


class BlackArrowsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Freccia+nera"""

    grid: list[list[tuple[int, int]]]
    pointed_by: list[list[list[tuple[int, int]]]]
    state: BlackArrowsPuzzleState

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        grid = [[DIRECTIONS[x] for x in line] for line in lines]

        return cls(grid)

    def __init__(self, grid, state=None):
        self.grid = grid
        self.pointed_by = [[[] for _ in row] for row in grid]

        for r, c in product(range(self.grid_size), repeat=2):
            dr, dc = self.grid[r][c]
            for new_r, new_c in self.ray_iter(r, c, dr, dc):
                self.pointed_by[new_r][new_c].append((r, c))

        if state is None:
            pointing_to_undecided = [[0 for _ in row] for row in grid]

            # this can also be more simply computed as the distance to the edge of the grid
            for r, c in product(range(self.grid_size), repeat=2):
                dr, dc = self.grid[r][c]
                pointing_to_undecided[r][c] = sum(
                    1 for new_r, new_c in self.ray_iter(r, c, dr, dc)
                )

            state = BlackArrowsPuzzleState(
                marked=[[None for _ in row] for row in grid],
                solved=[[0 for _ in row] for row in grid],
                pointed_from_solved=[[0 for _ in row] for row in grid],
                pointing_to_undecided=pointing_to_undecided,
            )

        self.state = state

    def __str__(self):
        ARROW = {value: key for key, value in PRETTY_DIRECTIONS.items()}

        return "\n".join(
            " ".join(
                ARROW[direction] if not self.state.marked[r][c] else "X"
                for c, direction in enumerate(row)
            )
            for r, row in enumerate(self.grid)
        )

    @property
    def grid_size(self):
        return len(self.grid)

    def in_range(self, r, c):
        return 0 <= r < self.grid_size and 0 <= c < self.grid_size

    def ray_iter(self, r, c, dr, dc):
        for distance in range(1, self.grid_size):
            new_r, new_c = r + dr * distance, c + dc * distance
            if not self.in_range(new_r, new_c):
                break

            yield new_r, new_c

    def star_iter(self, r, c):
        for dr, dc in DIRECTIONS.values():
            for new_r, new_c in self.ray_iter(r, c, dr, dc):
                yield dr, dc, new_r, new_c

    def can_mark(self, r, c, value):
        if value == 1:
            return self.state.pointed_from_solved[r][c] == 0

        for new_r, new_c in self.pointed_by[r][c]:
            if (
                self.state.pointing_to_undecided[new_r][new_c] <= 1
                and not self.state.solved[new_r][new_c]
            ):
                return False

        return True

    def _update_pointed_from_solved(self, r, c, delta):
        # arrows that are already pointed from solved can only be left unmarked
        dr, dc = self.grid[r][c]
        for new_r, new_c in self.ray_iter(r, c, dr, dc):
            self.state.pointed_from_solved[new_r][new_c] += delta

    def _update_conflicts(self, r, c, value, delta):
        # value = 1 -> arrow at r, c is marked, arrows that point to it are now solved
        # either way we reduce the number of undecided arrows they point to
        for new_r, new_c in self.pointed_by[r][c]:
            if value == 1:
                self.state.solved[new_r][new_c] += delta
                self._update_pointed_from_solved(new_r, new_c, delta)
            self.state.pointing_to_undecided[new_r][new_c] -= delta

    def set_mark(self, r, c, value):
        self.state.marked[r][c] = value
        self._update_conflicts(r, c, value, 1)

    def unset_mark(self, r, c):
        value = self.state.marked[r][c]
        self.state.marked[r][c] = None
        self._update_conflicts(r, c, value, -1)
