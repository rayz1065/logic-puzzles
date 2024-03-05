from itertools import product
from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.grid_utils import ORTHOGONAL_DIRECTIONS


class KropkiSolver(SimpleBranchingSolver):
    def is_location_set(self, location):
        r, c = location
        return self.state.grid[r][c] is not None

    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()

    def get_branching_score(self, location):
        return -len(self.puzzle.get_valid_values(location))

    def _compute_dirty(self, location):
        r, c = location

        dirty = set()

        for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(r, c):
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        if not self.puzzle.sudoku_mode:
            return dirty

        square_r, square_c = (
            r - r % self.puzzle.sudoku_square_size,
            c - c % self.puzzle.sudoku_square_size,
        )
        for dr, dc in product(range(self.puzzle.sudoku_square_size), repeat=2):
            new_r, new_c = square_r + dr, square_c + dc
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        return dirty
