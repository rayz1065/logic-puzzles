from logic_puzzles.solver import Solver


class KropkiSolver(Solver):
    def _solve_dirty(self, next_r, next_c, dirty):
        self.check_timeout()

        if len(dirty) == 0:
            return self._solve(next_r, next_c)

        r, c = dirty.pop()
        if self.state.grid[r][c] is not None:
            return self._solve_dirty(next_r, next_c, dirty)

        valid_values = [
            value
            for value in range(1, self.puzzle.grid_size + 1)
            if self.puzzle.is_valid(r, c, value)
        ]

        if len(valid_values) == 0:
            return 0

        if len(valid_values) > 1:
            return self._solve_dirty(next_r, next_c, dirty)

        value = valid_values[0]
        dirty.update(self.puzzle.set_value(r, c, value))
        res = self._solve_dirty(next_r, next_c, dirty)
        self.puzzle.unset_value(r, c)
        return res

    def _solve(self, r=0, c=0):
        self.check_timeout()

        if c == self.puzzle.grid_size:
            r, c = r + 1, 0
            if r == self.puzzle.grid_size:
                self.store_solution()
                return 1

        if self.state.grid[r][c] is not None:
            return self._solve(r, c + 1)

        res = 0
        for value in range(1, self.puzzle.grid_size + 1):
            if not self.puzzle.is_valid(r, c, value):
                continue

            dirty = self.puzzle.set_value(r, c, value)
            res += self._solve_dirty(r, c + 1, dirty)
            self.puzzle.unset_value(r, c)

        return res
