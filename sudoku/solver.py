from itertools import product
from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.sudoku_like import SudokuLike

class SudokuSolver(SimpleBranchingSolver, SudokuLike):
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
        res.extend(  # squares
            list(self.puzzle.iter_square(square_r, square_c))
            for square_r in range(self.puzzle.rows_square_count)
            for square_c in range(self.puzzle.cols_square_count)
        )

        return res

    def _branching_solve(self):
        res = self._solve_hidden_singles()
        if res is not None:
            return res

        return super()._branching_solve()

    def _compute_dirty(self, location):
        dirty = set()
        r, c = location
        square_r, square_c = self.puzzle.get_square_coords(r, c)
        for new_r in range(self.puzzle.grid_utils.rows):
            if not self.is_location_set((new_r, c)):
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_utils.rows):
            if not self.is_location_set((r, new_c)):
                dirty.add((r, new_c))

        for new_r, new_c in self.puzzle.iter_square(square_r, square_c):
            if not self.is_location_set((new_r, new_c)):
                dirty.add((new_r, new_c))

        return dirty
