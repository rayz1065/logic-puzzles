from logic_puzzles.solver import SimpleBranchingSolver


class SkyscrapersSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        return 1

    def _compute_dirty(self, location):
        dirty = set()

        r, c = location
        value = self.state.grid[r][c]

        # check all the cells next to this cell
        for new_r in range(self.puzzle.grid_size):
            if self.state.grid[new_r][c] is None:
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_size):
            if self.state.grid[r][new_c] is None:
                dirty.add((r, new_c))

        return dirty

    def is_location_set(self, location):
        r, c = location
        return self.state.grid[r][c] is not None

    def iter_locations(self):
        yield from self.puzzle.grid_utils.iter_grid()
