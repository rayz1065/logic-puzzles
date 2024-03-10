from math import comb
from logic_puzzles.solver import SimpleBranchingSolver


class TentsSolver(SimpleBranchingSolver):
    def _compute_dirty(self, location):
        dirty = set()

        r, c = location
        value = self.state.grid[r][c]
        state_value = 1 if value != (None, None) else 0

        # the cells next to a tent must be empty
        if state_value == 1:
            for new_r, new_c in self.puzzle.grid_utils.diagonal_iter(r, c, 1):
                if self.state.grid[new_r][new_c] is None:
                    dirty.add((new_r, new_c))

        # check all the cells next to trees next to this cell
        for tree_r, tree_c in self.puzzle.grid_utils.orthogonal_iter(r, c, 1):
            if self.puzzle.tree_ids[tree_r][tree_c] is None:
                continue

            for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(
                tree_r, tree_c, 1
            ):
                if self.state.grid[new_r][new_c] is None:
                    dirty.add((new_r, new_c))

        for new_r in range(self.puzzle.grid_utils.rows):
            if self.state.grid[new_r][c] is None:
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_utils.cols):
            if self.state.grid[r][new_c] is None:
                dirty.add((r, new_c))

        return dirty

    def get_branching_score(self, location):
        r, c = location

        def compute_score(found, empty, target, total):
            missing = target - found
            available = total - found - empty
            return -comb(available, missing)

        return max(
            compute_score(
                self.state.found_by_row[1][r],
                self.state.found_by_row[0][r],
                self.puzzle.row_counts[r],
                self.puzzle.grid_utils.cols,
            ),
            compute_score(
                self.state.found_by_col[1][c],
                self.state.found_by_col[0][c],
                self.puzzle.col_counts[c],
                self.puzzle.grid_utils.rows,
            ),
        )
