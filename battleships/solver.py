from math import comb
from logic_puzzles.solver import SimpleBranchingSolver


class BattleshipsSolver(SimpleBranchingSolver):
    def _compute_dirty(self, location):
        r, c = location
        dirty = set()
        for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(r, c):
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        # diagonal cells around a boat are also dirty as they must be set to 0
        # placing a 0 next to a + boat also requires the diagonal cells to be 1
        for new_r, new_c in self.puzzle.grid_utils.diagonal_iter(r, c, 1):
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        return dirty

    def get_branching_score(self, location):
        r, c = location

        def compute_score(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return -comb(available, missing)

        return max(
            compute_score(
                self.state.row_cells_by_value[1][r],
                self.state.row_cells_by_value[0][r],
                self.puzzle.row_counts[r],
                self.puzzle.grid_utils.cols,
            ),
            compute_score(
                self.state.col_cells_by_value[1][c],
                self.state.col_cells_by_value[0][c],
                self.puzzle.col_counts[c],
                self.puzzle.grid_utils.rows,
            ),
        )
