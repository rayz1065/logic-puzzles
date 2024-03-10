from logic_puzzles.puzzle import Puzzle, PuzzleState
from logic_puzzles.grid_utils import GridUtils, ORTHOGONAL_DIRECTIONS, ARROWS
from functools import cache


class TentsPuzzleState(PuzzleState):
    grid: list[list[tuple[int, int]]]
    found_by_row: tuple[list[int], list[int]]
    found_by_col: tuple[list[int], list[int]]
    found_by_tree: tuple[list[int], list[int]]

    def __init__(self, grid, found_by_row, found_by_col, found_by_tree):
        self.grid = grid
        self.found_by_row = found_by_row
        self.found_by_col = found_by_col
        self.found_by_tree = found_by_tree


class TentsPuzzle(Puzzle):
    """http://www.puzzlefountain.com/giochi.php?tipopuzzle=Camping"""

    initial_grid: list[list[str]]
    row_counts: list[int]
    col_counts: list[int]
    grid_utils: GridUtils
    state: TentsPuzzleState
    tree_ids: list[list[int | None]]
    trees: list[tuple[int, int] | None]

    @classmethod
    def from_string(cls, string):
        lines = [x.strip() for x in string.split("\n")]
        lines = [x.split() for x in lines if x and not x.startswith("#")]
        col_counts = [int(x) for x in lines[0]]
        row_counts = [int(x[0]) for x in lines[1:]]
        initial_grid = [[x.lower() for x in line[1:]] for line in lines[1:]]

        return cls(initial_grid, row_counts, col_counts)

    def __init__(self, initial_grid, row_counts, col_counts, state=None):
        self.initial_grid = initial_grid
        self.row_counts = row_counts
        self.col_counts = col_counts
        self.grid_utils = GridUtils(len(initial_grid), len(initial_grid[0]))
        self.state = state

        self.tree_ids = [[None] * len(self.initial_grid[0]) for _ in self.initial_grid]
        self.trees = []
        for r, c in self.grid_utils.iter_grid():
            if self.initial_grid[r][c] == "x":
                self.tree_ids[r][c] = len(self.trees)
                self.trees.append((r, c))

        if state is None:
            self.initialize_state()

    def initialize_state(self):
        self.state = TentsPuzzleState(
            grid=[[None for _ in row] for row in self.initial_grid],
            found_by_row=([0] * self.grid_utils.rows, [0] * self.grid_utils.rows),
            found_by_col=([0] * self.grid_utils.cols, [0] * self.grid_utils.cols),
            found_by_tree=([0] * len(self.trees), [0] * len(self.trees)),
        )

        for r, c in self.trees:
            self.set_value((r, c), (None, None))

    def __str__(self):
        arrow_map = {v: k for k, v in ARROWS.items()}

        def stringify_cell(r, c):
            if self.initial_grid[r][c] == "x":
                return "x"
            if self.state.grid[r][c] is None:
                return "."
            if self.state.grid[r][c][0] is None:
                return "/"
            return arrow_map[self.state.grid[r][c]]

        return "\n".join(
            " ".join(stringify_cell(r, c) for c in range(self.grid_utils.cols))
            for r in range(self.grid_utils.rows)
        )

    @cache
    def spaces_around_tree(self, tree_id):
        r, c = self.trees[tree_id]
        return len(list(self.grid_utils.orthogonal_iter(r, c, 1)))

    def iter_locations(self):
        yield from self.grid_utils.iter_grid()

    def iter_values(self):
        yield from ORTHOGONAL_DIRECTIONS
        yield (None, None)

    def can_set(self, location, value):
        r, c = location
        assert self.state.grid[r][c] is None
        dr, dc = value
        if dr is not None:
            tree_r, tree_c = r + dr, c + dc
            if not self.grid_utils.in_range(tree_r, tree_c):
                return False
            if self.tree_ids[tree_r][tree_c] is None:
                return False

        # there cannot be tents adjacent to a tent
        if dr is not None:
            for new_r, new_c in self.grid_utils.all_directions_iter(r, c, 1):
                if (
                    self.state.grid[new_r][new_c] is not None
                    and self.state.grid[new_r][new_c][0] is not None
                ):
                    return False

        def check_bounds(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return 0 <= missing <= available

        self.set_value(location, value)

        # make sure there's enough slack to complete the row/column requirements
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

        if res:
            for tree_id, (tree_r, tree_c) in enumerate(self.trees):
                res = check_bounds(
                    self.state.found_by_tree[1][tree_id],
                    self.state.found_by_tree[0][tree_id],
                    1,
                    self.spaces_around_tree(tree_id),
                )
                if not res:
                    break

        self.unset_value(location)

        return res

    def _update_value(self, r, c, value, delta):
        # update found in rows/columns
        dr, dc = value
        state_value = 1 if dr is not None else 0
        self.state.found_by_col[state_value][c] += delta
        self.state.found_by_row[state_value][r] += delta

        if dr is not None:
            tree_r, tree_c = r + dr, c + dc
        else:
            tree_r, tree_c = None, None

        # for the same tree: increase the found tents by 1 (if this is a tent)
        # for other trees: increase the empty spaces by 1
        for new_r, new_c in self.grid_utils.orthogonal_iter(r, c, 1):
            if self.tree_ids[new_r][new_c] is not None:
                new_state_value = (
                    state_value if (new_r, new_c) == (tree_r, tree_c) else 0
                )
                self.state.found_by_tree[new_state_value][
                    self.tree_ids[new_r][new_c]
                ] += delta

    def get_value(self, location):
        r, c = location
        return self.state.grid[r][c]

    def set_value(self, location, value):
        r, c = location
        self.state.grid[r][c] = value
        self._update_value(r, c, value, 1)

    def unset_value(self, location):
        r, c = location
        value = self.state.grid[r][c]
        self.state.grid[r][c] = None
        self._update_value(r, c, value, -1)
