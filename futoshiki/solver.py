from logic_puzzles.solver import SimpleBranchingSolver
from logic_puzzles.sudoku_like import SudokuLike


class FutoshikiSolver(SimpleBranchingSolver, SudokuLike):
    def get_constrained_locations(self):
        res = []
        res.extend(  # rows
            [("grid", (r, c)) for c in range(self.puzzle.grid_utils.cols)]
            for r in range(self.puzzle.grid_utils.rows)
        )
        res.extend(  # cols
            [("grid", (r, c)) for r in range(self.puzzle.grid_utils.rows)]
            for c in range(self.puzzle.grid_utils.cols)
        )
        return res

    def _branching_solve(self):
        res = self._solve_hidden_singles()
        if res is not None:
            return res

        return super()._branching_solve()

    def get_branching_score(self, location):
        location_type, location_data = location
        if location_type == "hint":
            # never branch on hints
            return -self.puzzle.grid_utils.rows * 2

        # locations with more hints removed are better
        r, c = location_data
        return sum(
            self.puzzle.get_value(("hint", (r, c, value))) == 0
            for value in self.puzzle.iter_values()
        )

    def _compute_dirty(self, location):
        location_type, (r, c, *_) = location
        # hints are only used (directly) for adjacent cells
        distance = 1 if location_type == "hint" else self.puzzle.grid_utils.rows

        dirty = set(
            ("grid", (new_r, new_c))
            for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(r, c, distance)
        )
        dirty.update(
            ("hint", (new_r, new_c, value))
            for new_r, new_c in self.puzzle.grid_utils.orthogonal_iter(r, c, distance)
            for value in self.puzzle.iter_values()
        )

        return set(x for x in dirty if not self.is_location_set(x))
