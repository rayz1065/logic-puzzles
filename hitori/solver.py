from logic_puzzles.solver import SimpleBranchingSolver


class HitoriSolver(SimpleBranchingSolver):
    def is_location_set(self, location):
        r, c = location
        return self.puzzle.state.grid[r][c] is not None

    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()

    def get_branching_score(self, location):
        r, c = location
        number = self.puzzle.initial_grid[r][c]

        if (
            self.state.numbers_by_row[r][number] == 1
            and self.state.numbers_by_col[c][number] == 1
        ):
            # If the solution is unique this cell is guaranteed to be white
            # we can therefore ignore it for now and only branch on it if
            # the solution is not unique
            return -self.puzzle.grid_utils.rows

        return -min(
            self.state.numbers_by_row[r][number],
            self.state.numbers_by_col[c][number],
        )

    def _compute_dirty(self, location):
        dirty = set()
        r, c = location

        for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(r, c):
            if not self.is_location_set((new_r, new_c)):
                dirty.add((new_r, new_c))

        return dirty
