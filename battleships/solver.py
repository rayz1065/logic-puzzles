from itertools import product
from logic_puzzles.solver import Solver


class BattleshipsSolver(Solver):
    def _compute_dirty(self, r, c):
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

    def _update_all_dirty(self, dirty):
        while len(dirty) > 0:
            r, c = dirty.pop()
            if self.state.grid[r][c] is None:
                valid_values = [x for x in (0, 1) if self.puzzle.can_set(r, c, x)]
                if len(valid_values) <= 1:
                    break
        else:
            # failed to find an empty dirty cell that doesn't require branching
            return set()

        if len(valid_values) == 0:
            return None

        value = valid_values[0]
        dirty.update(self._compute_dirty(r, c))
        self.puzzle.set_value(r, c, value)
        updated = self._update_all_dirty(dirty)

        if updated is None:
            self.puzzle.unset_value(r, c)
            return None

        updated.add((r, c))
        return updated

    def _solve_dirty(self, dirty):
        self.check_timeout()

        updated = self._update_all_dirty(dirty)

        if updated is None:
            return 0

        res = self._branching_solve()
        for r, c in updated:
            self.puzzle.unset_value(r, c)

        return res

    def _branching_solve(self):
        self.check_timeout()

        best_score, r, c = None, None, None
        for new_r, new_c in self.puzzle.grid_utils.iter_grid():
            if self.state.grid[new_r][new_c] is not None:
                continue

            score = self.puzzle.branching_score(new_r, new_c)
            if best_score is None or score > best_score:
                best_score, r, c = score, new_r, new_c

        if best_score is None:
            self.store_solution()
            return 1

        res = 0
        for value in self.branching_order((0, 1)):
            if not self.puzzle.can_set(r, c, value):
                continue

            dirty = self._compute_dirty(r, c)
            self.puzzle.set_value(r, c, value)
            res += self._solve_dirty(dirty)
            self.puzzle.unset_value(r, c)

        return res

    def _solve(self):
        dirty = set(
            (r, c)
            for r in range(self.puzzle.grid_utils.rows)
            for c in range(self.puzzle.grid_utils.cols)
            if self.state.grid[r][c] is None
        )

        return self._solve_dirty(dirty)
