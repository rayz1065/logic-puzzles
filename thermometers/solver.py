from math import comb
from logic_puzzles.solver import SimpleBranchingSolver


class ThermometersSolver(SimpleBranchingSolver):
    def _compute_dirty(self, location):
        r, c = location

        dirty = set()
        thermometer_idx, _ = self.puzzle.cell_thermometer[r][c]
        for new_r, new_c in self.puzzle.thermometers[thermometer_idx]:
            if not self.is_location_set((new_r, new_c)):
                dirty.add((new_r, new_c))

        for new_r in range(self.puzzle.grid_utils.rows):
            if not self.is_location_set((new_r, c)):
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_utils.cols):
            if not self.is_location_set((r, new_c)):
                dirty.add((r, new_c))

        return dirty

    def is_location_set(self, location):
        r, c = location
        return self.state.grid[r][c] is not None

    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()

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
