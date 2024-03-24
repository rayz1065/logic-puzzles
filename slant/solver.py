from itertools import combinations
from logic_puzzles.solver import SimpleBranchingSolver


def combinations_with_exclusions(iterable, r):
    items = set(iterable)
    for combination in combinations(items, r):
        yield combination, tuple(items.difference(combination))


class SlantSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        r, c = location
        if len(self.puzzle.intersections_by_cell[r, c]) == 0:
            return -99

        return max(
            self.puzzle.intersections_constraints[new_r, new_c].get_branching_score(
                self.puzzle.state.found_by_intersection[new_r, new_c, 1],
                self.puzzle.state.found_by_intersection[new_r, new_c, 0],
            )
            for new_r, new_c, _ in self.puzzle.intersections_by_cell[r, c]
        )

    def _compute_dirty(self, location):
        r, c = location
        # all of the adjacent cells in any direction
        return set(
            (new_r, new_c)
            for new_r, new_c in self.puzzle.grid_utils.all_directions_iter(r, c, 1)
            if not self.is_location_set((new_r, new_c))
        )

    def _test_combination(self, updates):
        updated = set()

        for r, c, slant in updates:
            if not self.puzzle.can_set((r, c), slant):
                break
            self.puzzle.set_value((r, c), slant)
            updated.add((r, c))

        for r, c in updated:
            self.puzzle.unset_value((r, c))

        return len(updated) == len(updates)

    def try_all_combinations(self):
        to_update = {}

        for r, row in enumerate(self.puzzle.intersections):
            for c, _ in enumerate(row):
                if self.puzzle.intersections[r][c] is None:
                    continue

                found = self.state.found_by_intersection[r, c, 1]
                missing = self.puzzle.intersections_constraints[r, c].get_missing(found)
                if missing == 0:
                    continue

                candidate_cells = [
                    (cell_r, cell_c, slant)
                    for cell_r, cell_c, new_r, new_c, slant in self.puzzle.adjacent_intersections(
                        r, c
                    )
                    if not self.is_location_set((cell_r, cell_c))
                ]

                frequencies = {
                    (cell_r, cell_c, slant): 0
                    for cell_r, cell_c, _ in candidate_cells
                    for slant in ("/", "\\")
                }
                valid_combinations = 0

                for combination, excluded in combinations_with_exclusions(
                    candidate_cells, missing
                ):
                    updates = combination + tuple(
                        [
                            (r, c, "/" if slant == "\\" else "\\")
                            for r, c, slant in excluded
                        ]
                    )
                    if not self._test_combination(updates):
                        continue

                    valid_combinations += 1
                    for cell_r, cell_c, slant in updates:
                        frequencies[cell_r, cell_c, slant] += 1

                for (cell_r, cell_c, slant), freq in frequencies.items():
                    if freq != valid_combinations:
                        continue

                    if to_update.get((cell_r, cell_c), slant) != slant:
                        # conflict
                        return None

                    to_update[cell_r, cell_c] = slant

        return to_update

    def _branching_solve(self):
        to_update = self.try_all_combinations()

        if to_update is None:
            return 0

        if self.debug:
            print(f"found by testing all combinations: {len(to_update)}")

        if to_update:
            return self._solve_updates_map(to_update)

        if not self.puzzle.check_no_cycles():
            if self.debug:
                print("cycle detected")
            return False

        return super()._branching_solve()
