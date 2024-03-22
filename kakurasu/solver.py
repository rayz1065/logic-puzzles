from functools import cache
from logic_puzzles.solver import SimpleBranchingSolver


@cache
def check_sum_possible(available, target):
    if target < 0:
        return False
    if target == 0:
        return True

    for i, is_available in enumerate(available):
        if not is_available:
            continue

        # NOTE: we won't need to use the same value in any future recursive call
        available = tuple(
            j_available and j != i for j, j_available in enumerate(available)
        )
        if check_sum_possible(available, target - (i + 1)):
            return True

    return False


class KakurasuSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        r, c = location
        missing_r = self.puzzle.target_by_rows[r] - self.state.found_by_rows[r, 1]
        missing_c = self.puzzle.target_by_cols[c] - self.state.found_by_cols[c, 1]

        return -min(missing_r, missing_c)

    def _compute_dirty(self, location):
        r, c = location
        dirty = set()
        dirty.update((r, new_c) for new_c in range(self.puzzle.grid_utils.cols))
        dirty.update((new_r, c) for new_r in range(self.puzzle.grid_utils.rows))

        return set(x for x in dirty if not self.is_location_set(x))

    def find_impossible_sums(self):
        to_update = {}

        for r, c in self.puzzle.grid_utils.iter_grid():
            if self.is_location_set((r, c)):
                continue

            # suppose this value were 1, could we achieve exactly the target?
            self.puzzle.set_value((r, c), 1)

            row_constraint = self.puzzle.row_constraints[r]
            col_constraint = self.puzzle.col_constraints[c]

            constraints = [
                (
                    row_constraint.get_missing(self.state.found_by_rows[(r, 1)]),
                    tuple(x is None for x in self.state.grid[r]),
                ),
                (
                    col_constraint.get_missing(self.state.found_by_cols[(c, 1)]),
                    tuple(x[c] is None for x in self.state.grid),
                ),
            ]

            if any(
                not check_sum_possible(available, target)
                for target, available in constraints
            ):
                to_update[r, c] = 0

            self.puzzle.unset_value((r, c))

        return to_update

    def _branching_solve(self):
        to_update = self.find_impossible_sums()

        if self.debug:
            print(f"Found by impossible sums: {len(to_update)}")

        if to_update:
            return self._solve_updates_map(to_update)

        return super()._branching_solve()
