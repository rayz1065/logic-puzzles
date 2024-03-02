from logic_puzzles.solver import Solver


class ThermometersSolver(Solver):
    def _compute_dirty(self, r, c):
        dirty = set()
        thermometer_idx, _ = self.puzzle.cell_thermometer[r][c]
        for new_r, new_c in self.puzzle.thermometers[thermometer_idx]:
            if self.state.grid[new_r][new_c] is None:
                dirty.add((new_r, new_c))

        for new_r in range(self.puzzle.grid_utils.rows):
            if self.state.grid[new_r][c] is None:
                dirty.add((new_r, c))

        for new_c in range(self.puzzle.grid_utils.cols):
            if self.state.grid[r][new_c] is None:
                dirty.add((r, new_c))

        return dirty

    def _update_all_dirty(self, dirty):
        while len(dirty) > 0:
            r, c = dirty.pop()
            if self.state.grid[r][c] is None:
                valid_values = self.puzzle.get_valid_values(r, c)
                if len(valid_values) <= 1:
                    break
        else:
            # failed to find an empty dirty cell that doesn't require branching
            return set()

        if len(valid_values) == 0:
            return None

        value = valid_values[0]
        self.puzzle.set_value(r, c, value)
        dirty.update(self._compute_dirty(r, c))
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

            score = self.puzzle.get_branching_score(new_r, new_c)
            if best_score is None or score > best_score:
                best_score, r, c = score, new_r, new_c

        if best_score is None:
            self.store_solution()
            return 1

        res = 0
        for value in self.branching_order(self.puzzle.get_valid_values(r, c)):
            self.puzzle.set_value(r, c, value)
            dirty = self._compute_dirty(r, c)
            res += self._solve_dirty(dirty)
            self.puzzle.unset_value(r, c)

        return res

    def _solve(self):
        dirty = set(self.puzzle.grid_utils.iter_grid())
        return self._solve_dirty(dirty)
