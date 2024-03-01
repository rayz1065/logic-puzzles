from logic_puzzles.solver import Solver
from .puzzle import ORTHOGONAL_DIRECTIONS, DIAGONAL_DIRECTIONS


class BattleshipsSolver(Solver):
    def _compute_dirty(self, r, c, value):
        dirty = set()
        for new_r, new_c in self.puzzle.orthogonal_iter(r, c):
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        if value == 0:
            return dirty

        # diagonal cells around a boat are also dirty as they must be set to 0
        for new_r, new_c in self.puzzle.diagonal_iter(r, c, 1):
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        return dirty

    def _solve_dirty(self, next_r, next_c, dirty):
        while len(dirty) > 0:
            r, c = dirty.pop()
            if self.state.grid[r][c] is None:
                valid_values = [x for x in (0, 1) if self.puzzle.can_set(r, c, x)]
                if len(valid_values) <= 1:
                    break
        else:
            # failed to find an empty dirty cell that doesn't require branching
            return self._branching_solve(next_r, next_c)

        if len(valid_values) == 0:
            return 0

        value = valid_values[0]
        dirty.update(self._compute_dirty(r, c, value))
        self.puzzle.set_value(r, c, value)
        res = self._solve_dirty(next_r, next_c, dirty)
        self.puzzle.unset_value(r, c)
        return res

    def _branching_solve(self, r=0, c=0):
        if c == self.puzzle.cols:
            c = 0
            r += 1
            if r == self.puzzle.rows:
                self.store_solution()
                return 1

        if self.state.grid[r][c] is not None:
            return self._branching_solve(r, c + 1)

        res = 0
        for value in (0, 1):
            if not self.puzzle.can_set(r, c, value):
                continue

            dirty = self._compute_dirty(r, c, value)
            self.puzzle.set_value(r, c, value)
            res += self._solve_dirty(r, c + 1, dirty)
            self.puzzle.unset_value(r, c)

        return res

    def _solve(self):
        dirty = set(
            (r, c)
            for r in range(self.puzzle.rows)
            for c in range(self.puzzle.cols)
            if self.state.grid[r][c] is None
        )

        return self._solve_dirty(0, 0, dirty)
