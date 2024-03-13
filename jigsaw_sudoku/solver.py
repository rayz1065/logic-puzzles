from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.sudoku_like import SudokuLike


class JigsawSudokuSolver(SimpleBranchingSolver, SudokuLike):
    def get_branching_score(self, location):
        return -len(self.puzzle.get_valid_values(location))

    def get_constrained_locations(self):
        res = []
        res.extend(  # rows
            [(r, c) for c in range(self.puzzle.grid_utils.cols)]
            for r in range(self.puzzle.grid_utils.rows)
        )
        res.extend(  # cols
            [(r, c) for r in range(self.puzzle.grid_utils.rows)]
            for c in range(self.puzzle.grid_utils.cols)
        )
        res.extend(self.puzzle.regions.values())  # regions

        return res

    def _branching_solve(self):
        res = self._solve_hidden_singles()
        if res is not None:
            return res

        return super()._branching_solve()

    def _compute_dirty(self, location):
        dirty = set()

        r, c = location
        region = self.puzzle.regions_grid[r][c]

        # rows
        dirty.update((new_r, c) for new_r in range(self.puzzle.grid_utils.rows))

        # cols
        dirty.update((r, new_c) for new_c in range(self.puzzle.grid_utils.cols))

        # regions
        dirty.update((new_r, new_c) for new_r, new_c in self.puzzle.regions[region])

        return set(x for x in dirty if not self.is_location_set(x))
